from threading import Thread
import os

N = 3

RUN_LIST = [
	'tangram.sh --batch 1 --nodes 4 4 resnet50 -o results/b1_4x4_res.json',
	'tangram.sh --batch 1 --nodes 4 4 googlenet -o results/b1_4x4_goog.json',

	'tangram.sh --batch 1 --nodes 12 12 resnet50 -o results/b1_12x12_res.json',
	'tangram.sh --batch 1 --nodes 12 12 googlenet -o results/b1_12x12_goog.json',

	'tangram.sh --batch 8 --nodes 4 4 resnet50 -o results/b8_4x4_res.json',
	'tangram.sh --batch 8 --nodes 4 4 googlenet -o results/b8_4x4_goog.json',

	'tangram.sh --batch 64 --nodes 4 4 resnet50 -o results/b64_4x4_res.json',
	'tangram.sh --batch 64 --nodes 4 4 googlenet -o results/b64_4x4_goog.json',

	'tangram.sh --batch 8 --nodes 12 12 resnet50 -o results/b8_12x12_res.json',
	'tangram.sh --batch 8 --nodes 12 12 googlenet -o results/b8_12x12_goog.json',

	'tangram.sh --batch 64 --nodes 12 12 resnet50 -o results/b64_12x12_res.json',
	'tangram.sh --batch 64 --nodes 12 12 googlenet -o results/b64_12x12_goog.json',
]

# RUN_LIST.reverse()

THR_LIST = [Thread(target = os.system, args = (i,)) for i in RUN_LIST]

running_thr = set()

for _ in range(N):
	t = THR_LIST.pop()
	t.start()
	running_thr.add(t)

while THR_LIST:
	old_t = None
	while True:
		for t in running_thr:
			t.join(timeout=1)
			if not t.is_alive():
				old_t = t
				break
		else:
			continue
		running_thr.remove(old_t)
		break
	t = THR_LIST.pop()
	t.start()
	running_thr.add(t)

for t in running_thr:
	t.join()
