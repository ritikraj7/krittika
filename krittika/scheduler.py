import numpy as np
import math
from collections import deque


from scalesim.memory.double_buffered_scratchpad_mem import double_buffered_scratchpad
from scalesim.compute.operand_matrix import operand_matrix
from krittika.config.krittika_config import KrittikaConfig

from krittika.chiplet_system import ChipletSys

class Scheduler:
    '''
        The objective of this class
        1. Read the chiplets that are going to be used
        2. Partition the matrices
        3. Generate the dependency matrices
        4. Calculate the latency
    '''

    def __init__(self):

        #Member Objects
        self.chiplet_sys = ChipletSys()
        self.op_mat_obj = operand_matrix()
        self.config_obj = KrittikaConfig() 
        self.dependency_matrix = []
        self.status_matrix = [] #(x,y) x-inp_dependency, y-run-status
        self.ready_to_run = deque()
        self.comm_latency_matrix = None
        self.end_latency_matrix = None
        self.ifmap_size_matrix = None
        self.data_dist_matrix = None
        #set these two in set_params
        #set this based on DRAM to SRAM latency
        self.init_latency = 0
        #hyper parameter
        self.cycles_per_sec = 1.8*math.pow(2,30)
        self.bandwidth = 1*math.pow(2,33)
        self.latency_per_hop = 1
        self.src_weightage = 1

        #Flags
        self.verbose = True

    def set_params(self,
                   chiplet_sys = ChipletSys(),
                   op_mat_obj = operand_matrix(),
                   config_obj = KrittikaConfig(),
                   verbosity=True):
        self.chiplet_sys = chiplet_sys
        self.op_mat_obj = op_mat_obj
        self.config_obj = config_obj
        self.verbose = verbosity

    def count_non_negative(self, list):
        negative_values = sum(sublist.count(-1) for sublist in list)
        total_values = sum(len(sublist) for sublist in list)
        non_negative = total_values - negative_values
        return non_negative

    def non_uniform_work_dist(self, occupancy_m, N_src):
        data_dist_m = np.zeros((occupancy_m.shape[0],occupancy_m.shape[1]))

        srcs = {}
        coordinates = {}
        for i in range(occupancy_m.shape[0]):
            for j in range(occupancy_m.shape[1]):
                if (occupancy_m[i][j] < 0):
                    srcs[occupancy_m[i][j]] = (i,j)
                if (occupancy_m[i][j] > 0):
                    if (occupancy_m[i][j] in coordinates):
                        coordinates[occupancy_m[i][j]].append((i,j))
                    else:
                        coordinates[occupancy_m[i][j]] = [(i,j)]

        total_distance = []
        for i in range (N_src):
            total_dist = 0
            src = i+1
            for coord in coordinates[src]:
                total_dist = total_dist + 1 + abs(coord[0] - srcs[-1*src][0]) + abs(coord[1] - srcs[-1*src][1])

            total_dist = total_dist + 1 
            total_distance.append(total_dist)
            print ("i = ", i, "tot dist = ", total_dist)

        for i in range (N_src):
            max_hopcount = 0
            tot_assigned = 0
            src = i+1
            #Find max hop count
            for coord in coordinates[src]:
                hop_count = abs(coord[0] - srcs[-1*src][0]) + abs(coord[1] - srcs[-1*src][1]) + 1
                if (max_hopcount < hop_count):
                    max_hopcount = hop_count
            #assign data
            for coord in coordinates[src]:
                hop_count = abs(coord[0] - srcs[-1*src][0]) + abs(coord[1] - srcs[-1*src][1]) + 1
                data_dist_m[coord[0]][coord[1]] = (max_hopcount - hop_count + 1)/total_distance[i]
                tot_assigned = tot_assigned + max_hopcount - hop_count + 1

            hop_count = 1
            
            data_dist_m[srcs[-1*src][0]][srcs[-1*src][1]] = max_hopcount - hop_count + 1 
            tot_assigned = tot_assigned + max_hopcount - hop_count + 1
            assign_leftover_to_src = total_distance[i] - tot_assigned
            data_dist_m[srcs[-1*src][0]][srcs[-1*src][1]] += assign_leftover_to_src
            data_dist_m[srcs[-1*src][0]][srcs[-1*src][1]] /= total_distance[i]
        
        return data_dist_m

    def workload_distribution(self, uniform = 1):
        ifmap_matrix, filter_matrix, ofmap_matrix = self.op_mat_obj.get_all_operand_matrix()

        if(uniform==1):
            input_rows_per_part = math.ceil(ifmap_matrix.shape[0] / self.chiplet_sys.num_input_part)
            filter_cols_per_part = math.ceil(filter_matrix.shape[1] / self.chiplet_sys.num_filter_part)

            self.comm_latency_matrix = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))
            self.end_latency_matrix = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))

            self.ifmap_size_matrix = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))

            for inp_part in range(self.chiplet_sys.num_input_part):
                ifmap_row_start = inp_part * input_rows_per_part
                ifmap_row_end = min(ifmap_row_start + input_rows_per_part, ifmap_matrix.shape[0])

                ifmap_part = ifmap_matrix[ifmap_row_start:ifmap_row_end,:]
                this_row_dependency = []
                this_row_status = []
                this_row_latency = []

                for filt_part in range(self.chiplet_sys.num_filter_part):
                    filt_col_start = filt_part * filter_cols_per_part
                    filt_col_end = min(filt_col_start + filter_cols_per_part, filter_matrix.shape[1])

                    filter_part = filter_matrix[:, filt_col_start: filt_col_end]
                    ofmap_part = ofmap_matrix[ifmap_row_start: ifmap_row_end, filt_col_start:filt_col_end]

                    #Assign the work to Chiplet
                    self.chiplet_sys.chiplet_matrix[inp_part][filt_part].compute_node.set_operands(ifmap_opmat=ifmap_part,
                                                                                                    filter_opmat=filter_part,
                                                                                        ofmap_opmat=ofmap_part)
                    
                    #the sizes of the ifmap and filt for this part of the communication
                    ifmap_part_size = np.sum(ifmap_part != -1)
                    self.ifmap_size_matrix[inp_part][filt_part] = ifmap_part_size

                    if(filt_part == 0):
                        inp_dep_coord = (-1, -1)
                        this_row_status.append([1,0])
                        self.comm_latency_matrix[inp_part][filt_part] = self.init_latency
                    else:
                        inp_dep_coord = (inp_part, filt_part - 1)
                        this_row_status.append([0,0])
                        self.comm_latency_matrix[inp_part][filt_part] = self.comm_latency_matrix[inp_part][filt_part-1] + np.ceil((ifmap_part_size*8/self.bandwidth)*self.cycles_per_sec)


                    if(inp_dep_coord == (-1,-1)):
                        if(self.ifmap_size_matrix[inp_part][filt_part] != 0):
                            self.ready_to_run.append((inp_part, filt_part))

                    this_row_dependency.append((inp_dep_coord))
                self.dependency_matrix.append(this_row_dependency)
                self.status_matrix.append(this_row_status)

        #else:

            print("Dependency matrix:")
            print(self.dependency_matrix)
            print("Status Matrix")
            print(self.status_matrix)
            print("Communication Latency Matrix")
            print(self.comm_latency_matrix)
            print("ifmap_size_matrix:")
            print(self.ifmap_size_matrix)

        elif(uniform==2): ###non-unfiorm + communication
            
    # Define the parameters for the greedy function
            N_src = self.chiplet_sys.num_input_part
            destination_list = [(i, j) for i in range(self.chiplet_sys.num_input_part) for j in range(self.chiplet_sys.num_filter_part)]
            src_list = []
            occupancy_m = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))
            occupancy_m = self._greedy(occupancy_m, N_src, destination_list, -1, None, src_list)

            print("Updated Occupancy Matrix with Greedy Algorithm:")
            print(occupancy_m)

            # Ensure that there are sources to place rows
            for i in range(occupancy_m.shape[0]):
                for j in range(occupancy_m.shape[1]):
                    if(occupancy_m[i][j] != 0):
                        src_list.append((i,j))

            print("PLACING ROWS")
            N_left = self.chiplet_sys.num_filter_part - 1
            destination_list = []
            for src in src_list:
                destination_list.append([src])
            for i in range(N_left):
                ii = 1
                for j in range(len(src_list)):
                    occupancy_m[src_list[j][0]][src_list[j][1]] = ii
                    occupancy_m = self._greedy(occupancy_m, 1, destination_list[j], ii, src, src_list)
                    for row in range(occupancy_m.shape[0]):
                        for col in range(occupancy_m.shape[1]):
                            if(occupancy_m[row][col] == ii):
                                destination_list[j].append((row,col))
                                destination_list[j] = list(set(destination_list[j]))
                    ii += 1
            print(occupancy_m)

            print("Updating SRC")
            latency_mat = np.zeros((len(destination_list), len(destination_list[0])))
            for i in range(len(destination_list)):
                for j in range(len(destination_list[i])):
                    tot_latency = 0
                    for otherchips in destination_list[i]:
                        tot_latency += self._latency(destination_list[i][j], otherchips)
                    latency_mat[i][j] = tot_latency
                thissrc = destination_list[i][np.argmin(latency_mat[i])]
                occupancy_m[thissrc[0]][thissrc[1]] = -(i+1)

            print(occupancy_m)   
            self.data_dist_m = self.non_uniform_work_dist (occupancy_m, N_src)
            
            print ("Data Dist Matrix matrix:")
            print (self.data_dist_m )
            total_filter_cols = filter_matrix.shape[1]

            filter_allocation_matrix = self.distribute_filters(occupancy_m, self.data_dist_m, total_filter_cols)
            print(filter_allocation_matrix)
            self.dependency_matrix = self.dependency_matrix_func(occupancy_m)
            input_rows_per_part = math.ceil(ifmap_matrix.shape[0] / self.chiplet_sys.num_input_part)

            self.comm_latency_matrix = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))
            self.end_latency_matrix = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))

            self.ifmap_size_matrix = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))            
            # Iterate over each source and its group
            for src in range(-1, -np.amax(np.abs(occupancy_m)).astype(int) - 1, -1):
                group_indices = np.argwhere(np.isin(occupancy_m, [src, -src]))
                group_indices_src = np.argwhere(occupancy_m == src)
                print(group_indices_src)
                this_row_dependency = []
                this_row_status = []                   
                filt_col_start = 0
                for idx_pair in group_indices:
                    inp_part, filt_part = idx_pair
                    filt_col_end = filt_col_start + filter_allocation_matrix[inp_part][filt_part]
                    
                    # Calculating the IFMAP and OFMAP matrix partitions based on the allocation
                    ifmap_row_start = inp_part * input_rows_per_part
                    ifmap_row_end = min((inp_part + 1) * input_rows_per_part, ifmap_matrix.shape[0])

                    
                    ifmap_part = ifmap_matrix[ifmap_row_start:ifmap_row_end, :]
                    filter_part = filter_matrix[:, filt_col_start:filt_col_end]
                    ofmap_part = ofmap_matrix[ifmap_row_start:ifmap_row_end, filt_col_start:filt_col_end]

                    # Assigning the work to the compute node associated with this part
                    self.chiplet_sys.chiplet_matrix[inp_part][filt_part].compute_node.set_operands(
                        ifmap_opmat=ifmap_part, filter_opmat=filter_part, ofmap_opmat=ofmap_part
                    )

                    # Moving to the next filter column start position
                    filt_col_start = filt_col_end
                    #the sizes of the ifmap and filt for this part of the communication
                    ifmap_part_size = np.sum(ifmap_part != -1)
                    self.ifmap_size_matrix[inp_part][filt_part] = ifmap_part_size
                    
   
            for inp_part in range(self.chiplet_sys.num_input_part):
                this_row_dependency = []
                this_row_status = []                 
                for filt_part in range(self.chiplet_sys.num_filter_part):
                     if(self.dependency_matrix[inp_part][filt_part]==(-1,-1)):
                         self.ready_to_run.append((inp_part, filt_part))
                         this_row_status.append([1,0])
                     else:  
                         this_row_status.append([0,0])
                self.status_matrix.append(this_row_status)              

            for latency_row in range(occupancy_m.shape[0]):
                for latency_col in range(occupancy_m.shape[1]):
                    c1=[latency_row,latency_col]
                    if(occupancy_m[latency_row][latency_col]>0):
                        c2=np.argwhere(occupancy_m==-occupancy_m[latency_row][latency_col])[0]
                    else:
                        c2=c1
                    self.comm_latency_matrix[latency_row][latency_col]=self._latency(c1,c2)*np.ceil((ifmap_part_size*8/self.bandwidth)*self.cycles_per_sec)                


            print("Dependency matrix:")
            print(self.dependency_matrix)
            print("Status Matrix")
            print(self.status_matrix)
            print("Communication Latency Matrix")
            print(self.comm_latency_matrix)
            print("ifmap_size_matrix:")
            print(self.ifmap_size_matrix)


        elif(uniform==3):    #### uniform + communication
            N_src = self.chiplet_sys.num_input_part
            destination_list = [(i, j) for i in range(self.chiplet_sys.num_input_part) for j in range(self.chiplet_sys.num_filter_part)]
            src_list = []
            occupancy_m = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))
            occupancy_m = self._greedy(occupancy_m, N_src, destination_list, -1, None, src_list)

            print("Updated Occupancy Matrix with Greedy Algorithm:")
            print(occupancy_m)

            # Ensure that there are sources to place rows
            for i in range(occupancy_m.shape[0]):
                for j in range(occupancy_m.shape[1]):
                    if(occupancy_m[i][j] != 0):
                        src_list.append((i,j))

            print("PLACING ROWS")
            N_left = self.chiplet_sys.num_filter_part - 1
            destination_list = []
            for src in src_list:
                destination_list.append([src])
            for i in range(N_left):
                ii = 1
                for j in range(len(src_list)):
                    occupancy_m[src_list[j][0]][src_list[j][1]] = ii
                    occupancy_m = self._greedy(occupancy_m, 1, destination_list[j], ii, src, src_list)
                    for row in range(occupancy_m.shape[0]):
                        for col in range(occupancy_m.shape[1]):
                            if(occupancy_m[row][col] == ii):
                                destination_list[j].append((row,col))
                                destination_list[j] = list(set(destination_list[j]))
                    ii += 1
            print(occupancy_m)

            print("Updating SRC")
            latency_mat = np.zeros((len(destination_list), len(destination_list[0])))
            for i in range(len(destination_list)):
                for j in range(len(destination_list[i])):
                    tot_latency = 0
                    for otherchips in destination_list[i]:
                        tot_latency += self._latency(destination_list[i][j], otherchips)
                    latency_mat[i][j] = tot_latency
                thissrc = destination_list[i][np.argmin(latency_mat[i])]
                occupancy_m[thissrc[0]][thissrc[1]] = -(i+1)

            print(occupancy_m)               
            input_rows_per_part = math.ceil(ifmap_matrix.shape[0] / self.chiplet_sys.num_input_part)
            filter_cols_per_part = math.ceil(filter_matrix.shape[1] / self.chiplet_sys.num_filter_part)
            self.dependency_matrix = self.dependency_matrix_func(occupancy_m)
            self.comm_latency_matrix = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))
            self.end_latency_matrix = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))
            self.ifmap_size_matrix = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))

            for src in range(-1, -np.amax(np.abs(occupancy_m)).astype(int) - 1, -1):
                group_indices = np.argwhere(np.isin(occupancy_m, [src, -src]))
                group_indices_src = np.argwhere(occupancy_m == src)
                this_row_dependency = []
                this_row_status = []                   
                filt_col_start = 0
                for idx_pair in group_indices:
                    inp_part, filt_part = idx_pair
                    filt_col_end = min(filt_col_start + filter_cols_per_part, filter_matrix.shape[1])                    
                    
                    # Calculating the IFMAP and OFMAP matrix partitions based on the allocation
                    ifmap_row_start = inp_part * input_rows_per_part
                    ifmap_row_end = min((inp_part + 1) * input_rows_per_part, ifmap_matrix.shape[0])
                    
                    ifmap_part = ifmap_matrix[ifmap_row_start:ifmap_row_end, :]
                    filter_part = filter_matrix[:, filt_col_start:filt_col_end]
                    ofmap_part = ofmap_matrix[ifmap_row_start:ifmap_row_end, filt_col_start:filt_col_end]

                    # Assigning the work to the compute node associated with this part
                    self.chiplet_sys.chiplet_matrix[inp_part][filt_part].compute_node.set_operands(
                        ifmap_opmat=ifmap_part, filter_opmat=filter_part, ofmap_opmat=ofmap_part
                    )

                    # Moving to the next filter column start position
                    filt_col_start = filt_col_end
                    #the sizes of the ifmap and filt for this part of the communication
                    ifmap_part_size = np.sum(ifmap_part != -1)
                    self.ifmap_size_matrix[inp_part][filt_part] = ifmap_part_size
                                   
   
            for inp_part in range(self.chiplet_sys.num_input_part):
                this_row_dependency = []
                this_row_status = []                 
                for filt_part in range(self.chiplet_sys.num_filter_part):
                     if(self.dependency_matrix[inp_part][filt_part]==(-1,-1)):
                         self.ready_to_run.append((inp_part, filt_part))
                         this_row_status.append([1,0])
                     else:  
                         this_row_status.append([0,0])
                self.status_matrix.append(this_row_status)              

            
            
            for latency_row in range(occupancy_m.shape[0]):
                for latency_col in range(occupancy_m.shape[1]):
                    c1=[latency_row,latency_col]
                    if(occupancy_m[latency_row][latency_col]>0):
                        c2=np.argwhere(occupancy_m==-occupancy_m[latency_row][latency_col])[0]
                    else:
                        c2=c1
                    self.comm_latency_matrix[latency_row][latency_col]=self._latency(c1,c2)*np.ceil((ifmap_part_size*8/self.bandwidth)*self.cycles_per_sec)  



            print("Dependency matrix:")
            print(self.dependency_matrix)
            print("Status Matrix")
            print(self.status_matrix)
            print("Communication Latency Matrix")
            print(self.comm_latency_matrix)
            print("ifmap_size_matrix:")
            print(self.ifmap_size_matrix)

        elif(uniform==4):  ####only non-uniform 
            occupancy_m = np.zeros((self.chiplet_sys.num_input_part,self.chiplet_sys.num_filter_part))
            for i in range(occupancy_m.shape[0]):
                occupancy_m[i] = (i+1)*np.ones(occupancy_m.shape[1])
            occupancy_m[:,0] = -1*occupancy_m[:,0]
            N_src = self.chiplet_sys.num_input_part
            print(occupancy_m)   
            self.data_dist_m = self.non_uniform_work_dist (occupancy_m, N_src)
            
            print ("Data Dist Matrix matrix:")
            print (self.data_dist_m )
            total_filter_cols = filter_matrix.shape[1]

            filter_allocation_matrix = self.distribute_filters(occupancy_m, self.data_dist_m, total_filter_cols)
            print(filter_allocation_matrix)
            self.dependency_matrix = self.dependency_matrix_func(occupancy_m)
            input_rows_per_part = math.ceil(ifmap_matrix.shape[0] / self.chiplet_sys.num_input_part)

            self.comm_latency_matrix = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))
            self.end_latency_matrix = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))

            self.ifmap_size_matrix = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))            
            # Iterate over each source and its group
            for src in range(-1, -np.amax(np.abs(occupancy_m)).astype(int) - 1, -1):
                group_indices = np.argwhere(np.isin(occupancy_m, [src, -src]))
                group_indices_src = np.argwhere(occupancy_m == src)
                this_row_dependency = []
                this_row_status = []                   
                filt_col_start = 0
                for idx_pair in group_indices:
                    inp_part, filt_part = idx_pair
                    filt_col_end = filt_col_start + filter_allocation_matrix[inp_part][filt_part]
                    
                    # Calculating the IFMAP and OFMAP matrix partitions based on the allocation
                    ifmap_row_start = inp_part * input_rows_per_part
                    ifmap_row_end = min((inp_part + 1) * input_rows_per_part, ifmap_matrix.shape[0])
                    
                    ifmap_part = ifmap_matrix[ifmap_row_start:ifmap_row_end, :]
                    filter_part = filter_matrix[:, filt_col_start:filt_col_end]
                    ofmap_part = ofmap_matrix[ifmap_row_start:ifmap_row_end, filt_col_start:filt_col_end]

                    # Assigning the work to the compute node associated with this part
                    self.chiplet_sys.chiplet_matrix[inp_part][filt_part].compute_node.set_operands(
                        ifmap_opmat=ifmap_part, filter_opmat=filter_part, ofmap_opmat=ofmap_part
                    )

                    # Moving to the next filter column start position
                    filt_col_start = filt_col_end
                    #the sizes of the ifmap and filt for this part of the communication
                    ifmap_part_size = np.sum(ifmap_part != -1)
                    self.ifmap_size_matrix[inp_part][filt_part] = ifmap_part_size
                    
              
   
            for inp_part in range(self.chiplet_sys.num_input_part):
                this_row_dependency = []
                this_row_status = []                 
                for filt_part in range(self.chiplet_sys.num_filter_part):
                     if(self.dependency_matrix[inp_part][filt_part]==(-1,-1)):
                         self.ready_to_run.append((inp_part, filt_part))
                         this_row_status.append([1,0])
                     else:  
                         this_row_status.append([0,0])
                self.status_matrix.append(this_row_status)              

            for latency_row in range(occupancy_m.shape[0]):
                for latency_col in range(occupancy_m.shape[1]):
                    c1=[latency_row,latency_col]
                    if(occupancy_m[latency_row][latency_col]>0):
                        c2=np.argwhere(occupancy_m==-occupancy_m[latency_row][latency_col])[0]
                    else:
                        c2=c1
                    self.comm_latency_matrix[latency_row][latency_col]=self._latency(c1,c2)*np.ceil((ifmap_part_size*8/self.bandwidth)*self.cycles_per_sec)  


            print("Dependency matrix:")
            print(self.dependency_matrix)
            print("Status Matrix")
            print(self.status_matrix)
            print("Communication Latency Matrix")
            print(self.comm_latency_matrix)
            print("ifmap_size_matrix:")
            print(self.ifmap_size_matrix)       


    def dependency_matrix_func(self, occupancy_m):

        dependency_m = []
        for i in range(occupancy_m.shape[0]):
            this_row_dep = []
            for j in range(occupancy_m.shape[1]):
                if(occupancy_m[i][j] == 0):
                    this_row_dep.append((-2,-2))
                elif(occupancy_m[i][j] > 0):
                    ii = occupancy_m[i][j]
                    row_index, col_index = np.where(occupancy_m == -ii)
                    neighbour_list = []
                    #Check in the 4 directions
                    K = [i-1,i+1]
                    L = [j-1,j+1]
                    for k in K:
                        if(k >= 0 and k < occupancy_m.shape[1]):
                            if(occupancy_m[k][j] == ii or occupancy_m[k][j] == -ii):
                                neighbour_list.append((k,j))
                    for l in L:
                        if(l >= 0 and l < occupancy_m.shape[0]):
                            if(occupancy_m[i][l] == ii) or occupancy_m[i][l] == -ii:
                                neighbour_list.append((i,l))

                    n_dist_src = 10000000
                    neigh = (-2,-2)
                    for n in neighbour_list:
                        dist = abs(n[0]-row_index[0]) + abs(n[1]-col_index[0])
                        if(dist < n_dist_src):
                            n_dist_src = dist
                            neigh = n

                    this_row_dep.append(neigh)
                else:
                    this_row_dep.append((-1,-1))
            dependency_m.append(this_row_dep)
        return dependency_m    



    def distribute_filters(self, occupancy_m, data_dist_m, total_filter_cols):
        filter_allocation_matrix = np.zeros_like(occupancy_m, dtype=int)
        for src in range(-1, -np.amax(np.abs(occupancy_m)).astype(int)-1, -1):
            group_indices = np.argwhere(np.isin(occupancy_m, [src, -src]))
            for idx_pair in group_indices:
                row_idx, col_idx = idx_pair
                filter_allocation_matrix[row_idx][col_idx] = int(data_dist_m[row_idx][col_idx] * total_filter_cols)
            

            total_allocated = np.sum(filter_allocation_matrix[group_indices[:, 0], group_indices[:, 1]])
            
            source_index = np.argwhere(occupancy_m == src)[0]
            
            surplus = total_filter_cols - total_allocated
            filter_allocation_matrix[source_index[0], source_index[1]] += surplus

        return filter_allocation_matrix

    def _latency(self, c1, c2):
        """ Calculate latency based on coordinates. """
        hops = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1])
        return hops * self.latency_per_hop

    def _greedy(self, occupancy_m, N, destination_list, ii, src, src_list):
        h, w = occupancy_m.shape
        N_left = N    
        comm_latency_m = np.zeros((h, w))

        for i in range(h):
            for j in range(w):
                comm_latency = 0
                for dest in destination_list:
                    if src and (dest == src):
                        comm_latency += self.src_weightage * self._latency((i, j), dest)
                    else:
                        comm_latency += self._latency((i, j), dest)
                comm_latency_m[i][j] = comm_latency

        while N_left:
            best_latency = float('inf')
            equal_list = []
            for i in range(h):
                for j in range(w):
                    if occupancy_m[i][j] == 0 and comm_latency_m[i][j] < best_latency:
                        best_latency = comm_latency_m[i][j]
                        best_coord = (i, j)
                        equal_list = [(i, j)]
                    elif occupancy_m[i][j] == 0 and comm_latency_m[i][j] == best_latency:
                        equal_list.append((i, j))

            if src and len(equal_list) > 1:
                best_latency = float('inf')
                for chip in equal_list:
                    src_latency = self._latency(chip, src)
                    if src_latency < best_latency:
                        best_latency = src_latency
                        best_coord = chip
            occupancy_m[best_coord[0]][best_coord[1]] = ii
            N_left -= 1
        return occupancy_m
   

    def set_memory_dependency(self):
        for row in range(self.chiplet_sys.num_input_part):
            for col in range(self.chiplet_sys.num_filter_part):
                #print("code entering here")
                dep_coordinate = self.dependency_matrix[row][col]

                if(dep_coordinate[0] == -1 and dep_coordinate[1] == -1):
                    pass
                else:
                    self.chiplet_sys.chiplet_matrix[row][col].scratch_pad.set_ifmap_backing_buffer( self.chiplet_sys.chiplet_matrix[dep_coordinate[0]][dep_coordinate[1]].scratch_pad.ifmap_buf)
            
        

    def run_chiplet(self):
        bandwidth_mode = self.config_obj.get_bandwidth_use_mode()
        per_core_ifmap_buf_size, per_core_fitler_buf_size, per_core_ofmap_buf_size \
            = ([i * 1024 for i in self.config_obj.get_per_unit_sram_sizes_kb()])

        per_core_ifmap_bw, per_core_filter_bw, per_core_ofmap_bw\
            = self.config_obj.get_interface_bandwidths()
       
        chiplet_node = self.chiplet_sys.chiplet_matrix[self.ready_to_run[0][0]][self.ready_to_run[0][1]]
        # print("Chiplet being Run: ", self.ready_to_run[0][0], self.ready_to_run[0][1])
        nop_latency = self.comm_latency_matrix[self.ready_to_run[0][0]][self.ready_to_run[0][1]]

        chiplet_node.scratch_pad.set_params(verbose=self.verbose,
                                 estimate_bandwidth_mode=bandwidth_mode,
                                 ifmap_buf_size_bytes=per_core_ifmap_buf_size,
                                 filter_buf_size_bytes=per_core_fitler_buf_size,
                                 ofmap_buf_size_bytes=per_core_ofmap_buf_size,
                                 ifmap_backing_buf_bw=per_core_ifmap_bw,
                                 filter_backing_buf_bw=per_core_filter_bw,
                                 ofmap_backing_buf_bw=per_core_ofmap_bw
                                 )

        this_node_ifmap_demand_mat, this_node_filter_demand_mat, this_node_ofmap_demand_mat \
            = chiplet_node.compute_node.get_demand_matrices()

        this_node_ifmap_fetch_mat, this_node_filter_fetch_mat = chiplet_node.compute_node.get_prefetch_matrices()
        if (self.config_obj.get_bandwidth_use_mode()=="USER"):
            chiplet_node.scratch_pad.set_read_buf_prefetch_matrices(ifmap_prefetch_mat=this_node_ifmap_fetch_mat,
                                                     filter_prefetch_mat=this_node_filter_fetch_mat
                                                     )
        temp = chiplet_node.scratch_pad.service_memory_requests(this_node_ifmap_demand_mat,
                                             this_node_filter_demand_mat,
                                             this_node_ofmap_demand_mat,
                                             nop_latency)
        
        self.end_latency_matrix[self.ready_to_run[0][0]][self.ready_to_run[0][1]] \
            = self.comm_latency_matrix[self.ready_to_run[0][0]][self.ready_to_run[0][1]] + this_node_ofmap_demand_mat.shape[0]


    def run_sys(self):
        while len(self.ready_to_run):
            #pass the latency of the chiplet to run _chiplet (to account for traces start time)
            self.run_chiplet()
            present_chiplet = self.ready_to_run.popleft()
            self.status_matrix[present_chiplet[0]][present_chiplet[1]][1] = 1
    
            #update the ready_to_run with new chiplets that are ready to run
            for i in range(len(self.dependency_matrix)):
                row = self.dependency_matrix[i]
                for j in range(len(row)):
                    ele = self.dependency_matrix[i][j]
                    if(ele == present_chiplet):
                        self.status_matrix[i][j][0] = 1
                    if(self.status_matrix[i][j] == [1,0]):
                        if(self.ifmap_size_matrix[i][j] != 0):
                            self.ready_to_run.append((i,j))
                        self.ready_to_run = deque(set(self.ready_to_run))
        print("Communication Latency Matrix")
        print(self.comm_latency_matrix)
        print("Max Communication Latency")
        print(np.max(self.comm_latency_matrix))
        print("End Latency Matrix")
        print(self.end_latency_matrix)

    def get_latency(self):
        completion_time = np.max(self.end_latency_matrix)
        return completion_time
    
    def get_ifmap_size_matrix(self):
        return self.ifmap_size_matrix
