import math

from scalesim.topology_utils import topologies
from krittika.config.krittika_config import KrittikaConfig
from krittika.static_utilities import StaticUtilities
import json

class PartitionManager:
    def __init__(self):
        self.partition_table_cols = ['LayerID', 'InputParts', 'FilterParts', 'ComputeUnit', 'Dataflow']
        self.partition_table = []
        self.config = KrittikaConfig()
        self.workload = topologies()
        self.SET_json_file = ''

        # Flags
        self.params_valid = False
        self.partition_table_valid = False

    #
    def set_params(self,
                   config_obj=KrittikaConfig(),
                   workload_obj=topologies(),
                   SET_json_file=''):
        self.config = config_obj
        self.workload = workload_obj

        self.params_valid = True
        self.SET_json_file = SET_json_file

    #
    def create_partition_table(self):
        partition_mode = self.config.get_partition_mode()

        if partition_mode == 'IFMAP':
            self.create_opt_ifmap_part_table()
        elif partition_mode == 'FILTER':
            self.create_opt_filter_part_table()
        elif partition_mode == 'CONST_DF':
            self.create_opt_const_df_part_table()
        elif partition_mode == 'AUTO':
            self.create_opt_auto_part_table()
        elif partition_mode == 'SET_RA_TREE':
            self.create_opt_SET_RA_tree_part_table()

        self.partition_table_valid = True

    #
    def create_opt_auto_part_table(self):
        # print("DEBUG: Entered AUTO part mode")
        num_cores = self.config.get_num_cores()
        num_layers = self.workload.get_num_layers()
        partitions_list = StaticUtilities.get_factors_as_pairs(num_cores)
        dataflow_list = ['os', 'is', 'ws']
        layer_params = self.workload.get_layer_params()
        for lid in range(num_layers):
            layer_params = self.workload.get_layer_params(lid)
            if (layer_params[0] in ['conv', 'gemm']):
                opt_unit, opt_dataflow, input_parts, filter_parts \
                    = self.search_layer_opt_config( layer_id=lid,
                                                part_list=partitions_list,
                                                matmul_dataflow_list=dataflow_list,
                                                vec_dataflow_list=dataflow_list
                                                )

                entry = [lid, input_parts, filter_parts, opt_unit, opt_dataflow]
                self.partition_table += [entry]

    #
    #

    def create_opt_const_df_part_table(self):
        # print("DEBUG: Entered CONST_DF part mode")
        num_cores = self.config.get_num_cores()
        num_layers = self.workload.get_num_layers()
        partitions_list = StaticUtilities.get_factors_as_pairs(num_cores)
        matmul_dataflow_list = [self.config.get_matmul_dataflow()]
        vector_dataflow_list = [self.config.get_vector_dataflow()]

        for lid in range(num_layers):
            layer_params = self.workload.get_layer_params(lid)
            if (layer_params[0] in ['conv', 'gemm']):
                opt_unit, opt_dataflow, input_parts, filter_parts \
                    = self.search_layer_opt_config( layer_id=lid,
                                                part_list=partitions_list,
                                                matmul_dataflow_list=matmul_dataflow_list,
                                                vec_dataflow_list=vector_dataflow_list
                                               )

                entry = [lid, input_parts, filter_parts, opt_unit, opt_dataflow]
                self.partition_table += [entry]
    #
    #  

    def create_opt_SET_RA_tree_part_table(self):
        # print("DEBUG: Entered SET part mode")                
        SET_optimal = {}
        with open(self.SET_json_file) as f:     
        # Load the JSON data into a dictionary   
            SET_optimal = json.load(f)
        num_layers = self.workload.get_num_layers()
        matmul_dataflow_list = [self.config.get_matmul_dataflow()]
        vector_dataflow_list = [self.config.get_vector_dataflow()]

        for lid in range(num_layers):
            layer_params = self.workload.get_layer_params(lid)
            layer_type = layer_params[0]

            if layer_type in ['conv', 'gemm']:
                # Fetch the number of cores specific to the layer type from SET_optimal
                
                ### optimal algo
                num_cores = SET_optimal["Layers"][str(lid)]['num_cores']
                input_part_a = SET_optimal["Layers"][str(lid)]['input_part']
                filter_part_a = SET_optimal["Layers"][str(lid)]['filter_part']
                
                ### LS
                # num_cores = 16
                # input_part_a = 4
                # filter_part_a = 4
                  
                partitions_list = [[input_part_a,filter_part_a]]
                
                # Search for the optimal configuration using the updated partitions list
                opt_unit, opt_dataflow, input_parts, filter_parts = self.search_layer_opt_config(
                    layer_id=lid,
                    part_list=partitions_list,
                    matmul_dataflow_list=matmul_dataflow_list,
                    vec_dataflow_list=vector_dataflow_list
                )

                # Create the entry for this layer
                entry = [lid, input_parts, filter_parts, opt_unit, opt_dataflow]
                self.partition_table += [entry]
    
    #  
    
    def create_opt_ifmap_part_table(self):
        num_cores = self.config.get_num_cores()
        num_layers = self.workload.get_num_layers()
        partitions_list = [[num_cores, 1]]
        matmul_dataflow_list = [self.config.get_matmul_dataflow()]
        vector_dataflow_list = [self.config.get_vector_dataflow()]

        for lid in range(num_layers):
            layer_params = self.workload.get_layer_params(lid)
            if (layer_params[0] in ['conv', 'gemm']):
                opt_unit, opt_dataflow, input_parts, filter_parts \
                    = self.search_layer_opt_config(layer_id=lid,
                                               part_list=partitions_list,
                                               matmul_dataflow_list=matmul_dataflow_list,
                                               vec_dataflow_list=vector_dataflow_list
                                               )

            entry = [lid, input_parts, filter_parts, opt_unit, opt_dataflow]
            self.partition_table += [entry]

    #
    def create_opt_filter_part_table(self):
        num_cores = self.config.get_num_cores()
        num_layers = self.workload.get_num_layers()
        partitions_list = [[1, num_cores]]
        matmul_dataflow_list = [self.config.get_matmul_dataflow()]
        vector_dataflow_list = [self.config.get_vector_dataflow()]

        for lid in range(num_layers):
            layer_params = self.workload.get_layer_params(lid)
            if (layer_params[0] in ['conv', 'gemm']):
                opt_unit, opt_dataflow, input_parts, filter_parts \
                    = self.search_layer_opt_config(layer_id=lid,
                                               part_list=partitions_list,
                                               matmul_dataflow_list=matmul_dataflow_list,
                                               vec_dataflow_list=vector_dataflow_list
                                               )

            entry = [lid, input_parts, filter_parts, opt_unit, opt_dataflow]
            self.partition_table += [entry]

    #
    def search_layer_opt_config(self, layer_id=0, part_list=None,
                                matmul_dataflow_list=None, vec_dataflow_list=None):
        assert not layer_id < 0
        assert part_list is not None

        opt_matmul_part_entries = []
        opt_vector_part_entries = []
        opt_matmul_runtime = 10 ** 10
        opt_vector_runtime = 10 ** 10

        use_matmul, use_vector = self.config.get_compute_unit_valids()
        if use_matmul:
            assert matmul_dataflow_list is not None
            opt_matmul_runtime, opt_matmul_part_entries =  \
                self.search_matmul_layer_opt_config(layer_id=layer_id, part_list=part_list,
                                                    dataflow_list=matmul_dataflow_list)
            
        if use_vector:
            assert vec_dataflow_list is not None
            opt_vector_runtime, opt_vector_part_entries = \
                self.search_vector_layer_opt_config(layer_id=layer_id, part_list=part_list,
                                                    dataflow_list=vec_dataflow_list)
           
        if use_matmul and use_vector:
            if opt_matmul_runtime < opt_vector_runtime:
                print(opt_matmul_part_entries)
                return opt_matmul_part_entries
            else:
                print(opt_vector_part_entries)
                return opt_vector_part_entries
        elif use_matmul:
            #print(opt_matmul_part_entries)
            return opt_matmul_part_entries
        else:
            return opt_vector_part_entries

    #
    def search_matmul_layer_opt_config(self, layer_id=0, part_list=None, dataflow_list=None):
        min_runtime = 10 ** 10
        M, N, K = self.workload.get_transformed_mnk_dimensions(layer_id)

        arr_row, arr_col = self.config.get_matmul_dims()

        opt_df = 'os'
        opt_input_part = 1
        opt_filter_part = 1

        for part_pair in part_list:
            input_part = part_pair[0]
            filter_part = part_pair[1]

            for df in dataflow_list:
                runtime = self.get_mat_mul_analytical_runtime(M, N, K, df, arr_row, arr_col, input_part, filter_part)

                if runtime < min_runtime:
                    min_runtime = runtime
                    opt_df = df
                    opt_input_part = input_part
                    opt_filter_part = filter_part

        return min_runtime, ['matmul', opt_df, opt_input_part, opt_filter_part]

    #
    def search_vector_layer_opt_config(self, layer_id=0, part_list=None, dataflow_list=None):
        min_runtime = 10 ** 10
        M, N, K = self.workload.get_transformed_mnk_dimensions(layer_id)

        num_vec_units = self.config.get_vector_dim()

        opt_df = 'os'
        opt_input_part = 1
        opt_filter_part = 1

        for part_pair in part_list:
            input_part = part_pair[0]
            filter_part = part_pair[1]

            for df in dataflow_list:
                if df == 'os' or df == 'is':
                    arr_row, arr_col = [num_vec_units, 1]
                else:   # df == 'ws':
                    arr_row, arr_col = [1, num_vec_units]

                runtime = self.get_mat_mul_analytical_runtime(M, N, K, df, arr_row, arr_col, input_part,
                                                              filter_part)

                if runtime < min_runtime:
                    min_runtime = runtime
                    opt_df = df
                    opt_input_part = input_part
                    opt_filter_part = filter_part

        return min_runtime, ['vector', opt_df, opt_input_part, opt_filter_part]

    #
    @staticmethod
    def get_mat_mul_analytical_runtime(M=1, N=1, K=1, df='os',
                                       arr_row=1, arr_col=1,
                                       input_part=1, filt_part=1):
        assert df in ['os', 'is', 'ws']

        if df == 'os':
            max_input_part = math.floor(M/arr_row)
            max_filter_part = math.floor(N/arr_col)

        elif df == 'ws':
            max_input_part = M
            max_filter_part = math.floor(N/arr_col)

        else: # df == 'is'
            max_input_part = math.floor(M/arr_col)
            max_filter_part = N

        input_part = min(max_input_part, input_part)
        filter_part = min(max_filter_part, filt_part)

        Mprime = math.ceil(M/input_part)
        Nprime = math.ceil(N/filter_part)

        if df == 'os':
            Sr, Sc, T = [Mprime, Nprime, K]
        elif df == 'ws':
            Sr, Sc, T = [K, Nprime, Mprime]
        else: # df == 'is'
            Sr, Sc, T = [K, Mprime, Nprime]

        runtime = 2 * arr_row + arr_col + T - 2
        runtime *= math.ceil(Sr / arr_row) * math.ceil(Sc / arr_col)

        return runtime

    #
    def get_layer_partitions(self, layer_id=0):
        assert self.partition_table_valid, 'Partition table is not valid'
        count = 0
        for i in range (layer_id):
            if self.workload.topo_list[i][2] == 'maxpool'or self.workload.topo_list[i][2] == 'relu' or self.workload.topo_list[i][2] == 'adde':
              count = count + 1
            
      
        partition_data = self.partition_table[layer_id- count]
        input_part = partition_data[1]
        filter_part = partition_data[2]

        return input_part, filter_part

    #
    def get_opt_compute_params(self, layer_id=0):
        assert self.partition_table_valid, 'Partition table is not valid'
        count = 0
        for i in range (layer_id):
           if self.workload.topo_list[i][2] == 'maxpool' or self.workload.topo_list[i][2] == 'relu' or self.workload.topo_list[i][2] == 'adde':
             count = count + 1
        partition_data = self.partition_table[layer_id-count]
        opt_compute_unit = partition_data[3]
        opt_dataflow = partition_data[4]

        return opt_compute_unit, opt_dataflow

    #
    def read_user_partition_table(self, filename=''):

        f = open(filename, 'r')
        first = True

        for row in f:
            if first:
                first = False
            else:
                elems = row.strip().split(',')
                entry = [int(e.strip()) for e in elems[0:-2]]
                df = elems[-1].strip()
                unit = elems[-2].strip()
                assert unit in ['matmul', 'vector']
                assert df in ['os', 'ws', 'is']

                entry += [unit, df]

                self.partition_table += [entry]

        self.partition_table_valid = True

    #
    def write_current_partition_table(self, filename):
        assert self.partition_table_valid

        f = open(filename, 'w')

        header = ', '.join(self.partition_table_cols) + '\n'
        f.write(header)

        for entry in self.partition_table:
            log = ', '.join([str(x) for x in entry]) + '\n'
            f.write(log)

        f.close()

