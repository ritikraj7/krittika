import json
import os

import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../..'))

from nn_dataflow.core import Option, LoopBlockingScheme
from nn_dataflow.core import PipelineSegmentTiming
from nn_dataflow.core.layer import ConvLayer, FCLayer
from nn_dataflow.nns import import_network
from nn_dataflow.core import loop_enum as le

from collections import OrderedDict

from copy import deepcopy


def get_elem(res, elem):
	if not res:
		return None
	if elem not in res:
		return None
	return res[elem]

elems = ['net', 'batch', 'size', 'utility', 'total_cost', 'total_time', 'total_op_cost', 'total_noc_cost', #'opt_loop_time', 
		 'total_access_cost', 'access_prop', 
		 #'cluster_hops', 'dram_hops', 'sram_hops', 'filter_hops', 'node_hops',  'sbuf_hops',
		 #'GOPS',
		 #'proc_util', 'total_util',
		 #'active_node_pes_avg', 'active_node_pes_max',
		 'elapsed', 'options', 'version']

out_name = 'data.csv'
f=open(out_name, 'w')

print(','.join(['']+elems)\
	.replace('access_prop','dram,other')\
	.replace('options','opt_goal,np')\
	.replace('opt_loop_time','opt_loop_time,opt_util')
	, file = f)

