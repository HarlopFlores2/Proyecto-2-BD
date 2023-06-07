from InvertedIndex import *	
import sys
import pickle

class SPIMI:
    def __init__(self, block_size):
        self.block_size = block_size
        self.index = InvertedIndex("C:/PROYECTO-2-BD/data/index.json", "C:/PROYECTO-2-BD/data/data.json")
        self.blocks = []
        self.temp_dir = "temp_blocks"

    def add_document(self, doc_id, document):
        self.index.add_document(doc_id, document)

    def build_index(self, documents):
        os.makedirs(self.temp_dir, exist_ok=True)
        for doc_id, document in documents:
            self.add_document(doc_id, document)
            if sys.getsizeof(self.index.get_dict_index()) > self.block_size:
                self.flush_block()
        self.flush_block()
        return self.merge_blocks()
    
    def flush_block(self):
        sorted_terms = sorted(self.index.get_dict_index().keys())
        block_filepath = os.path.join(self.temp_dir, "block" + str(len(self.blocks)) + ".pkl")
        with open(block_filepath, "wb") as block_file:
            pickle.dump(sorted_terms, block_file)
            pickle.dump(self.index.get_dict_index(), block_file)
        self.blocks.append(block_filepath)
        self.index.get_dict_index().clear()


    def merge_blocks(self):
        merged_index = {}
        for block_filepath in self.blocks:
            with open(block_filepath, "rb") as block_file:
                terms = pickle.load(block_file)
                dict_index = pickle.load(block_file)
                for term in terms:
                    merged_index[term] = dict_index.get(term)
            os.remove(block_filepath)
        self.blocks = []
        return merged_index


# test
documents = []
with open(dirPath+'data.json', 'r') as f:
    data = json.load(f)
    for doc_id in data['data']:
        documents.append((doc_id, data['data'][doc_id]))

spimi = SPIMI(100000)

index = spimi.build_index(documents)
#print(index)

    

