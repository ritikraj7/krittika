#! /usr/bin/python3

import re
import os
import sys

RES = 'results'
#RUN = 'running'

'''
MAPPER = [
	'polar', 'eyeriss'
]

NETWORK = [
	'darknet19',
	'vgg19',
	'resnet50',
	'googlenet',
	'resnet101',
	'densenet',
	'incep_resnet',
	'gnmt',
	'lstm',
	'zfnet',
]
'''

BEST_HEADS = (4, 3)

ST_HEADS = (
	'BASE',
	'LP-SA',
	'LS-SA',
	'SA-BASE',
	'SA-min',
)

TOP_SEG = 20

HEADERS = [
	'suffix',
	'param',
	'mapper',
	'net',
	'scale',
	'batch',
	'cost',
	'method',
	'tot_energy',
	'tot_cycle',
	'tot_cost',
	'impr_energy',
	'impr_cycle',
	'impr_cost',
	'ubuf_energy',
	'buffer_energy',
	'bus_energy',
	'mac_energy',
	'noc_energy',
	'dram_energy',
	'max_depth',
	'leaf_avg_depth',
	'avg_depth',
	'max_elapsed',
	'valid %',
	'accept %',
]

COST_F = {
	-1 : 'e' ,
	 0 : 'd' ,
	 1 : 'ed',
}

def cost_f(c):
	c = int(c)
	if c in COST_F:
		return COST_F[c]
	if c > 0:
		return 'e^{}d'.format(c)
	return 'ed^{}'.format(-c)

num_str = r'(?:(?:\d(?:\.\d+)?(?:e[+-]\d+)?)|\d+(?:\.\d+)?)'

re_str = (r''
r'(?P<method>_METHOD_): '
r'E:(?P<tot_energy>{ns}), T:(?P<tot_cycle>{ns}), Cost:(?P<tot_cost>{ns}), '
r'Ubuf/Buf/Bus/Mac/NoC/DRAM:'
r'(?P<ubuf_energy>{ns})/'
r'(?P<buffer_energy>{ns})/'
r'(?P<bus_energy>{ns})/'
r'(?P<mac_energy>{ns})/'
r'(?P<noc_energy>{ns})/'
r'(?P<dram_energy>{ns})'
).replace('_METHOD_', '|'.join(ST_HEADS))

detail_str = (r''
r'(?P<tab>\s+)(?P<head_info>.*) '
r'E:(?P<e>{ns}), T:(?P<t>{ns}), Cost:(?P<cost>{ns}) '
r'Ubuf/Buf/Bus/Mac:'
r'(?P<ubuf>{ns})/'
r'(?P<buf>{ns})/'
r'(?P<bus>{ns})/'
r'(?P<mac>{ns}) '
r'NoC\(hops=(?P<tot_hops>{ns}), DRAM acc=(?P<dram_acc>{ns})\) '
r'Buffer\(max=(?P<buf_max>{ns}), avg=(?P<buf_avg>{ns})\) '
r'Buffer\(max=(?P<wgt_max>{ns}), avg=(?P<wgt_avg>{ns})\) '
r'Buffer\(max=(?P<ifm_max>{ns}), avg=(?P<ifm_avg>{ns})\) '
r'(?:(?P<ifm_size>{ns})/(?P<wgt_size>{ns})/(?P<ofm_size>{ns}) )?'
r'Max NoC: (?P<link_max>{ns})'
)

layer_str = r'(?P<layer>\S.*?) (?P<batch>\d+) \((?P<partition>[BKHW:\d, ]+)\) util:(?P<util>{ns})/(?P<tot_util>{ns})'
cut_str = r'(?P<cut_type>[ST]) (?P<tot_batch>\d+)/(?P<num_bgrp>\d+)'

header_str = r'Mapper (?P<mapper>\S+) Network (?P<net>\S+) Mesh (?P<scale>\d+)\*(?P<scale_y>\d+) Batch (?P<batch>\d+)'

