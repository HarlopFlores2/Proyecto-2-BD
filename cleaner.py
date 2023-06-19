import os
import json


def filtered_json(input_file_path, output_directory):
    with open(input_file_path, 'r') as input_file:
        # Crea la carpeta destino si no existe
        os.makedirs(output_directory, exist_ok=True)
                
        json_data = []
        for line in input_file:
            new_dict = {}
            objeto = json.loads(line)
            new_dict['id'] = objeto['id']
            new_dict['abstract'] = objeto['abstract']
            json_data.append(new_dict)
        
        if json_data:
            output_file_path = os.path.join(output_directory, 'newdata.json')
            with open(output_file_path, 'w') as output_file:
                json.dump(json_data, output_file)


input_file_path = "./arxiv.json"
output_directory = "./data2"
chunk_size = 200000

filtered_json(input_file_path, output_directory)
