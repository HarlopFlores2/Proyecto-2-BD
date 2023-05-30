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
            if cont == 1000:
                break

    with open(dirPath+'data.json', 'w') as f:
        json.dump(datos_nuevos, f, indent=4)


#filterJson()


class InvertedIndex:
    def __init__(self, indexPath, dataPath, block_size=1000):
        nltk.download('punkt')
        nltk.download('stopwords')
        self.index = defaultdict(list)
        self.dataPath = dataPath
        self.indexPath = indexPath
        self.doc_lengths = {}
        self.doc_frequency = defaultdict(int)
        self.term_frequency = defaultdict(lambda: defaultdict(int))
        self.stopwords = stopwords.words('english')
        self.stemmer = SnowballStemmer('english')
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
        for term in terms:
            self.add_term(term, doc_id)
            self.term_frequency[term][doc_id] += 1

    # tfdf_weight
    def tfdf_weight(self, term, doc_id):
        tf = self.term_frequency[term][doc_id]
        df = self.doc_frequency[term]
        idf = np.log(len(self.doc_lengths) / (1+df))
        return tf * idf
    
    def cosine_similarity(self, query_vector, doc_vector):
        dot_product = sum(query_vector[term] * doc_vector[term] for term in query_vector)
        query_norm = math.sqrt(sum(value ** 2 for value in query_vector.values()))
        document_norm = math.sqrt(sum(value ** 2 for value in doc_vector.values()))
        if (query_norm * document_norm) == 0:
            return 0
        return dot_product / (query_norm * document_norm)

    

    

        

invertedIndex = InvertedIndex(dirPath+'index.json', dirPath+'data.json')
invertedIndex.add_document('1', 'This is a test')
invertedIndex.add_document('2', 'This is another test')
print(invertedIndex.index)