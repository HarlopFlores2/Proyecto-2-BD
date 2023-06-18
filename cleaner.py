import os
import json

def split_filtered_json(input_file_path, output_directory):
    with open(input_file_path, 'r') as input_file:
        # Crea la carpeta destino si no existe
        os.makedirs(output_directory, exist_ok=True)
        
        new_dict = {}
        for line in input_file:
            objeto = json.loads(line)
            new_dict[objeto["id"]] = objeto["abstract"]
            
        output_file_path = os.path.join(output_directory, 'data.json')
        with open(output_file_path, 'w') as output_file:
            json.dump(new_dict, output_file)


input_file_path = "./arxiv-metadata-oai-snapshot.json"
output_directory = "./data"

split_filtered_json(input_file_path, output_directory)
