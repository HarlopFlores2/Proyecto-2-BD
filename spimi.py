import functools
import glob
import heapq
import itertools
import json
import math
import os
import pickle
import re
import sys
from collections import defaultdict

import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

import util

stemmer = SnowballStemmer("english")


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


class SPIMI:
    def __init__(self, block_size):
        self.block_size = block_size
        self.block_dict_temp = {}
        self.blocks = []
        self.temp_dir = "temp_blocks"
        self.index_path = os.path.join("index")
        self.data_path = os.path.join("data")
        self.data = json.load(open(os.path.join(self.data_path, "data.json"), "rb"))

        self.stopwords = set(itertools.chain(stopwords.words("english"), stopwords.words("spanish")))

    def process_query(self, query, k):
        index = open(self.index_path + "/index.pkl", "rb")
        index = pickle.load(index)
        query = self.processText(query)
        query_vector = []
        for term in query:
            tf = query.count(term)
            # comprobar si el termino esta en el indice
            if term not in index:
                df = 0
            else:
                df = len(index[term])

            idf = math.log(len(self.data.keys()) / (1 + df), 4)
            query_vector.append(tf * idf)

        scores = defaultdict(float)

        docs = set()
        for term in query:
            for doc_id in index[term]:
                docs.add(doc_id)

        for doc_id in docs:
            doc_vector = []
            for term in query:
                tf = self.data[doc_id].count(term)
                df = len(index[term])
                idf = math.log(len(self.data.keys()) / (1 + df), 4)
                doc_vector.append(tf * idf)
            scores[doc_id] = self.cosine_similarity(query_vector, doc_vector)

        return sorted(scores.items(), key=lambda item: item[1], reverse=True)[:k]
