This repo is the baseline of our SET paper in ISCA 2023.

This repo is the *original open source of the Tangram framework* with the following modifications:

# Modifications

1. We fixed some minor bugs on the original Tangram framework.

2. We added an output file option (`-o xxx.json`).

3. We added a simple script (`./nn_dataflow/tools/pyrun_tangram.py`) to run the baseline experiments in parallel.
The parameter of the experiments are in `./nn_dataflow/tools/tangram.sh`

4. We added a simple script (`./nn_dataflow/tools/data.py`) to gather all results into a `.csv` file.

This git repo is on branch `baseline`, and there are two commits on this branch that corresponds to 1.2. and 3.4., respectively.

# Usage

The original usage, including install, usage and code structure, is supplemented in the original README.rst.

We have added one option `-o xxx.json`, which means putting the output json into the file `xxx.json`.

To run the baseline in SET paper, just run `python ./nn_dataflow/tools/pyrun_tangram.py`,
or run the shell script in the command line (e.g. `tangram.sh --batch 1 --nodes 4 4 resnet50 -o results/b1_4x4_res.json`).

# Results

The example results and csv file are supplemented in `./nn_dataflow/tools/results_example`