sa_str = r'Elapsed: (?P<elapsed>\d+)s Valid: \d+ \((?P<valid>{ns})%\) Accept: \d+ \((?P<accept>{ns})%\)'

re_str = re_str.format(ns = num_str)
detail_str = detail_str.format(ns = num_str)
layer_str = layer_str.format(ns = num_str)
sa_str = sa_str.format(ns = num_str)


def avg(l):
	if l:
		return sum(l) / len(l)
	return float('nan')

def str_div(a, b):
	return str(float(a) / float(b))

def analysis(f, fname, c, suffix):
	nmethod = 0
	read_tree = False
	struct_line = False
	info_dict = {'cost' : c, 'suffix': suffix, 'param': ''}
	it = suffix.rfind('_')
	if it != -1:
		info_dict['suffix'] = suffix[:it]
		info_dict['param'] = suffix[it+1:]

	depth_list = []
	leaf_depth_list = []

	tot_elapsed = []
	valid_list = []
	accept_list = []
	root_type = None

	curCosts = {}
	with open(fname, 'r', encoding = 'utf-8') as g:
		for line in g.readlines():
			line = line.rstrip()
			if any(line.startswith(_i) for _i in ST_HEADS):
				match = re.fullmatch(re_str, line)
				assert match is not None, 'Cannot match "{}" with "{}" in "{}"'.format(line, re_str, fname)
				method = match['method']
				assert method not in curCosts, 'Find schemes with same name "{}" in "{}"'.format(method, fname)
				curCosts[method] = (match['tot_energy'], match['tot_cycle'], match['tot_cost'])

	minCost = None
	for i in BEST_HEADS:
		method = ST_HEADS[i]
		if method in curCosts:
			minCost = curCosts[method]
			break

	with open(fname, 'r', encoding = 'utf-8') as g:
		for line in g.readlines():
			line = line.rstrip()
			assert not line.startswith('[Error]'), "Error detected in {}".format(fname)
			if line.startswith('Warning'):
				assert False, "Warning detected in {}".format(fname)

			# Check for header:
			match = re.fullmatch(header_str, line)
			if match is not None:
				info_dict.update(match.groupdict())
				continue

			# Check for tree start:
			if any(line.startswith(_i) for _i in ST_HEADS):
				match = re.fullmatch(re_str, line)
				assert match is not None, 'Cannot match "{}" with "{}" in "{}"'.format(line, re_str, fname)
				assert 'mapper' in info_dict is not None, 'No header found for "{}"'.format(fname)
				assert not read_tree, 'Start of a new tree while reading old tree at "{}" in "{}"'.format(line, fname)

				cur_dict = info_dict.copy()
				cur_dict.update(match.groupdict())
				cur_dict['impr_energy'] = ''
				cur_dict['impr_cycle'] = ''
				cur_dict['impr_cost'] = ''
				if minCost is not None:
					cur_dict['impr_energy'] = str_div(cur_dict['tot_energy'], minCost[0])
					cur_dict['impr_cycle'] = str_div(cur_dict['tot_cycle'], minCost[1])
					cur_dict['impr_cost'] = str_div(cur_dict['tot_cost'], minCost[2])
				f.write(','.join(cur_dict[key] for key in HEADERS[:TOP_SEG]))
				nmethod += 1
				read_tree = True
				struct_line = False
				depth_list = []
				leaf_depth_list = []
				root_type = None
				continue

			# Check for tree:
			if read_tree:
				# First line
				if not struct_line:
					assert line == 'Struct:', 'Missing struct line at "{}" in "{}"'.format(line, fname)
					struct_line = True
					continue

				match = re.fullmatch(detail_str, line)
				if match is None:
					# End of tree
					read_tree = False

					assert leaf_depth_list, fname + '\n' + line
					max_d = max(depth_list)
					avg_d = avg(depth_list)
					avg_ld = avg(leaf_depth_list)
					f.write(',{},{},{}'.format(max_d, avg_ld, avg_d))
					valid_d = 0
					accept_d = 0
					if valid_list:
						valid_d = avg(valid_list)
						accept_d = avg(accept_list)
					max_elapsed = 0
					if tot_elapsed:
						max_elapsed = max(tot_elapsed)
					f.write(',{},{},{}'.format(max_elapsed, valid_d, accept_d))
					tot_elapsed = []
					valid_list = []
					accept_list = []
					f.write('\n')
				else:
					# Middle of tree
					lmatch = re.fullmatch(layer_str, match['head_info'])
					cmatch = re.fullmatch(cut_str, match['head_info'])
					assert cmatch is not None or lmatch is not None, \
						'"{}" cannot match both layer and cut in "{}"'.format(match['head_info'], fname)

					depth = len(match['tab']) - 1
					is_root = (depth == 0)
					# -1:L, 0:S, 1:T
					ltype = int(cmatch['cut_type'] == 'T') if lmatch is None else -1

					if is_root:
						assert root_type is None, 'Multiple root detected in "{}"'.format(fname)
						root_type = ltype
					else:
						assert root_type is not None, 'Root is missing in "{}"'.format(fname)

					# is_seg = (is_root and ltype != 1) or (depth == 1 and root_type == 1)

					if not is_root:
						depth_list.append(depth)
						if ltype == -1:
							leaf_depth_list.append(depth)

				continue

			# Check for SA info:
			match = re.fullmatch(sa_str, line)
			if match is not None:
				tot_elapsed.append(int(match['elapsed']))
				valid_list.append(float(match['valid']))
				accept_list.append(float(match['accept']))


		if read_tree:
			assert leaf_depth_list, fname + '\n' + line
			max_d = max(depth_list)
			avg_d = avg(depth_list)
			avg_ld = avg(leaf_depth_list)
			f.write(',{},{},{}'.format(max_d, avg_ld, avg_d))
			valid_d = 0
			accept_d = 0
			if valid_list:
				valid_d = avg(valid_list)
				accept_d = avg(accept_list)
			max_elapsed = 0
			if tot_elapsed:
				max_elapsed = max(tot_elapsed)
			f.write(',{},{},{}'.format(max_elapsed, valid_d, accept_d))
			f.write('\n')

	return nmethod

