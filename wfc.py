import sys, random
from PIL import Image
from os import listdir, remove
from os.path import isfile, join

# RULES
DO_PROGRESS_TEXT = 1
DO_PROGRESS_IMAGES = False
USE_WRAPAROUND = False
RULE_TYPE = 0
# 0 = sockets w/ blacklist
# 1 = whitelist
# rulify.py makes type 1 lists
FRAMES_OUT_DIR = 'testout'

NORTH = 0
EAST  = 1
SOUTH = 2
WEST  = 3

VECTORS = ((0,-1),(1,0),(0,1),(-1,0))

def add_vec(v1, v2):
	return (v1[0] + v2[0], v1[1] + v2[1])

class Tile:
	def __init__(self, im, rul, weight, black):
		self.im = im
		self.rules = rul
		self.weight = weight
		self.blacklists = black

class Board:
	def __init__(self, w, h):
		self.w = w
		self.h = h
		self.tiles = [[[] for _ in range(w)] for _ in range(h)]
		self.tiles2 = self.copy_buffer(self.tiles)
		self.tiles3 = self.copy_buffer(self.tiles)

	def get_collapsed_count(self):
		ct = 0
		for til in self.get_tile_list():
			if len(til[0]) == 1:
				ct += 1
		return ct

	def copy_buffer(self, bf):
		temp = []
		for row in bf:
			temp.append(row.copy())
		return temp

	def backup_buffer(self):
#		self.tiles5 = self.copy_buffer(self.tiles4)
#		self.tiles4 = self.copy_buffer(self.tiles3)
		self.tiles3 = self.copy_buffer(self.tiles2)
		self.tiles2 = self.copy_buffer(self.tiles)

	def restore_buffer(self):
		self.tiles = self.tiles2
		self.tiles2 = self.tiles3
		self.tiles3 = [[[] for _ in range(self.w)] for _ in range(self.h)]
#		self.tiles3 = self.tiles4
#		self.tiles4 = self.tiles5
#		self.tiles5 = [[[] for _ in range(self.w)] for _ in range(self.h)]

	def get_ratio_done(self):
		ct = self.get_collapsed_count()
		return ct / (self.w * self.h)

	def get_tile_list(self):
		# retuns a list of tuples (tile_data, (x, y))
		lst = []
		for y in range(self.h):
			for x in range(self.h):
				lst.append((self[x,y], (x, y)))
		return lst

	def check_in_bounds(self, pos):
		if pos[0] < 0 or pos[1] < 0:
			return False
		if pos[0] >= self.w or pos[1] >= self.h:
			return False
		return True

	def level_wrap_pt(self, pos):
		new_pos = [pos[0], pos[1]]
		if pos[0] < 0:
			new_pos[0] = self.w - 1
		if pos[1] < 0:
			new_pos[1] = self.h - 1
		if pos[0] >= self.w:
			new_pos[0] = 0
		if pos[1] >= self.h:
			new_pos[1] = 0
		return tuple(new_pos)

	def test_tiles(self, t1, t2, t2i, direc, tiles):
		if RULE_TYPE == 0:
			return self.test_tiles_method0(t1, t2, t2i, direc, tiles)
		elif RULE_TYPE == 1:
			return self.test_tiles_method1(t1, t2, t2i, direc, tiles)
		return t2

	def test_tiles_method0(self, t1, t2, t2i, direc, tiles):
		from_direc = (direc + 2) % 4
		that_rules = tiles[t2[t2i]].rules
		for t1_t in t1:
			if (t2[t2i] in tiles[t1_t].blacklists[direc]) or t1_t in tiles[t2[t2i]].blacklists[from_direc]:
				t2[t2i] = None
				break
			this_rules = tiles[t1_t].rules
			if this_rules[direc] == that_rules[from_direc]:
				break
		else:
			t2[t2i] = None
		return t2

	def test_tiles_method1(self, t1, t2, t2i, direc, tiles):
		from_direc = (direc + 2) % 4
		that_rules = tiles[t2[t2i]].rules
		for t1_t in t1:
			if t1_t in that_rules[from_direc]:
				break
		else:
			t2[t2i] = None
		return t2

	def propogate(self, start_pos, tiles):
		queue = [start_pos]
		while len(queue) > 0:
			cur_pos = queue.pop(0)
			for direc in [0, 1, 2, 3]:
				new_pos = add_vec(cur_pos, VECTORS[direc])
				if USE_WRAPAROUND:
					new_pos = self.level_wrap_pt(new_pos)
				elif self.check_in_bounds(new_pos) == False:
					continue
				new_til = self[new_pos].copy()
				for i in range(len(new_til)):
					new_til = self.test_tiles(self[cur_pos], new_til, i, direc, tiles)
					if None in new_til:
						if not new_pos in queue:
							queue.append(new_pos)
					self[new_pos] = [k for k in new_til if k is not None]

	def is_finished(self):
		for til in self.get_tile_list():
			if len(til[0]) != 1:
				return False
		return True

	def get_low_entropy_tile(self):
		# get min entropy >= 2
		min_entropy = 999999
		min_e_list = []
		for y in range(self.h):
			for x in range(self.w):
				ll = len(self[x,y])
				if ll > 1 and ll < min_entropy:
					# new min entropy
					min_entropy = ll
					min_e_list = []
				if ll == min_entropy:
					min_e_list.append((x, y))
		return [(self[pos], pos) for pos in min_e_list]

	def __setitem__(self, ind, val):
		self.tiles[ind[1]][ind[0]] = val
	def __getitem__(self, ind):
		return self.tiles[ind[1]][ind[0]]