for root, _, files in os.walk('./results'):
	for file in files:
		if not file.endswith('.json'):
			continue
		print(root, file)
		g=open(os.path.join(root, file), 'r')
		try:
			res = json.load(g)
		except Exception as e:
			g.close()
			continue

		try:
			net = import_network(res['net'])
			options=Option(layer_parallel=res['options'].get('layer_parallel',False))
			#if not options.layer_parallel:
			#	print(net)
			#print(options.layer_parallel, res['options']['layer_parallel'])
			net = deepcopy(net)
			net.reformat(options)
			#print(net)
		except Exception as e:
			net = None

		string = file[:-5]
		for elem in elems:
			string += ','
			if elem == 'pref':
				first_ = file.find('_')
				if first_ == -1 or first_ + 5 > len(file):
					first_ = -5
				string += file[:first_]
				continue
			elif elem == 'size':
				string += str(res['resource']['proc_region'][-1])
			elif elem == 'opt_loop_time':
				sch = get_elem(res, 'schedules')
				try:
					batch_dict = dict()
					for v in sch.values():
						sq = v['sched_seq'][0]
						ord_loops = LoopBlockingScheme.ordered_loops(
							v['scheme']['tvals'][0], v['scheme']['orders'][0])
						# Top loop blocking factors.
						tb = 1
						if ord_loops and ord_loops[0][0] == le.BAT:
							tb = ord_loops.pop(0)[1]
						# Lazily update BAT group number.
						if sq not in batch_dict:
							batch_dict[sq] = tb
						elif batch_dict[sq] != tb:
							# Unmatched.
							batch_dict[sq] = 1

					cur_seq = [-1,0,0]
					ltl = []
					layer2idx = dict()
					lct = []
					ldt = []
					lnt = []
					lt = []
					cur_ndict = []
					ldd = []
					#print("batch_dict", batch_dict)
					for layer_name, v in sch.items():
						sq = v['sched_seq']
						ts_xb = 0
						td_xb = 0
						if sq[0] == cur_seq[0] + 1:
							assert sq[1] == 0 and sq[2] == 0
							mt = 0
							last_ndict = []
							for i, psum in enumerate(cur_ndict):
								mt = max(mt, ltl[-1][i][-1].td_xb + lct[-1] * (batch_dict[cur_seq[0]] - 1))
								last_ndict.append((psum,mt))
							#print(last_ndict, cur_ndict)
							#if lct:
							#	print("last crit time: %d, last batch_dict: %d" % (lct[-1], batch_dict[cur_seq[0]]))
							cur_ndict = []
							ltl.append([])
							lct.append(0)
							ldt.append(0)
							lnt.append(0)
							lt.append(0)
							ldd.append(dict())
							tot_num = 0
							cur_seq[0] = sq[0]
							cur_seq[1] = -1

						if sq[1] == cur_seq[1] + 1:
							assert sq[0] == cur_seq[0] and sq[2] == 0
							ltl[-1].append([])
							cur_seq[1] = sq[1]
							cur_seq[2] = 0
							tot_num += v['scheme']['num_nodes']
							cur_ndict.append(tot_num)
							for i,mt in last_ndict:
								if i >= tot_num:
									ts_xb = max(ts_xb, mt)
									break
							else:
								if last_ndict:
									ts_xb = max(ts_xb, last_ndict[-1][-1])

							#print("%d starts at %f, with total num %d" % (sq[1], ts_xb, tot_num))

						layer2idx[layer_name] = sq
						ofm_ngrp = v['scheme']['tofm']
						# Calculate timing.
						seg_idx, sp_idx, tm_idx = sq
						bat_ngrp = batch_dict[seg_idx]
						time = v['scheme']['time']
						for p in net.prevs(layer_name):
							if p not in layer2idx:
								# Off-chip source.
								continue
							# On-chip source.
							p_seg, p_sp_idx, p_tm_idx = layer2idx[p]
							p_timing = ltl[p_seg][p_sp_idx][p_tm_idx]
							if p_seg < seg_idx:
								# Circling!
								o_t = ts_xb
								ts_xb = max(ts_xb, p_timing.td_xb + \
									((batch_dict[p_seg]-1) // batch_dict[seg_idx]) \
									* lct[p_seg])
								#print("Start: %f -> %f" % (o_t,ts_xb))
								continue
							assert p_seg == seg_idx
							if p_sp_idx == sp_idx:
								assert p_tm_idx == tm_idx - 1
								# Same spatial scheduling.
								if p_timing.ngrp > 1: #not is_conv:
									# Fused.
									start = p_timing.ts_xb + p_timing.time / (p_timing.ngrp * bat_ngrp)
									# Also constrain the done time.
									o_d = td_xb
									td_xb = p_timing.td_xb + time / bat_ngrp
									#print("Done: %f -> %f" % (o_d,td_xb))
								else:
									# Not fused.
									start = p_timing.td_xb
							else:
								assert p_sp_idx < sp_idx
								assert p_tm_idx == len(ltl[p_seg][p_sp_idx]) - 1
								# Previous spatial scheduling.
								if p_timing.ngrp > 1: #(ifm_ngrp if is_conv else ofm_ngrp) == p_timing.ngrp:
									# I/OFM group forwarding.
									start = p_timing.ts_xb + p_timing.time / (p_timing.ngrp * bat_ngrp)
									td_xb = p_timing.td_xb + time / (bat_ngrp * p_timing.ngrp)
								else:
									# All I/OFM double buffering.
									start = p_timing.td_xb
							#print("Start: %f update with %f" % (ts_xb,start))
							ts_xb = max(ts_xb, start)
						td_xb = max(td_xb, ts_xb + time / bat_ngrp)
						#print("End: update with %f/%d" % (time,bat_ngrp))

						timing = PipelineSegmentTiming.LayerTiming(
							time=time, #node_time=0, dram_time=0,
							num_nodes=0, ngrp=ofm_ngrp, bat_ngrp=bat_ngrp, ts_xb=ts_xb, td_xb=td_xb)
						ltl[-1][-1].append(timing)

						critical_time = max(tlist[-1].td_xb - tlist[0].ts_xb
									 for tlist in ltl[-1])

						# DRAM time.
						# Each layer DRAM time is calculated using the layer accesses and the
						# maximum bandwidth. Accumulating the accesses is accumulating the
						# time.
						dram_dict=ldd[-1]
						for node, ntime in v['scheme']['dram_dict']:
							node = tuple(node)
							dram_dict[node] = dram_dict.get(node, 0) + ntime

						dram_time = max(dram_dict.values(), default = 0)
						node_time = max(tlist[-1].td_xb
											  + critical_time * (bat_ngrp - 1)
											 for tlist in ltl[-1])
						assert node_time >= critical_time
						lct[-1] = critical_time
						ldt[-1] = dram_time
						lnt[-1] = node_time
						lt[-1] = max(dram_time + ltl[-1][0][0].ts_xb, node_time)

					ans = lt[-1]
				except Exception as e:
					string += ','
					continue
				string += str(ans)
				string += ','
				op_cost = get_elem(res, 'total_op_cost')
				if op_cost is None:
					continue
				if isinstance(op_cost, list):
					op_cost = op_cost[0]
				time = lt[-1]
				pe_arr = get_elem(res, 'resource').get('dim_array',None)
				if pe_arr is None:
					continue
				pe_arr = pe_arr[0]*pe_arr[1]
				proc = get_elem(res, 'resource').get('proc_region',None)
				if proc is None:
					continue
				if isinstance(proc[0],list):
					proc = proc[0]
				proc_num = proc[0]*proc[1]
				if len(proc) == 3 and proc[2]:
					proc_num -= len(proc[2])
				ans = op_cost * 100 / (time * pe_arr * proc_num)
				string += str(ans)
				continue
			elif elem == 'utility':
				op_cost = get_elem(res, 'total_op_cost')
				if op_cost is None:
					continue
				if isinstance(op_cost, list):
					op_cost = op_cost[0]
				op_cost /= res['cost']['mac_op']
				time = get_elem(res, 'total_time')
				if time is None:
					continue
				pe_arr = get_elem(res, 'resource').get('dim_array',None)
				if pe_arr is None:
					continue
				pe_arr = pe_arr[0]*pe_arr[1]
				proc = get_elem(res, 'resource').get('proc_region',None)
				if proc is None:
					continue
				if isinstance(proc[0],list):
					proc = proc[0]
				proc_num = proc[0]*proc[1]
				if len(proc) == 3 and proc[2]:
					proc_num -= len(proc[2])
				ans = op_cost * 100 / (time * pe_arr * proc_num)
				string += str(ans)
				continue
			elif elem.endswith('_util'):
				if net == None:
					continue
				try:
					sch = get_elem(res, 'schedules')
					ntime_list = dict()
					op_list = dict()
					max_ptime = dict()
					for layer in sch:
						if not isinstance(net[layer],ConvLayer):
							continue
						l = sch[layer]
						idx = l['sched_seq'][0]
						ops = l['scheme']['ops']
						nodes = l['scheme']['num_nodes']
						proc_time = l['scheme']['proc_time']
						op_list[idx] = op_list.get(idx,0) + ops
						if elem == 'proc_util':
							ntime_list[idx] = ntime_list.get(idx,0) + proc_time * nodes
						else:
							ntime_list[idx] = ntime_list.get(idx,0) + nodes
							max_ptime[idx] = max(max_ptime.get(idx,0), proc_time)
					if elem != 'proc_util':
						for idx in ntime_list:
							ntime_list[idx] *= max_ptime[idx]
					nsum = sum(ntime_list.values())
					ans = sum(op_list.values()) / nsum if nsum != 0 else float('nan')
					string += str(ans)
				except Exception as e:
					pass
				continue
			ans = get_elem(res, elem)
			if ans is None:
				if elem == 'access_prop':
					dram_acc = res['total_accesses'][0]
					dram_cost = dram_acc * res['cost']['mem_hier'][0]
					other_cost = res['total_access_cost'] - dram_cost
					string += '{},{}'.format(dram_cost, other_cost)
					#string += ','*4
				continue
			if elem.startswith('active_node_pes'):
				ans = str(ans['total']) if 'total' in ans else ''
			elif elem == 'access_prop':
				total = get_elem(res, 'total_access_cost')
				if isinstance(total, list) and len(total) == 2:
					total = total[0]
				ans = ','.join([str(i*total) for i in ans[:2]])
			elif elem == 'options':
				ans = ','.join([str(ans['opt_goal']),str(ans['nprocesses'])])
			else:
				if isinstance(ans, list) and len(ans) == 2:
					ans = ans[0]
				ans = str(ans)
			string += ans
		print(string, file = f)
f.close()
os.system('start '+out_name)