def main(l):
	with open('results.csv', 'w', encoding='utf-8') as f:
		print(','.join(HEADERS), file = f)
		partial_list = []
		for folder, i in l:
			if not i.endswith('.txt'):
				continue
			'''
			res = re.fullmatch(r'(\d+)_(\d+)_(\d+)_(\d+)_(-?\d+)(?:_([a-zA-Z][a-zA-Z0-9_.]*))?\.txt', i)
			if res is None:
				continue

			m,n,b,s = [int(_i) for _i in [res[1], res[2], res[3], res[4]]]
			m=MAPPER[m]
			n=NETWORK[n]
			c = cost_f(res[5])
			suffix = res[6]
			if suffix is None:
				suffix = ''
			'''
			c = cost_f(1)
			suffix = 'tangram'
			whole_i = os.path.join(folder, i)
			nmethod = analysis(f, whole_i, c, suffix)
			tot_method = 2
			if nmethod < tot_method:
				if folder == RES:
					print('Warning: "{}" not completed ({}/{}).'.format(whole_i, nmethod, tot_method))
				else:
					partial_list.append((nmethod, i))
		partial_list.sort()
		for nmethod, fname in partial_list:
			print(nmethod, fname)

if __name__ == '__main__':
	l = [(RES, i) for i in os.listdir(RES)]
	'''
	if len(sys.argv) >= 2 and sys.argv[1] == 'all':
		l += [(RUN, i) for i in os.listdir(RUN)]
	'''
	main(l)
