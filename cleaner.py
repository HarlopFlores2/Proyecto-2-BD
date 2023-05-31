import os
import json

def split_filtered_json(input_file_path, output_directory, chunk_size):
    with open(input_file_path, 'r') as input_file:
        # Crea la carpeta destino si no existe
        os.makedirs(output_directory, exist_ok=True)
        
        chunk_number = 1
        json_data = []
        for line in input_file:
            new_dict = {}
            objeto = json.loads(line)
            new_dict['id'] = objeto['id']
            new_dict['abstract'] = objeto['abstract']
            json_data.append(new_dict)
            
            # Verifica si se alcanzo el tamaño establecido
            if len(json_data) == chunk_size:
                output_file_path = os.path.join(output_directory, f'chunk_{chunk_number}.json')
                with open(output_file_path, 'w') as output_file:
                    json.dump(json_data, output_file)
                chunk_number += 1
                json_data = []
        
        # Escribe los datos restantes en el ultimo chunk
        if json_data:
            output_file_path = os.path.join(output_directory, f'chunk_{chunk_number}.json')
            with open(output_file_path, 'w') as output_file:
                json.dump(json_data, output_file)


input_file_path = "./arxiv-metadata-oai-snapshot.json"
output_directory = "./clean"
chunk_size = 200000

# split_filtered_json(input_file_path, output_directory, chunk_size)
