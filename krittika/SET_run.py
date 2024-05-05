import subprocess
import os
import argparse
from SET.parse_res import parse_file,output_json

def build_and_run_setframework(config_file, output_file):
    # Path to the SET folder of the framework
    SET_framework = "../SET_artifact/SET_framework"

    # Navigate to the main folder
    # os.chdir(SET_framework)

    # Run the make command to build the project
    print("Building the SET framework...")
    make_command = ["make"]
    try:
        subprocess.check_call(make_command,cwd=SET_framework)
        print("Build completed successfully.")
    except subprocess.CalledProcessError as e:
        print("Failed to build the SET framework: ", e)
        return

    # Command to run the framework
    print(f"./build/stschedule {config_file}")
    run_command = f"./build/stschedule ../../krittika/{config_file}"
    # os.chdir("../../krittika/SET")
    os.makedirs(os.path.dirname(f"SET/{output_file}"), exist_ok=True)

    # Open the output file
    with open(f"SET/{output_file}", 'w') as outfile:
        print(f"Running the SET framework and saving output to {output_file}...")
        try:
            subprocess.check_call(run_command.split(), stdout=outfile, cwd=SET_framework)
            print("Framework run successfully.")
        except subprocess.CalledProcessError as e:
            print("Failed to run the SET framework: ", e)
            return

def main():
    parser = argparse.ArgumentParser(description='Build and run the SET framework with provided configuration.')
    parser.add_argument('-c', '--config', required=True, type=str, help='Path to the configuration file for the SET framework')
    parser.add_argument('-j', '--SET_output', required=True, type=str, help='Path to save the output results file')
    args = parser.parse_args()
    output_file = "intermediate_results/SET_output.txt"
    if not os.path.exists(args.config): print("Warning: Config file does not exist. Proceeding with default settings.")
    build_and_run_setframework(args.config, output_file)
    input_filename = './SET/intermediate_results/SET_output.txt'  # Hard-coded input file
    data = parse_file(input_filename)
    output_json(data, args.SET_output)

if __name__ == "__main__":
    main()