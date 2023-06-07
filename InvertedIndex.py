import json
import os
import re
import nltk
import numpy as np
import math
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from collections import defaultdict

jsonPath = "C:/PROYECTO-2-BD/data/data_no_filter.json"
dirPath = "C:/PROYECTO-2-BD/data/"

def filterJson():
    datos_nuevos = {'data': {}}
    
    with open(jsonPath, 'r') as f:
        cont = 0
        for line in f:
            objeto = json.loads(line)
            cont += 1
            id = objeto['id']
            abstract = objeto['abstract']
            datos_nuevos['data'][id] = abstract
            if cont == 10000:
                break

    with open(dirPath+'data.json', 'w') as f:
        json.dump(datos_nuevos, f, indent = 4)


filterJson()

def init():
    invertedIndex = InvertedIndex(dirPath+'index.json', dirPath+'data.json')
    with open(dirPath+'data.json', 'r') as f:
        data = json.load(f)
        for doc_id in data['data']:
            invertedIndex.add_document(doc_id, data['data'][doc_id])
    with open(dirPath+'index.json', 'w') as f:
        json.dump(invertedIndex.index, f, indent = 4)
    return invertedIndex


class InvertedIndex:
    def __init__(self, indexPath, dataPath, block_size=1000):
        #nltk.download('punkt')
        #nltk.download('stopwords')
        self.index = defaultdict(list)
        self.dataPath = dataPath
        self.indexPath = indexPath
        self.doc_lengths = {}
        self.doc_norm = {}
        self.doc_frequency = defaultdict(int)
        self.term_frequency = defaultdict(lambda: defaultdict(int))
        self.stopwords = stopwords.words('english')
        self.stemmer = SnowballStemmer('english')

    def get_dict_index(self):
        return self.index
    # procesamiento de palabra
    def processWord(self, word):
        word = word.lower()
        if word in self.stopwords:
            return None
        word = self.stemmer.stem(word)
        return word
    # procesamiento de texto
    def processText(self, text):
        text = re.sub(r'[^\w\s]', '', text)
        tokens = nltk.word_tokenize(text)
        tokens = [self.processWord(word) for word in tokens]
        tokens = [word for word in tokens if word is not None]
        return tokens
    # añadir termino 
    def add_term(self, term, doc_id):
        if doc_id not in self.index[term]:
            self.index[term].append(doc_id)
            self.doc_frequency[term] += 1
    
    # añadir documento a la coleccion
    def add_document(self, doc_id, document):
        terms = self.processText(document)
        self.doc_lengths[doc_id] = len(terms)
        doc_norm_temp = 0
        for term in terms:
            self.term_frequency[term][doc_id] += 1
            self.add_term(term, doc_id)
            doc_norm_temp += self.tfidf_weight(term, doc_id) ** 2
        
        self.doc_norm[doc_id] = math.sqrt(doc_norm_temp)
    # tfdf_weight
    def tfidf_weight(self, term, doc_id):
        tf = self.term_frequency[term][doc_id]
        df = self.doc_frequency[term]
        idf = np.log(len(self.doc_lengths) / (1+df))
        return tf * idf
    
    def cosine_similarity(self, query_vector, doc_vector, doc_id):
        dot_product = sum(query_vector[i] * doc_vector[i] for i in range(len(query_vector)))
        query_norm = math.sqrt(sum(value ** 2 for value in query_vector))
        document_norm = self.doc_norm[doc_id]
        if (query_norm * document_norm) == 0:
            return 0
        return dot_product / (query_norm * document_norm)
    
    def process_query(self, query, k):
        query = self.processText(query)
        query_vector = []
        for term in query:
            tf = query.count(term)
            df = self.doc_frequency[term]
            idf = np.log(len(self.doc_lengths) / (1+df))
            query_vector.append(tf*idf)

        scores = defaultdict(float)

        for doc_id in self.doc_lengths:
            doc_vector = []
            for term in query:
                doc_vector.append(self.tfidf_weight(term, doc_id))
            scores[doc_id] = self.cosine_similarity(query_vector, doc_vector, doc_id)

        return sorted(scores.items(), key=lambda item: item[1], reverse=True)[:k]
    


'''
invertedIndex = InvertedIndex(dirPath+'index.json', dirPath+'data.json')
invertedIndex.add_document('1', 'This is a test')
invertedIndex.add_document('2', 'This is another test')
process_query = invertedIndex.process_query('another test', 2)
print(process_query)
'''
