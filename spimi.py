from InvertedIndex import *	
import sys
import pickle

def init(dataPath):
    documents = []
    with open(dataPath, 'r') as f:
        data = json.load(f)
        for doc_id in data['data']:
            documents.append((doc_id, data['data'][doc_id]))
    return documents

class SPIMI:
    def __init__(self, block_size):
        self.block_size = block_size
        self.block_dict_temp = {}
        self.doc_lengths = {}
        self.doc_norm = {}
        self.term_frequency = defaultdict(lambda: defaultdict(int))
        self.blocks = []
        self.temp_dir = "temp_blocks"
        self.index_path = os.path.join("index", "index.pkl")
        self.data_path = os.path.join("data", "data.json")
        self.stopwords = stopwords.words('english') + stopwords.words('spanish')
        self.stemmer = SnowballStemmer('english')

    def processWord(self, word):
        word = word.lower()
        if word in self.stopwords:
            return None
        word = self.stemmer.stem(word)
        return word

    def processText(self, text):
        text = re.sub(r'\d+', '', text)
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'[^a-zA-Z0-9]', ' ', text)
        text = re.sub(r'\b\w{1,2}\b', '', text)
        tokens = nltk.word_tokenize(text)
        tokens = [self.processWord(word) for word in tokens]
        tokens = [word for word in tokens if word is not None]
        return tokens
    
    def calculate_doc_norm(self):
        with open(self.index_path, "rb") as index_file:
            index = pickle.load(index_file)
        
        with open(self.data_path, "rb") as data_file:
            data = json.load(data_file)

        for doc_id in self.doc_lengths:
            doc_norm = 0
            terms = self.processText(data["data"][doc_id])
            for term in terms:
                tf = self.term_frequency[term][doc_id]
                idf = math.log(len(self.doc_lengths) / len(index[term]))
                doc_norm += (tf * idf) ** 2

            self.doc_norm[doc_id] = math.sqrt(doc_norm)
        
    def add_document(self, doc_id, document):
        terms = self.processText(document)
        self.doc_lengths[doc_id] = len(terms)
        self.doc_norm[doc_id] = 0
        for term in terms:
            self.term_frequency[term][doc_id] += 1
            if term not in self.block_dict_temp:
                self.block_dict_temp[term] = [doc_id]
            else:
                self.block_dict_temp[term].append(doc_id)

    def build_index(self, documents):
        os.makedirs(self.temp_dir, exist_ok=True)
        for doc_id, document in documents:
            self.add_document(doc_id, document)
            if sys.getsizeof(self.block_dict_temp) > self.block_size:
                self.flush_block()
        self.flush_block()
        self.merge_blocks()
        self.calculate_doc_norm()
        
    
    def flush_block(self):
        sorted_terms = sorted(self.block_dict_temp.keys())
        block_filepath = os.path.join(self.temp_dir, "block" + str(len(self.blocks))+ ".pkl")
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
                    merged_block[terms1[i]] = list(set(term_dict1[terms1[i]] + term_dict2[terms2[j]]))
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
        os.remove(block2) 
        return merged_block


    def merge_blocks(self):
        merged_blocks = {}
        for i in range(0, len(self.blocks)):
            if i == 0:
                with open(self.blocks[i], "rb") as block_file:
                    terms1 = pickle.load(block_file)
                    term_dict1 = pickle.load(block_file)
                    merged_blocks = term_dict1
                
                os.remove(self.blocks[i])
            else:
                merged_blocks = self.merge_two_blocks(terms1, term_dict1, self.blocks[i])
                terms1 = list(merged_blocks.keys())
                term_dict1 = merged_blocks
            
        
        with open(self.index_path, "wb") as index_file:
            pickle.dump(merged_blocks, index_file)

        return merged_blocks
        
    def cosine_similarity(self, query_vector, doc_vector, doc_id):
        dot_product = sum(query_vector[i] * doc_vector[i] for i in range(len(query_vector)))
        query_norm = math.sqrt(sum(value ** 2 for value in query_vector))
        document_norm = self.doc_norm[doc_id]

        if (query_norm * document_norm) == 0:
            return 0
        return dot_product / (query_norm * document_norm)
    
    def process_query(self, query, k):
        index = open(self.index_path, "rb")
        query = self.processText(query)
        query_vector = []
        for term in query:
            tf = query.count(term)
            #comprobar si el termino esta en el indice
            if term not in index:
                df = 0
            else:
                df = len(index[term])

            idf = math.log(len(self.doc_lengths)/(1+df), 4)
            query_vector.append(tf*idf)

        scores = defaultdict(float)

        for doc_id in self.doc_lengths:
            doc_vector = []
            for term in query:
                tf = self.term_frequency[term][doc_id]
                if term not in index:
                    df = 0
                else:
                    df = len(index[term])
                idf = math.log(len(self.doc_lengths)/(df+1), 4)
                doc_vector.append(tf*idf)

            scores[doc_id] = self.cosine_similarity(query_vector, doc_vector, doc_id)

        return sorted(scores.items(), key=lambda item: item[1], reverse=True)[:k]



    

