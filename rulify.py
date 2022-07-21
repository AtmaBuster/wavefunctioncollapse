from PIL import Image
import sys

def get_nearest_factors(x):
	strt = int(x ** 0.5)
	while True:
		if x % strt == 0:
			return (strt, x // strt)
		strt -= 1

def img_compare(i1, i2):
	size1 = i1.size
	size2 = i2.size
	if size1 != size2:
		return False
	px1 = [p for p in i1.getdata()]
	px2 = [p for p in i2.getdata()]
	for c1, c2 in zip(px1, px2):
		if c1 != c2:
			return False
	return True

def image_in_list(l, im):
	for im_l in l:
		if img_compare(im_l, im):
			return True
	return False

def image_to_tiles(im, tw, th):
	imw, imh = im.size
	hct = imw // tw
	vct = imh // th
	l = []
	for y in range(vct):
		for x in range(hct):
			t = im.crop((x * tw, y * th, x * tw + tw, y * th + th))
			l.append(t)
	return l

def get_unique_tiles(lst):
	l_out = []
	for i,t in enumerate(lst):
		if not image_in_list(l_out, t):
			l_out.append(t)
#		if i % 16 == 0:
#			print(i / len(lst))
	return l_out

def make_empty_tile(l):
	return Image.new('RGB', l[0].size)

def make_tileset(lst):
	while True:
		setw, seth = get_nearest_factors(len(lst))
		if setw < 4:
			lst.append(make_empty_tile(lst))
		else:
			break
	tilw, tilh = lst[0].size
	im = Image.new('RGB', (tilw * setw, tilh * seth))
	for y in range(seth):
		for x in range(setw):
			tili = y * setw + x
			im.paste(lst[tili], (x * tilw, y * tilh))
	return im

def get_index(tile_list, tile):
	for i,t in enumerate(tile_list):
		if img_compare(t, tile):
			return i
	return -1

def make_tilemap(image, tiles):
	tw, th = tiles[0].size
	mp = []
	rows = image.size[1] // th
	cols = image.size[0] // tw
	for y in range(rows):
		cur_row = []
		for x in range(cols):
			cur_til = image.crop((x*tw, y*th, x*tw+tw, y*th+th))
			cur_row.append(get_index(tiles, cur_til))
		mp.append(cur_row)
	return mp

class Counter:
	def __init__(self):
		self.cts = {}
	def inc(self, i):
		if not i in self.cts.keys():
			self.cts[i] = 0
		self.cts[i] += 1
	def __getitem__(self, ind):
		return self.cts[ind]
	def __str__(self):
		return str(self.cts)

vec = ((0,-1),(1,0),(0,1),(-1,0))
def add_rule(tmap, ruls, x, y, direc):
	t = tmap[y][x]
	if not t in ruls.keys():
		ruls[t] = [[],[],[],[]]
	x2 = x + vec[direc][0]
	y2 = y + vec[direc][1]
	t2 = tmap[y2][x2]
	if not t2 in ruls[t][direc]:
		ruls[t][direc].append(t2)

def make_ruleset(tilemap_list):
	lins = []
	lins.append('whitelist')
	cts = Counter()
	ruls = {}
	for i,tilemap in enumerate(tilemap_list):
		print('getting rules for tilemap {}...'.format(i))
		maph = len(tilemap)
		mapw = len(tilemap[0])
		chkin = lambda x,y: ((x>=0)&(y>=0)&(x<mapw)&(y<maph))

		maxtil = -1
		for y in range(maph):
			for x in range(mapw):
				tt = tilemap[y][x]
				if tt > maxtil:
					maxtil = tt
				cts.inc(tt)
				if chkin(x  ,y-1): add_rule(tilemap, ruls, x, y, 0)
				if chkin(x+1,y  ): add_rule(tilemap, ruls, x, y, 1)
				if chkin(x  ,y+1): add_rule(tilemap, ruls, x, y, 2)
				if chkin(x-1,y  ): add_rule(tilemap, ruls, x, y, 3)

	for i in range(maxtil + 1):
		currul = ruls[i]
		curwgt = cts[i]
		rulparts = []
		for k in currul:
			if len(k) == 0:
				rulparts.append('-')
			else:
				rulparts.append(','.join([str(x) for x in k]))
		lins.append('{} {}'.format(curwgt, ' '.join(rulparts)))

	return '\n'.join(lins)

if __name__ == '__main__':
#pallet = Image.open(sys.argv[1])
#lst = image_to_tiles(pallet, 16, 16)
#lst = get_unique_tiles(lst)
#imout = make_tileset(lst)
#imout.save(sys.argv[2])
	if len(sys.argv) < 5:
		print('usage: python {} outfiles tilewidth tileheight imgin...'.format(sys.argv[0]))
		exit()
	img_list = sys.argv[4:]
	tw = int(sys.argv[2])
	th = int(sys.argv[3])
	tmaps = []
	tile_list = []
	for imfn in img_list:
		print('processing image "{}"...'.format(imfn))
		img_in = Image.open(imfn)
		cur_tils = image_to_tiles(img_in, tw, th)
		tile_list += cur_tils
		tile_list = get_unique_tiles(tile_list)
		tmaps.append(make_tilemap(img_in, tile_list))
	print('making rules...')
	rules = make_ruleset(tmaps)
	print('making tileset image...')
	img_out = make_tileset(tile_list)

	img_out.save(sys.argv[1] + '.png')
	open(sys.argv[1] + '.txt', 'w').write(rules)