get_tile = lambda t,x,y,w,h: t.crop((x*w,y*h,x*w+w,y*h+h))

def load_tiles(tset, tw, th, rules):
	tset_w, tset_h = tset.size
	tset_ww = tset_w // tw
	tset_hh = tset_h // th
	tils = []
	for y in range(tset_hh):
		for x in range(tset_ww):
			t_i = y * tset_ww + x
			if t_i >= len(rules):
				continue
			tt = get_tile(tset, x, y, tw, th)
			tils.append(Tile(tt, rules[t_i][1:5], rules[t_i][0], rules[t_i][5:9]))
	return tils

rule_dict = {}
def parse_rules(rul):
	lins = rul.split('\n')
	typ, lins = lins[0], lins[1:]
	global RULE_TYPE
	if typ == 'socket':
		RULE_TYPE = 0
	elif typ == 'whitelist':
		RULE_TYPE = 1
	else:
		raise Exception('Invalid rule type "{}"'.format(typ))
	rules = []
	rule_i = 0
	total_weight = 0
	for l in lins:
		if l == '':
			continue
		if l[0] == ';':
			continue
		rul_lin = l.split(' ')
		cur_rules = []
		got_weight = False
		sockets_left = 4
		for r in rul_lin:
			if r == '':
				continue
			if got_weight:
				if RULE_TYPE == 0:
					if sockets_left == 0:
						# blacklist
						blklst = r.split('|')
						for b in blklst:
							act_blk = []
							if b == '':
								act_blk = []
							else:
								act_blk = [int(x) for x in b.split(',')]
							cur_rules.append(act_blk)
					else:
						if not r in rule_dict:
							rule_dict[r] = rule_i
							rule_i += 1
						cur_rules.append(rule_dict[r])
						sockets_left -= 1
				elif RULE_TYPE == 1:
					if r == '-':
						lst = []
					else:
						lst = [int(x) for x in r.split(',')]
					cur_rules.append(lst)
			else:
				cur_rules.append(int(r))
				total_weight += int(r)
				got_weight = True
		if len(cur_rules) == 5:
			cur_rules.append([])
			cur_rules.append([])
			cur_rules.append([])
			cur_rules.append([])
		rules.append(cur_rules)
	for k in rules:
		k[0] /= total_weight
	return rules

