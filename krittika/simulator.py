import os
import statistics

from krittika.workload_manager import WorkloadManager
from scalesim.scale_config import scale_config
from scalesim.compute.operand_matrix import operand_matrix
from krittika.config.krittika_config import KrittikaConfig
from krittika.partition_manager import PartitionManager
from krittika.single_layer_sim import SingleLayerSim
from krittika.config.network_config import NetworkConfig
from krittika.noc.noc_factory import NoCFactory


class Simulator:
    def __init__(self):
        # Objects
        self.config_obj = KrittikaConfig()
        self.network_config_obj = NetworkConfig()
        self.partition_obj = PartitionManager()
        self.workload_obj = WorkloadManager()
        self.noc = None

        # State
        self.verbose = True
        self.trace_gen_flag = True
        self.autopartition = False
        self.single_layer_objects_list = []
        self.top_path = "./"
        self.reports_dir_path = "./"

        # REPORT Structures
        self.total_cycles_report_grid = []
        self.stall_cycles_report_grid = []
        self.overall_utils_report_grid = []
        self.mapping_eff_report_grid = []
        self.cycles_report_avg_items = []
        self.cycles_report_ready = False
        self.bandwidth_report_avg_items = []
        self.bandwidth_report_ready = False
        self.detailed_report_avg_items = []
        self.detailed_report_ready = False

        # Flags
        self.params_valid = False
        self.runs_done = False
        self.reports_dir_ready = False

    def set_params(
        self,
        config_filename="",
        network_config_filename="",
        workload_filename="",
        custom_partition_filename="",
        reports_dir_path="./",
        verbose=True,
        noc_obj= None,
        save_traces=True,
    ):
        # Read the user input and files and prepare the objects
        self.config_obj.read_config_from_file(filename=config_filename)
        self.network_config_obj.read_network_config(filename=network_config_filename)

        self.workload_obj = WorkloadManager()
        self.workload_obj.read_topologies(workload_filename=workload_filename)
        self.noc_obj = noc_obj

        # print(self.workload_obj.get_simd_operation(0))

        self.partition_obj.set_params(
            config_obj=self.config_obj, workload_obj=self.workload_obj
        )
        self.autopartition = self.config_obj.is_autopartition()
        if self.autopartition:
            self.partition_obj.create_partition_table()
        else:
            self.partition_obj.read_user_partition_table(
                filename=custom_partition_filename
            )

        # This can be changed in the future to support other NoCs
        # For now, directly get an AstraSimANoC
        self.noc = NoCFactory.get_noc(
            noc_type="AstraSimANoC", NetworkConfig=self.network_config_obj
        )

        # FIXME: Just a simple example of the API
        self.noc.setup()

        t_ids = []
        for i in range(10):
            t = self.noc.post((500 * (i + 2)), 1, 3, 512)
            #print("t",i," ",(500 * (i+2)))
            t_ids.append(t)
        
        self.noc.deliver_all_txns()

        latencies = []
        for t in t_ids:
            l = self.noc.get_latency(t)
            latencies.append(l)

        stat_lat = self.noc.get_static_latency(0, 1, 512)

        self.verbose = verbose
        self.trace_gen_flag = save_traces

        self.reports_dir_path = reports_dir_path

        self.params_valid = True
        self.enable_ls_partition = False
        self.enable_lp_partition = True

        self.tile_num = {} # Global variable as of now

    #

    def run_ls():
        assert self.params_valid, "Cannot run simulation without inputs"

        # Run compute simulations for all layers first
        num_layers = self.workload_obj.get_num_layers()

        # Update the offsets to generate operand matrices
        single_arr_config = scale_config()
        conf_list = scale_config.get_default_conf_as_list()
        user_offsets = self.config_obj.get_operand_offsets()
        conf_list[6] = user_offsets[0]
        conf_list[7] = user_offsets[1]
        conf_list[8] = user_offsets[2]
        conf_list[10] = self.config_obj.get_bandwidth_use_mode()
        conf_list.append(self.config_obj.get_interface_bandwidths()[0])
        single_arr_config.update_from_list(conf_list=conf_list)
        for layer_id in range(num_layers):
            if self.verbose:
                print('Running Layer ' + str(layer_id))
            this_layer_op_mat_obj = operand_matrix()
            layer_params = self.workload_obj.get_layer_params(layer_id)
            if (layer_params[0] in ['conv', 'gemm']):
                this_layer_op_mat_obj.set_params(config_obj=single_arr_config,
                                             topoutil_obj=self.workload_obj,
                                             layer_id=layer_id)
                this_layer_op_mat_obj.create_operand_matrices()

                this_layer_sim = SingleLayerSim()
                this_layer_sim.set_params(config_obj=self.config_obj,
                                      op_mat_obj=this_layer_op_mat_obj,
                                      partitioner_obj=self.partition_obj,
                                      layer_id=layer_id,core_id= layer_id,
                                      log_top_path=self.top_path,
                                      verbosity=self.verbose)
                this_layer_sim.run()
                self.single_layer_objects_list += [this_layer_sim]

                if self.verbose:
                    print('SAVING TRACES')
                this_layer_sim.save_traces()
                this_layer_sim.gather_report_items_across_cores()
            elif (layer_params[0] in ['activation']):
                op_matrix = self.single_layer_objects_list[layer_id-1].get_ofmap_operand_matrix()

                this_layer_sim = SingleLayerSim()
                this_layer_sim.set_params(config_obj=self.config_obj,
                                      op_mat_obj=this_layer_op_mat_obj,
                                      partitioner_obj=self.partition_obj,
                                      layer_id=layer_id,
                                      log_top_path=self.top_path,
                                      verbosity=self.verbose)
                this_layer_sim.run_simd_all_parts(operand_matrix=op_matrix, optype = layer_params[1])
                self.single_layer_objects_list += [this_layer_sim]
                
                this_layer_sim.gather_simd_report_items_across_cores()
        
        self.runs_done = True
        self.generate_all_reports()        

    def run_lp(self):

        num_cores = self.workload_obj.get_num_layers() # self.workload_obj.get_num_cores()

        # Update the offsets to generate operand matrices
        single_arr_config = scale_config()
        conf_list = scale_config.get_default_conf_as_list()
        user_offsets = self.config_obj.get_operand_offsets()
        conf_list[6] = user_offsets[0]
        conf_list[7] = user_offsets[1]
        conf_list[8] = user_offsets[2]
        conf_list[10] = self.config_obj.get_bandwidth_use_mode()
        conf_list.append(self.config_obj.get_interface_bandwidths()[0])
        single_arr_config.update_from_list(conf_list=conf_list)   
        time_across_cores = {}
        time_across_cores_prev = {}
        executed_tile = {}
        this_layer_op_mat_obj={}
        this_layer_sim ={}
        for core_id in range(num_cores):
            time_across_cores[core_id] = 0
            time_across_cores_prev[core_id] = 0
            executed_tile[core_id] = -1
            self.tile_num[core_id] = -1
            this_layer_op_mat_obj[core_id] = operand_matrix()
            layer_params = self.workload_obj.get_layer_params(core_id)   
            if (layer_params[0] in ['conv', 'gemm']):
                this_layer_op_mat_obj[core_id].set_params(config_obj=single_arr_config,
                topoutil_obj=self.workload_obj,
                layer_id=core_id)
                this_layer_op_mat_obj[core_id].create_operand_matrices()
    
                this_layer_sim[core_id] = SingleLayerSim() ### again for now till milestone we can assume one core, hmm maybe have an additional self knob for hyrbvid
                this_layer_sim[core_id].set_params(config_obj=self.config_obj,
                                      op_mat_obj=this_layer_op_mat_obj[core_id],
                                      partitioner_obj=self.partition_obj,
                                      noc_obj = self.noc,
                                      layer_id=core_id,core_id= core_id,
                                      log_top_path=self.top_path,
                                      verbosity=self.verbose,skip_dram_reads=self.enable_lp_partition,skip_dram_writes = self.enable_lp_partition,num_cores = num_cores, enable_lp_partition = self.enable_lp_partition )
                this_layer_sim[core_id].run() ## This is run_compute
                this_layer_sim[core_id].setup_memory()
                self.single_layer_objects_list += [this_layer_sim[core_id]]
            #elif (layer_params[0] in ['activation']): ## TODO Need to fix this
            #    op_matrix = self.single_layer_objects_list[core_id-1].get_ofmap_operand_matrix()
    
            #    this_layer_sim = SingleLayerSim()
            #    this_layer_sim.set_params(config_obj=self.config_obj,
            #                          op_mat_obj=this_layer_op_mat_obj,
            #                          partitioner_obj=self.partition_obj,
            #                          layer_id=core_id,
            #                          log_top_path=self.top_path,
            #                          verbosity=self.verbose)
            #    this_layer_sim.run_simd_all_parts(operand_matrix=op_matrix, optype = layer_params[1])
            #    self.single_layer_objects_list += [this_layer_sim]
            
        self.time_overall=0 ## starts the cycles.
        # Need to create dependancy graph.
        completed = 0
        iterator = 0 # debug ppurposes
        for core_id in range(num_cores): ## dependancy grpahs
            this_layer_sim[core_id].tile_number = core_id*-1
        
        while(completed != num_cores): ## naive way of looping untill allof these are started.
            step_increment_cycles = 0
            completed = 0
            extra_noc_cycles = 0
            for core_id in range(num_cores):
                completed_per_core = this_layer_sim[core_id].run_mem_sim_all_parts_lp(core_id)
                #print("Returned number core",core_id,"tile",this_layer_sim[core_id].tile_number,"comepleted >?",completed_per_core)
                print(completed_per_core)
                completed += completed_per_core 
                if(this_layer_sim[core_id].tile_number < 0 ):
                    this_layer_sim[core_id].tile_number +=1
                    continue ## We dont wanna do any updates for the core if nothing was executed.
                if(completed_per_core == 1):
                    if(core_id != num_cores - 1):
                        time_across_cores_prev[core_id] = time_across_cores[core_id]
                        extra_noc_cycles = 10 #sreemanth api call
                    continue # Since we use a prev iteration values, they need to be updated correctly once you are done with one core's execution
                #print(this_layer_sim[core_id].this_part_mem.cycles_per_tile,step_increment_cycles,extra_noc_cycles)
                if(step_increment_cycles < this_layer_sim[core_id].this_part_mem.cycles_per_tile + extra_noc_cycles): 
                    step_increment_cycles = this_layer_sim[core_id].this_part_mem.cycles_per_tile + extra_noc_cycles ## Post updating to make sure add the noc cycles to thenext core.
                    #print("Step:",core_id,this_layer_sim[core_id].this_part_mem.cycles_per_tile,step_increment_cycles,extra_noc_cycles)
                if(core_id != 0 ): ### Need to double check this. Getting the per core absolute time using the rpevious core as reference
                    time_across_cores[core_id ] = time_across_cores_prev[core_id - 1 ] + extra_noc_cycles + this_layer_sim[core_id].this_part_mem.cycles_per_tile #DEBG 
                    #print("Core",core_id,time_across_cores_prev[core_id - 1 ],extra_noc_cycles,this_layer_sim[core_id].this_part_mem.cycles_per_tile)
                    #######
                else:
                    time_across_cores_prev[core_id] = time_across_cores[core_id]
                    time_across_cores[core_id] += this_layer_sim[core_id].this_part_mem.cycles_per_tile + extra_noc_cycles # May require -1
                extra_noc_cycles = 10
                    # sreemanth api
                if(core_id != (num_cores - 1)):
                    if not (core_id + 1) in this_layer_sim[core_id].tracking_id :
                         this_layer_sim[core_id].tracking_id[core_id+1] = {}
                    if not self.tile_num[core_id] in this_layer_sim[core_id].tracking_id[core_id + 1] :
                        this_layer_sim[core_id].tracking_id[core_id + 1][self.tile_num[core_id]] = {}
                    ### Call congestion unaware NoC to remove the 6 cyclesdelay here.
                    #print("NOc insertion Core:",core_id,"Tile ",this_layer_sim[core_id].tile_number," at time ",time_across_cores[core_id])
                    this_layer_sim[core_id].tracking_id[core_id+1][self.tile_num[core_id]] =self.noc.post(time_across_cores[core_id] ,
                    core_id, core_id+1, this_layer_sim[core_id].per_tile_size) # TODO replace this with SreemanthsAPI call.

                this_layer_sim[core_id].tile_number +=1
                
            ## Following 
            self.time_overall += step_increment_cycles ## Hmm weird last tile is meesing it up TODO, fix this or use the last ocre's time to fix this
            iterator+=1
            #print("Total TIme elapsed",self.time_overall)
            ####
            ### Query again the tracking id to get the latencies to adjust the time i guess
            ### NOC Deliver
            ## Reset traces
           #for core_id in range(num_cores):
           #    this_layer_sim[core_id].this_part_mem.reset()
           ####
           #self.noc.deliver_all_txns()
           #### Run the while loop again.
           ### Question, do we need to reset the layer obkets? i dont think so.
        
        for lid in range(num_cores):
            #print("Core",lid,time_across_cores[core_id])
            layer_params = self.workload_obj.get_layer_params(lid)
            if layer_params[0] in ["conv", "gemm"]: ## TODO mmanish remove activation    
                if self.verbose:
                    print("SAVING TRACES")
                this_layer_sim[lid].save_traces()
                this_layer_sim[lid].gather_report_items_across_cores()   
       
        print("Total Cycles taken for the sim is", time_across_cores[num_cores - 1]) 
        self.runs_done = True
        self.generate_all_reports()  

    def run(self):
        if self.enable_ls_partition:
            self.run_ls()
        else:
            self.run_lp()

    def generate_all_reports(self):
        self.create_cycles_report_structures()
        self.create_bandwidth_report_structures()
        self.create_detailed_report_structures()
        self.save_all_cycle_reports()
        self.save_all_bw_reports()
        self.save_all_detailed_reports()

    # Report generation
    def create_cycles_report_structures(self):
        assert self.runs_done

        for lid in range(self.workload_obj.get_num_layers()):
            layer_params = self.workload_obj.get_layer_params(lid)
            if layer_params[0] in ["conv", "gemm", "activation"]:
                this_layer_sim_obj = self.single_layer_objects_list[lid]
                total_cycles_list = this_layer_sim_obj.total_cycles_list
                stall_cycles_list = this_layer_sim_obj.stall_cycles_list
                overall_util_list = this_layer_sim_obj.overall_util_list
                mapping_eff_list = this_layer_sim_obj.mapping_eff_list
                compute_util_list = this_layer_sim_obj.compute_util_list
                self.cycles_report_avg_items += [statistics.mean(total_cycles_list)]
                self.cycles_report_avg_items += [statistics.mean(stall_cycles_list)]
                self.cycles_report_avg_items += [statistics.mean(overall_util_list)]
                self.cycles_report_avg_items += [statistics.mean(mapping_eff_list)]
                self.cycles_report_avg_items += [statistics.mean(compute_util_list)]

        self.cycles_report_ready = True

    def create_bandwidth_report_structures(self):
        assert self.runs_done

        for lid in range(self.workload_obj.get_num_layers()):
            layer_params = self.workload_obj.get_layer_params(lid)
            if layer_params[0] in ["conv", "gemm"]:
                this_layer_sim_obj = self.single_layer_objects_list[lid]
                avg_ifmap_sram_bw_list = this_layer_sim_obj.avg_ifmap_sram_bw_list
                avg_ifmap_dram_bw_list = this_layer_sim_obj.avg_ifmap_dram_bw_list
                avg_filter_sram_bw_list = this_layer_sim_obj.avg_filter_sram_bw_list
                avg_filter_dram_bw_list = this_layer_sim_obj.avg_filter_dram_bw_list
                avg_ofmap_sram_bw_list = this_layer_sim_obj.avg_ofmap_sram_bw_list
                avg_ofmap_dram_bw_list = this_layer_sim_obj.avg_ofmap_dram_bw_list

                self.bandwidth_report_avg_items += [
                    statistics.mean(avg_ifmap_sram_bw_list)
                ]
                self.bandwidth_report_avg_items += [
                    statistics.mean(avg_filter_sram_bw_list)
                ]
                self.bandwidth_report_avg_items += [
                    statistics.mean(avg_ofmap_sram_bw_list)
                ]
                self.bandwidth_report_avg_items += [
                    statistics.mean(avg_ifmap_dram_bw_list)
                ]
                self.bandwidth_report_avg_items += [
                    statistics.mean(avg_filter_dram_bw_list)
                ]
                self.bandwidth_report_avg_items += [
                    statistics.mean(avg_ofmap_dram_bw_list)
                ]

        self.bandwidth_report_ready = True

    def create_detailed_report_structures(self):
        assert self.runs_done

        for lid in range(self.workload_obj.get_num_layers()):
            layer_params = self.workload_obj.get_layer_params(lid)
            if layer_params[0] in ["conv", "gemm"]:
                this_layer_sim_obj = self.single_layer_objects_list[lid]
                ifmap_sram_start_cycle_list = (
                    this_layer_sim_obj.ifmap_sram_start_cycle_list
                )
                ifmap_sram_stop_cycle_list = (
                    this_layer_sim_obj.ifmap_sram_stop_cycle_list
                )
                ifmap_sram_reads_list = this_layer_sim_obj.ifmap_sram_reads_list
                filter_sram_start_cycle_list = (
                    this_layer_sim_obj.filter_sram_start_cycle_list
                )
                filter_sram_stop_cycle_list = (
                    this_layer_sim_obj.filter_sram_stop_cycle_list
                )
                filter_sram_reads_list = this_layer_sim_obj.filter_sram_reads_list
                ofmap_sram_start_cycle_list = (
                    this_layer_sim_obj.ofmap_sram_start_cycle_list
                )
                ofmap_sram_stop_cycle_list = (
                    this_layer_sim_obj.ofmap_sram_stop_cycle_list
                )
                ofmap_sram_writes_list = this_layer_sim_obj.ofmap_sram_writes_list

                ifmap_dram_start_cycle_list = (
                    this_layer_sim_obj.ifmap_dram_start_cycle_list
                )
                ifmap_dram_stop_cycle_list = (
                    this_layer_sim_obj.ifmap_dram_stop_cycle_list
                )
                ifmap_dram_reads_list = this_layer_sim_obj.ifmap_dram_reads_list
                filter_dram_start_cycle_list = (
                    this_layer_sim_obj.filter_dram_start_cycle_list
                )
                filter_dram_stop_cycle_list = (
                    this_layer_sim_obj.filter_dram_stop_cycle_list
                )
                filter_dram_reads_list = this_layer_sim_obj.filter_dram_reads_list
                ofmap_dram_start_cycle_list = (
                    this_layer_sim_obj.ofmap_dram_start_cycle_list
                )
                ofmap_dram_stop_cycle_list = (
                    this_layer_sim_obj.ofmap_dram_stop_cycle_list
                )
                ofmap_dram_writes_list = this_layer_sim_obj.ofmap_dram_writes_list

                self.detailed_report_avg_items += [
                    statistics.mean(ifmap_sram_start_cycle_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(ifmap_sram_stop_cycle_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(ifmap_sram_reads_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(filter_sram_start_cycle_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(filter_sram_stop_cycle_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(filter_sram_reads_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(ofmap_sram_start_cycle_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(ofmap_sram_stop_cycle_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(ofmap_sram_writes_list)
                ]

                self.detailed_report_avg_items += [
                    statistics.mean(ifmap_dram_start_cycle_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(ifmap_dram_stop_cycle_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(ifmap_dram_reads_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(filter_dram_start_cycle_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(filter_dram_stop_cycle_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(filter_dram_reads_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(ofmap_dram_start_cycle_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(ofmap_dram_stop_cycle_list)
                ]
                self.detailed_report_avg_items += [
                    statistics.mean(ofmap_dram_writes_list)
                ]

        self.detailed_report_ready = True

    def save_all_cycle_reports(self):
        assert self.cycles_report_ready
        compute_report_name = self.top_path + "traces/" + "/COMPUTE_REPORT.csv"
        compute_report = open(compute_report_name, "w")
        header = "LayerID, Total Cycles, Stall Cycles, Overall Util %, Mapping Efficiency %, Compute Util %,\n"
        columns = header.count(",") - 1
        compute_report.write(header)

        for lid in range(self.workload_obj.get_num_layers()):
            layer_params = self.workload_obj.get_layer_params(lid)
            if layer_params[0] in ["conv", "gemm", "activation"]:
                log = str(lid) + ", "
                log += ", ".join(
                    [
                        str(x)
                        for x in self.cycles_report_avg_items[
                            lid * columns : lid * columns + 5
                        ]
                    ]
                )
                log += ",\n"
                compute_report.write(log)

        compute_report.close()

    def save_all_bw_reports(self):
        assert self.bandwidth_report_ready

        bandwidth_report_name = self.top_path + "traces" + "/BANDWIDTH_REPORT.csv"
        bandwidth_report = open(bandwidth_report_name, "w")
        header = "LayerID, Avg IFMAP SRAM BW, Avg FILTER SRAM BW, Avg OFMAP SRAM BW, "
        header += "Avg IFMAP DRAM BW, Avg FILTER DRAM BW, Avg OFMAP DRAM BW,\n"
        columns = header.count(",") - 1

        bandwidth_report.write(header)

        for lid in range(self.workload_obj.get_num_layers()):
            layer_params = self.workload_obj.get_layer_params(lid)
            if layer_params[0] in ["conv", "gemm"]:
                log = str(lid) + ", "
                log += ", ".join(
                    [
                        str(x)
                        for x in self.bandwidth_report_avg_items[
                            lid * columns : lid * columns + columns
                        ]
                    ]
                )
                log += ",\n"
                bandwidth_report.write(log)

        bandwidth_report.close()

    def save_all_detailed_reports(self):
        assert self.detailed_report_ready

        detailed_report_name = self.top_path + "traces" + "/DETAILED_ACCESS_REPORT.csv"
        detailed_report = open(detailed_report_name, "w")
        header = "LayerID, "
        header += "SRAM IFMAP Start Cycle, SRAM IFMAP Stop Cycle, SRAM IFMAP Reads, "
        header += "SRAM Filter Start Cycle, SRAM Filter Stop Cycle, SRAM Filter Reads, "
        header += "SRAM OFMAP Start Cycle, SRAM OFMAP Stop Cycle, SRAM OFMAP Writes, "
        header += "DRAM IFMAP Start Cycle, DRAM IFMAP Stop Cycle, DRAM IFMAP Reads, "
        header += "DRAM Filter Start Cycle, DRAM Filter Stop Cycle, DRAM Filter Reads, "
        header += "DRAM OFMAP Start Cycle, DRAM OFMAP Stop Cycle, DRAM OFMAP Writes,\n"
        columns = header.count(",") - 1

        detailed_report.write(header)

        for lid in range(self.workload_obj.get_num_layers()):
            layer_params = self.workload_obj.get_layer_params(lid)
            if layer_params[0] in ["conv", "gemm"]:
                log = str(lid) + ", "
                log += ", ".join(
                    [
                        str(x)
                        for x in self.detailed_report_avg_items[
                            lid * columns : lid * columns + columns
                        ]
                    ]
                )
                log += ",\n"
                detailed_report.write(log)

        detailed_report.close()
