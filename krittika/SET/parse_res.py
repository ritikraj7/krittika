import re
import json
import argparse

def parse_khwb_values(line):
    # Extract values from K, H, W for num_cores and new parameters
    match = re.search(r'\(([^()]*)\)', line)
    values = match.group(1).split(',')
    values_dict = {}
    for value in values:
        key, val = value.strip().split(':')
        values_dict[key.strip()] = int(val.strip())
    num_cores = values_dict['K'] * values_dict['H'] * values_dict['W']
    input_part = values_dict['K']
    filter_part = values_dict['H'] * values_dict['W']
    return num_cores, input_part, filter_part

def parse_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
    RA_tree = {}
    Layers = {}
    indentation_levels = []
    cut_counter = {'T': 0, 'S': 0}
    leaf_id = 0
    processing = False
    first_node = True
    stop_parsing = False
    for line in lines:
        if 'SA-BASE' in line:
            processing = True
            continue
        if processing and 'Struct:' in line:
            continue
        
        if processing and not stop_parsing:
            stripped_line = line.strip()
            if stripped_line == "":
                continue
            indent = len(line) - len(stripped_line)
            parts = stripped_line.split()
            first_word = parts[0]
            # Check if we need to stop processing after specific node
            # if first_word == "conv_2_0_res":
            #     stop_parsing = True
            if first_word in ['T', 'S']:
                if first_node:
                    node_name = 'Main'  # First node is always 'Main'
                    node_type = first_word + '_cut'
                    first_node = False
                else:
                    cut_counter[first_word] += 1
                    node_name = first_word + str(cut_counter[first_word])
                    node_type = first_word + '_cut'
            else:
                if not first_word.startswith('conv') or 'res' in first_word:
                    comp_type = 'activation'
                else:
                    comp_type = 'conv'
                num_cores, input_part, filter_part = parse_khwb_values(stripped_line)
                Layers[leaf_id] = {
                    "comp": comp_type,
                    "num_cores": num_cores,
                    "input_part": input_part,
                    "filter_part": filter_part
                }
                # Add leaf node under the appropriate parent based on indentation
                for level in reversed(indentation_levels):
                    if level[0] < indent:
                        RA_tree[level[1]]['children'].append({"Type": "Leaf", "ID": leaf_id})
                        break
                leaf_id += 1
                if stop_parsing:
                    break
                continue
            node = {"Type": node_type, "children": []}
            while indentation_levels and indentation_levels[-1][0] >= indent:
                indentation_levels.pop()
            if indentation_levels:
                RA_tree[indentation_levels[-1][1]]['children'].append({"Type": "Cut", "ID": node_name})
            indentation_levels.append((indent, node_name))
            RA_tree[node_name] = node
            if stop_parsing:
                break
    return {"RA_tree": RA_tree, "Layers": Layers}

def output_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
# Usage

def main():
    parser = argparse.ArgumentParser(description="Output JSON from parsed SET data.")
    parser.add_argument('-o', '--output_file',required=True, type=str, help="The output file path for the JSON data.")
    args = parser.parse_args()

    # input_filename = './results/SET_output.txt'  # Hard-coded input file
    # data = parse_file(input_filename)
    # output_json(data, args.output_file)

if __name__ == "__main__":
    main()