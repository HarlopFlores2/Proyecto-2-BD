import functools
import glob
import heapq
import itertools
import json
import math
import os
import pickle
from collections import Counter, defaultdict

import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

import util

stemmer = SnowballStemmer("english")
stop_words = set(
    itertools.chain(stopwords.words("english"), stopwords.words("spanish"))
)


@functools.lru_cache(1_000_000)
def stem(w):
    return stemmer.stem(w)


def word_valid(word):
    return any((c.isalnum() for c in word))


def tokens_for_text(text, stop_words=set()):
    return (
        stem(w)
        for w in (w.casefold() for w in nltk.word_tokenize(text) if word_valid(w))
        if w not in stop_words
    )


def create_offsets_for_index(offsets_filename, index_filename):
    token_offsets = dict()
    with open(index_filename, "rb") as index_fp:
        while True:
            offset = index_fp.tell()
            try:
                (token, _) = pickle.load(index_fp)
            except EOFError:
                break

            token_offsets[token] = offset

    with open(offsets_filename, "wb") as offsets_fp:
        pickle.dump(token_offsets, offsets_fp)
    return token_offsets


def idfs_for_index(total_documents, index_filename):
    idf_s = dict()

    with open(index_filename, "rb") as index_fp:
        while True:
            try:
                (token, tf_s) = pickle.load(index_fp)
            except EOFError:
                break

            assert total_documents >= len(tf_s)
            idf_s[token] = math.log((total_documents + 1) / (len(tf_s) + 1))

    return idf_s


def norms_for_index(idfs, index_filename):
    with open(index_filename, "rb") as index_fp:
        norms = defaultdict(int)
        while True:
            try:
                (token, tf_s) = pickle.load(index_fp)
            except EOFError:
                break

            for doc_id, n_occurrences in tf_s.items():
                norms[doc_id] += math.log(1 + n_occurrences) * idfs[token]

    for doc_id, total in norms.items():
        norms[doc_id] = math.sqrt(total)

    return norms


def merge_blocks_in_dir(result_filename, directory):
    blocks_filenames = glob.glob(os.path.join(directory, "*.blk"))
    merge_blocks(result_filename, blocks_filenames)


def merge_blocks(result_filename, blocks_filenames):
    blocks_fps = [open(bf, "rb") for bf in blocks_filenames]

    blocks = []
    for i, bfp in enumerate(blocks_fps):
        try:
            e = pickle.load(bfp)
            # This is necessary for the heap to work
            blocks.append((e[0], i, e[1]))
        except EOFError:
            blocks_fps[i] = None
    heapq.heapify(blocks)

    def advance_token_entries_in_order():
        if len(blocks) == 0:
            return

        (token, index, tfs) = heapq.heappop(blocks)

        try:
            e = pickle.load(blocks_fps[index])
            heapq.heappush(blocks, (e[0], index, e[1]))
        except EOFError:
            pass

        return (token, tfs)

    it = itertools.takewhile(
        lambda e: e is not None,
        (advance_token_entries_in_order() for _ in itertools.count()),
    )

    def merge_tfs(tfs_1: dict, tfs_2: dict):
        """Add the entries in tfs_2 to tfs_1."""
        for doc_id, count in tfs_2.items():
            tfs_1[doc_id] = tfs_1.get(doc_id, 0) + count

    # We assume there is at least one entry
    first_token, first_tfs = next(it)
    with open(result_filename, "wb") as fp:
        for token, tfs in it:
            if token == first_token:
                merge_tfs(first_tfs, tfs)
            else:
                pickle.dump((first_token, first_tfs), fp)
                first_token, first_tfs = token, tfs

        pickle.dump((first_token, first_tfs), fp)


def dot_product(v1, v2):
    if len(v1) != len(v2):
        raise RuntimeError("Vectors don't have the same length.")
    return sum(n1 * n2 for n1, n2 in zip(v1, v2))


def build_index(filename, stop_words):
    # Getting the complete size of the dictionary is expensive, so we
    # estimate it by the total count of entries for each token
    n_tuples = 0
    max_bytes_per_block = 500_000_000
    bytes_per_tuple = (
        55  # This is an approximation made by running with some example data
    )
    max_tuples_per_block = max_bytes_per_block // bytes_per_tuple
    n_blocks = 0

    term_frequencies = defaultdict(lambda: defaultdict(int))

    os.makedirs("blocks", exist_ok=True)

    def gen_filename_for_block_file(i):
        return os.path.join("blocks", f"b{i}.blk")

    def write_term_frequencies(term_frequencies, filename):
        with open(filename, "wb") as fp:
            block = sorted(
                (
                    (token, dict(docs_dict))
                    for token, docs_dict in term_frequencies.items()
                ),
                key=lambda t: t[0],
            )
            for e in block:
                pickle.dump(e, fp)

    with open(filename, "r") as fp:
        for i, line in enumerate(fp):
            j = json.loads(line)
            abstract = j["abstract"]
            for t in tokens_for_text(abstract, stop_words):
                if t not in term_frequencies or i not in term_frequencies[t]:
                    if n_tuples == max_tuples_per_block:
                        block_filename = gen_filename_for_block_file(n_blocks)
                        n_blocks += 1

                        write_term_frequencies(term_frequencies, block_filename)

                        term_frequencies.clear()
                        n_tuples = 0

                    n_tuples += 1

                term_frequencies[t][i] += 1

    if len(term_frequencies) != 0:
        write_term_frequencies(term_frequencies, gen_filename_for_block_file(n_blocks))

    return term_frequencies


class Query:
    __slots__ = "index_file", "offsets", "idfs", "norms"

    def __init__(self, index_file, offsets, idfs, norms):
        self.index_file = index_file
        self.offsets = offsets
        self.idfs = idfs
        self.norms = norms

    def query(self, query, top_k):
        query_count = Counter(tokens_for_text(query, stop_words))
        query_count = list(query_count.items())

        query_vector = []
        documents_vectors = defaultdict(dict)

        for (i, (token, count)) in enumerate(query_count):
            if token in self.offsets:
                [_, token_tfs] = util.unpickle_file_at_offset(
                    self.index_file, self.offsets[token]
                )
                for doc_id, tf in token_tfs.items():
                    documents_vectors[doc_id][i] = math.log(tf + 1) * self.idfs[token]

                query_vector.append(count)

        def default_dict_to_vector(dd, size):
            ret = []
            for i in range(size):
                ret.append(dd.get(i, 0))
            return ret

        documents_scores = [
            (
                doc_id,
                dot_product(
                    default_dict_to_vector(doc_vector, len(query_vector)), query_vector
                )
                / self.norms[doc_id],
            )
            for doc_id, doc_vector in documents_vectors.items()
        ]

        return sorted(documents_scores, key=lambda e: e[1], reverse=True)[:top_k]