def do_wfc(tiles, board, baseboard=None):
	# initialize board
	if baseboard is None:
		for y in range(board.h):
			for x in range(board.w):
				board[x,y] = [i for i in range(len(tiles))]
		if DO_PROGRESS_TEXT >= 2: print('do first propogation')
		board.propogate((0, 0), tiles)
	else:
		for y in range(board.h):
			for x in range(board.w):
				board[x,y] = baseboard[y][x]
		for y in range(board.h):
			for x in range(board.w):
				if DO_PROGRESS_TEXT >= 2: print('do first propogation at ({}, {})'.format(x, y))
				board.propogate((x, y), tiles)
	if DO_PROGRESS_IMAGES: make_board_image(tiles, board, 16, 16).save('testout/0.png')
	iii = 1
	lstpcnt = -1
	while not board.is_finished():
		# choose a random low entropy tile
		if DO_PROGRESS_TEXT >= 2: print('choose a random low entropy tile')
		collapsible_tiles = board.get_low_entropy_tile()
		if len(collapsible_tiles) == 0:
			board.restore_buffer()
			board.restore_buffer()
			print('ERROR')
			break
		rand_tile = random.choice(collapsible_tiles)
		# choose a random value for it
		if DO_PROGRESS_TEXT >= 2: print('choose a random value for it')
		tile_weights = [tiles[x].weight for x in rand_tile[0]]
		rand_coll = random.choices(population = rand_tile[0], weights = tile_weights)[0]
		# collapse that tile
		if DO_PROGRESS_TEXT >= 2: print('collapse that tile')
		board[rand_tile[1]] = [rand_coll]
		if DO_PROGRESS_IMAGES: make_board_image(tiles, board, 16, 16).save('testout/{}_1.png'.format(iii))
		# propogate changes
		if DO_PROGRESS_TEXT >= 2: print('propogate changes')
		board.propogate(rand_tile[1], tiles)
		board.backup_buffer()
		# debug output
		if DO_PROGRESS_IMAGES: make_board_image(tiles, board, 16, 16).save('testout/{}_2.png'.format(iii))
		iii += 1
		if DO_PROGRESS_TEXT >= 1:
			chkpcnt = int(board.get_ratio_done() * 100)
			if chkpcnt > lstpcnt:
				print(chkpcnt, '%')
				lstpcnt = chkpcnt

def make_board_image(tiles, board, tw, th):
	im = Image.new('RGB', (board.w * tw, board.h * th))
	for y in range(board.h):
		for x in range(board.w):
			cur_til = board[x,y]
			if len(cur_til) == 1:
				im.paste(tiles[cur_til[0]].im, (x * tw, y * th))
	return im

def load_base_board(fn):
	txt = open(fn).read()
	lins = txt.split('\n')
	dct = {}
	for gp in lins[0].split('|'):
		k, v = gp.split(':')
		val = []
		for vv in v.split(','):
			val.append(int(vv))
		dct[k] = val
	arr = []
	for y,l in enumerate(lins[1:]):
		cur_lin = []
		for x,c in enumerate(l):
			cur_lin.append(dct[c])
		arr.append(cur_lin)
	return arr

if __name__ == '__main__':
	if len(sys.argv) not in (8, 9):
		print('usage: python {} tileset tilewidth tileheight ruleset output outputwidth outputheight [baseboard]'.format(sys.argv[0]))
		quit()

	if DO_PROGRESS_IMAGES:
		filelist = [f for f in listdir(FRAMES_OUT_DIR) if isfile(join(FRAMES_OUT_DIR, f))]
		for f in filelist:
			remove(FRAMES_OUT_DIR + '/' + f)

	tileset = Image.open(sys.argv[1])
	tile_w = int(sys.argv[2])
	tile_h = int(sys.argv[3])
	ruleset = parse_rules(open(sys.argv[4]).read())
	tilelist = load_tiles(tileset, tile_w, tile_h, ruleset)
	board_w = int(sys.argv[6])
	board_h = int(sys.argv[7])
	tileboard = Board(board_w, board_h)
	if len(sys.argv) == 9:
		baseboard = load_base_board(sys.argv[8])
	else:
		baseboard = None

	do_wfc(tilelist, tileboard, baseboard)

	img = make_board_image(tilelist, tileboard, tile_w, tile_h)
	img.save(sys.argv[5])
