import functools
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


stemmer = SnowballStemmer("english")


@functools.lru_cache(1_000_000)
def stem(w):
    return stemmer.stem(w)


def tokens_for_text(text, stop_words=set()):
    return (
        stem(w)
        for w in (w.casefold() for w in nltk.word_tokenize(text))
        if w not in stop_words
    )


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

    def add_document(self, doc_id, document):
        terms = self.processText(document)
        for term in terms:
            if term not in self.block_dict_temp:
                self.block_dict_temp[term] = [doc_id]
            else:
                self.block_dict_temp[term].append(doc_id)

    def build_index(self):
        os.makedirs(self.temp_dir, exist_ok=True)

        with open(os.path.join(self.data_path, "data.json"), "rb") as data_file:
            documents = json.load(data_file)

        for doc_id in documents.keys():
            self.add_document(doc_id, documents[doc_id])
            if sys.getsizeof(self.block_dict_temp) > self.block_size:
                self.flush_block()
        self.flush_block()
        self.merge_blocks()

    def flush_block(self):
        sorted_terms = sorted(self.block_dict_temp.keys())
        block_filepath = os.path.join(
            self.temp_dir, "block" + str(len(self.blocks)) + ".pkl"
        )
        with open(block_filepath, "wb") as block_file:
            pickle.dump(sorted_terms, block_file)
            pickle.dump(self.block_dict_temp, block_file)
        self.blocks.append(block_filepath)
        self.block_dict_temp.clear()

    def merge_two_blocks(self, terms1, term_dict1, block2):
        merged_block = {}
        with open(block2, "rb") as block_file2:
            terms2 = pickle.load(block_file2)
            term_dict2 = pickle.load(block_file2)
            i = 0
            j = 0
            while i < len(terms1) and j < len(terms2):
                if terms1[i] == terms2[j]:
                    merged_block[terms1[i]] = list(
                        set(term_dict1[terms1[i]] + term_dict2[terms2[j]])
                    )
                    i += 1
                    j += 1
                elif terms1[i] < terms2[j]:
                    merged_block[terms1[i]] = term_dict1[terms1[i]]
                    i += 1
                else:
                    merged_block[terms2[j]] = term_dict2[terms2[j]]
                    j += 1
            while i < len(terms1):
                merged_block[terms1[i]] = term_dict1[terms1[i]]
                i += 1
            while j < len(terms2):
                merged_block[terms2[j]] = term_dict2[terms2[j]]
                j += 1
        # os.remove(block2)
        return merged_block

    def merge_blocks(self):
        merged_blocks = {}
        for i in range(0, len(self.blocks)):
            if i == 0:
                with open(self.blocks[i], "rb") as block_file:
                    terms1 = pickle.load(block_file)
                    term_dict1 = pickle.load(block_file)
                    merged_blocks = term_dict1

                # os.remove(self.blocks[i])
            else:
                merged_blocks = self.merge_two_blocks(
                    terms1, term_dict1, self.blocks[i]
                )
                terms1 = list(merged_blocks.keys())
                term_dict1 = merged_blocks

        os.makedirs(self.index_path, exist_ok=True)

        with open(self.index_path + "/index.pkl", "wb") as index_file:
            pickle.dump(merged_blocks, index_file)

        return merged_blocks

    def cosine_similarity(self, query_vector, doc_vector):
        dot_product = sum(
            query_vector[i] * doc_vector[i] for i in range(len(query_vector))
        )
        query_norm = math.sqrt(sum(value**2 for value in query_vector))
        document_norm = math.sqrt(sum(value**2 for value in doc_vector))

        if (query_norm * document_norm) == 0:
            return 0
        return dot_product / (query_norm * document_norm)

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
