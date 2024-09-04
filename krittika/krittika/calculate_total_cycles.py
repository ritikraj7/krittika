import csv
from itertools import islice
layer_cycles_dict = {}

import json 
 


def process_cut(cut_id, ra_tree, layers, reader):
    cut_cycles = 0
    if cut_id in ra_tree:
        node = ra_tree[cut_id]
        if 'children' in node:
            for child in node['children']:
                child_cycles = 0
                if child['Type'] == 'Cut':
                    node_id = child['ID']
                    child_cycles = process_cut(node_id, ra_tree, layers, reader)

                elif child['Type'] == 'Leaf':
                    layer_id = child['ID']
                    child_cycles = process_layer(layer_id, layers, reader)

                else:
                    print("Unknown node type:", child['Type'])
                
                if node['Type'] == 'T_cut':
                    cut_cycles += child_cycles
                    
                   # print(" enter process cur t cut ")
                elif node['Type'] == 'S_cut':
                    cut_cycles = max(cut_cycles, child_cycles)
                else:
                    print("Unknown node type:", node['Type'])
    else:
        print("Cut not found:", cut_id) 
    return cut_cycles

def process_layer(layer_id, layers, reader):  
    layer_cycles = 0  
    #print("sdnay ")        
    #next(reader)  # Skip the header row
    #reader = islice(reader, 1, None)
   
 
    if str(layer_id) in layers:
        # for row in reader:
        #     print(row[1])
        #print(layer_id)
        # print("Processing Layer:", layers[str(layer_id)])
        #get cycles for layer_id
 
        
       
        for row in reader:
            print(row)
            print(layer_id)
            if int(layer_id) == int(row[0]):
                layer_cycles =  float(row[1])
                #print(f"layercycle:{layer_cycles}")
                layer_cycles_dict[layer_id] = layer_cycles
                #print(layer_cycles_dict)
                break
        
    else:
        
        print("Unknown layer:", layer_id)

    return layer_cycles

def traverse_tree(tree, ra_tree, layers, reader):
    if 'Main' in tree['RA_tree']:
        main_node = tree['RA_tree']['Main']
        total_cycles = 0
        if 'children' in main_node:
            for child in main_node['children']:
                if child['Type'] == 'Cut':
                    node_id = child['ID']
                    child_cycles = process_cut(node_id, ra_tree, layers, reader)
                    print(child_cycles)
                elif child['Type'] == 'Leaf':
                    layer_id = child['ID']
                    child_cycles = process_layer(layer_id, layers, reader)
                else:
                    print("Unknown node type:", child['Type'])
                
                if main_node['Type'] == 'T_cut':
                    total_cycles += child_cycles
                   # print("enter main S cut ")
                elif main_node['Type'] == 'S_cut':
                    total_cycles = max(total_cycles, child_cycles)
                  
                else:
                    print("Unknown node type:", main_node['Type'])  

        print("Total cycles taken:", total_cycles)  
    
    else:
        print("Main node not found.")

# Test the function with the provided data


with open(r'/nethome/rsenthilkumar9/HML_project/krittika_c/krittika/SET_output_50_layers_except_last_2 1.json') as f:     
    # Load the JSON data into a dictionary   
    SET_optimal = json.load(f)


# SET_optimal =  {
#     "RA_tree":
#         {
#     "Main": {
#             "Type": "T_cut",
#             "children": [
#             {"Type": "Cut", "ID": "T1"}
#         ]
#     },
#     "T1": {
#         "Type": "T_cut",
#         "children": [
#             {"Type": "Layer", "ID": 0},
#             {"Type": "Layer", "ID": 1},
#             {"Type": "Layer", "ID": 2},
#             {"Type": "Cut", "ID": "S1"},
#             {"Type": "Layer", "ID": 6}
#         ]
#     },
#     "S1": {
#         "Type": "S_cut",
#         "children": [
#             {"Type": "Cut", "ID": "T2"},
#             {"Type": "Layer", "ID": 5}
#         ]
#     },
#     "T2": {
#         "Type": "T_cut",
#         "children": [
#             {"Type": "Layer", "ID": 3},
#             {"Type": "Layer", "ID": 4}
#         ]
#     }
#         },
#     "Layers":{
    
#     "0":{
        
#         "comp":"conv",
#         "num_cores": 16,
#         "input_part": 4, 
#         "filter_part": 4  
#         }
#     ,
#     "1":{
        
#         "comp":"activation",
#         "num_cores": 16,
#         "input_part": 4, 
#         "filter_part": 4 
#         }
#     ,
#     "2":{
        
#         "comp":"conv",
#         "num_cores": 16,
#         "input_part": 4, 
#         "filter_part": 4
    
#         }
#     ,
#     "3":{
        
#         "comp":"conv",
#         "num_cores": 16,
#         "input_part": 4, 
#         "filter_part": 4                
#         },
    
#     "4":{
        
#         "comp":"conv",
#         "num_cores": 16,
#         "input_part": 4, 
#         "filter_part": 4
#         },
        
#     "5":{
        
#         "comp":"conv",
#         "num_cores": 16,
#         "input_part": 4, 
#         "filter_part": 4  
    
#         },
#     "6":{
#         "comp": "activation",
#         "num_cores": 16,
#         "input_part": 4, 
#         "filter_part": 4  
#     }
#     }          
# }
  

with open('/nethome/rsenthilkumar9/HML_project/krittika_c/traces/COMPUTE_REPORT.csv',mode='r', newline='') as csvfile:
    reader = csv.reader(csvfile)
    #print(reader)
    reader = islice(reader, 1, None)
    traverse_tree(SET_optimal, SET_optimal['RA_tree'], SET_optimal['Layers'], reader)