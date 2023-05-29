import json
import os
import re
import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

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
    def __init__(self, indexPath, dataPath):
        nltk.download('punkt')
        nltk.download('stopwords')
        self.dataPath = dataPath
        self.indexPath = indexPath
        self.stopwords = stopwords.words('english')
        self.stemmer = SnowballStemmer('english')
    
    def processWord(self, word):
        word = word.lower()
        if word in self.stopwords:
            return None
        word = self.stemmer.stem(word)
        return word
    
    def processText(self, text):
        text = re.sub(r'[^\w\s]', '', text)
        tokens = nltk.word_tokenize(text)
        tokens = [self.processWord(word) for word in tokens]
        tokens = [word for word in tokens if word is not None]
        return tokens
    
    def building(self, collection_text):
        inverted_index = {}
        with open(collection_text, 'r') as f:
            collection = json.load(f)
            for id, abstract in collection['data'].items():
                tokens = self.processText(abstract)
                for token in tokens:
                    if token not in inverted_index:
                        inverted_index[token] = set()
                    inverted_index[token].add(id)
        return inverted_index
        

#invertedIndex = InvertedIndex(dirPath+'index.json', dirPath+'data.json')
#index = invertedIndex.building(dirPath+'data.json')
print("hola")