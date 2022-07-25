import argparse, random, struct

def add_vec(v1, v2):
	return (v1[0] + v2[0], v1[1] + v2[1])

class Board:
	def __init__(self, w, h):
		self.w = w
		self.h = h
		self.tiles = [[[] for _ in range(w)] for _ in range(h)]

	def wrap_point(self, pos):
		new_pos = [pos[0], pos[1]]
		if new_pos[0] < 0:
			new_pos[0] = self.w - 1
		if new_pos[1] < 0:
			new_pos[1] = self.h - 1
		if new_pos[0] >= self.w:
			new_pos[0] = 0
		if new_pos[1] >= self.h:
			new_pos[1] = 0
		return tuple(new_pos)

	def check_oob(self, pos):
		return pos[0] < 0 or pos[1] < 0 or pos[0] >= self.w or pos[1] >= self.h

	def propogate(self, start_loc, rules, wrap):
		queue = [start_loc]
		while len(queue) > 0:
			cur_pos = queue.pop()
			cur_til = self[cur_pos]
			for direc in [0,1,2,3]:
				new_pos = add_vec(cur_pos, ((0,-1),(1,0),(0,1),(-1,0))[direc])
				if wrap:
					new_pos = self.wrap_point(new_pos)
				elif self.check_oob(new_pos):
					continue
				new_til = self[new_pos].copy()
				for i in range(len(new_til)):
					for t0 in cur_til:
						thisrule = rules[t0][direc+1]
						if thisrule[new_til[i]]:
							break
					else:
						new_til[i] = None
				if None in new_til:
					if not new_pos in queue:
						queue.append(new_pos)
				self[new_pos] = [k for k in new_til if k is not None]

	def do_first_propogation(self, rules, wrap):
		if wrap:
			self.propogate((0, 0), rules, wrap)
			return
		if self.w == 1:
			xvals = [0]
		elif self.w == 2:
			xvals = [0, 1]
		else:
			xvals = [1]
		if self.h == 1:
			yvals = [0]
		elif self.h == 2:
			yvals = [0, 1]
		else:
			yvals = [1]
		for y in yvals:
			for x in xvals:
				self.propogate((x, y), rules, wrap)

	def done_tiles(self):
		ct = 0
		for y in range(self.h):
			for x in range(self.w):
				if len(self[x,y]) == 1:
					ct += 1
		return ct

	def get_low_entropy_tile(self):
		min_entropy = 999999
		min_e_list = []
		for y in range(self.h):
			for x in range(self.w):
				ll = len(self[x,y])
				if ll > 1 and ll < min_entropy:
					min_entropy = ll
					min_e_list = []
				if ll == min_entropy:
					min_e_list.append((x, y))
		return min_e_list

	def to_bin(self):
		b = b''
		for y in range(self.h):
			for x in range(self.w):
				t = self[x,y]
				if len(t) == 1:
					b += struct.pack('I', t[0])
				else:
					b += b'\xff\xff\xff\xff'
		return b

	def __getitem__(self, ind):
		return self.tiles[ind[1]][ind[0]]
	def __setitem__(self, ind, val):
		self.tiles[ind[1]][ind[0]] = val
	def __str__(self):
		return str(self.tiles)

class Bitfield:
	def __init__(self):
		self.num = 0
	def __getitem__(self, ind):
		return bool(self.num & (1 << ind))
	def __setitem__(self, ind, val):
		if isinstance(val, int):
			if val != 0 and val != 1:
				raise ValueError
		elif not isinstance(val, bool):
			raise ValueError
		self.num |= (1 << ind)

def parse_rules(fn):
	rul = open(fn).read()
	lins = rul.split('\n')
	rules = []
	rulei = 0
	totweight = 0
	for l in lins:
		if l == '' or l[0] == ';':
			continue
		rul_lin = [x for x in l.split(' ') if x]
		assert len(rul_lin) == 5
		wgt = int(int(rul_lin[0]))
		totweight += wgt
		cur_rules = [wgt]
		for r in rul_lin[1:]:
			fld = Bitfield()
			if r != '-':
				for i in [int(x) for x in r.split(',')]:
					fld[i] = 1
			cur_rules.append(fld)
		rules.append(cur_rules)
	return rules

def apply_wfc(board, rules, args):
	# init board
	for y in range(board.h):
		for x in range(board.w):
			board[x,y] = [i for i in range(len(rules))]
	# first propogation
	board.do_first_propogation(rules, args.wraplevel)
	# progress tracker
	lastpcnt = -1
	while board.done_tiles() < board.w * board.h:
		# choose a random low entropy tile
		collapsible_tiles = board.get_low_entropy_tile()
		if len(collapsible_tiles) == 0:
			print('ERROR')
			return
		rand_tile = random.choice(collapsible_tiles)
		rand_tile_data = board[rand_tile]
		# choose a random weighted value for it
		weights = [rules[x][0] for x in rand_tile_data]
		rand_coll = random.choices(rand_tile_data, weights)[0]
		# collapse the tile to that value
		board[rand_tile] = [rand_coll]
		# propogate changes
		board.propogate(rand_tile, rules, args.wraplevel)
		# progress tracker
		chkpcnt = int((board.done_tiles() / (board.w * board.h)) * 100)
		if chkpcnt > lastpcnt:
			print(chkpcnt, '%')
			lastpcnt = chkpcnt

def main(args):
	ruleset = parse_rules(args.ruleset)
	board = Board(args.outputwidth, args.outputheight)
	apply_wfc(board, ruleset, args)
	binboard = board.to_bin()
	open(args.output, 'wb').write(binboard)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Uses the wave function collapse algorithm to generate a random map')
	parser.add_argument('ruleset', type=str, help='ruleset file')
	parser.add_argument('output', type=str, help='output map file')
	parser.add_argument('outputwidth', type=int, help='output map width (in tiles)')
	parser.add_argument('outputheight', type=int, help='output map width (in tiles)')
	parser.add_argument('-r', '--repeat', action='store_true', help='repeat if error until success')
	parser.add_argument('-w', '--wraplevel', action='store_true', help='wrap level border')
	args = parser.parse_args()
	while True:
		if main(args) or args.repeat == False:
			break
