def process_cut(cut_id, ra_tree, layers):
    if cut_id in ra_tree:
        node = ra_tree[cut_id]
        if 'children' in node:
            for child in node['children']:
                if child['Type'] == 'Cut':
                    node_id = child['ID']
                    process_cut(node_id, ra_tree, layers)
 
                elif child['Type'] == 'Layer':
                    layer_id = child['ID']
                    process_layer(layer_id, layers)
 
                else:
                    print("Unknown node type:", child['Type'])
 
def process_layer(layer_id, layers):            
        if layer_id in layers:
            print("Processing Layer:", layers[layer_id])
        else:
            print("Unknown layer:", layer_id)
 
def traverse_tree(tree, ra_tree, layers):
    if 'Main' in tree['RA_tree']:
        main_node = tree['RA_tree']['Main']
        if 'children' in main_node:
            for child in main_node['children']:
                if child['Type'] == 'Cut':
                    node_id = child['ID']
                    process_cut(node_id, ra_tree, layers)
                elif child['Type'] == 'Layer':
                    layer_id = child['ID']
                    process_layer(layer_id, layers)
SET_optimal =  {
    "RA_tree":
        {
    "Main": {
            "Type": "T_cut",
            "children": [
            {"Type": "Cut", "ID": "T1"}
        ]
    },
    "T1": {
        "Type": "T_cut",
        "children": [
            {"Type": "Layer", "ID": 0},
            {"Type": "Layer", "ID": 1},
            {"Type": "Layer", "ID": 2},
            {"Type": "Cut", "ID": "S1"},
            {"Type": "Layer", "ID": 6}
        ]
    },
    "S1": {
        "Type": "S_cut",
        "children": [
            {"Type": "Cut", "ID": "T2"},
            {"Type": "Layer", "ID": 5}
        ]
    },
    "T2": {
        "Type": "T_cut",
        "children": [
            {"Type": "Layer", "ID": 3},
            {"Type": "Layer", "ID": 4}
        ]
    }
        },
    "Layers":{
    0: {
        
        "comp":"conv",
        "num_cores": 4
    },
    1:{
        
        "comp":"activation",
        "num_cores": 4
        }
    ,
    2:{
        
        "comp":"conv",
        "num_cores": 4
        }
    ,
    3:{
        
        "comp":"conv",
        "num_cores": 4
        }
    ,
    4:{
        
        "comp":"conv",
        "num_cores": 2
        }
    ,
    5:{
        
        "comp":"conv",
        "num_cores": 2
        }
    ,
    6:{
        
        "comp":"activation",
        "num_cores": 4
        }
    }          
}               

traverse_tree(SET_optimal, SET_optimal['RA_tree'], SET_optimal['Layers'])