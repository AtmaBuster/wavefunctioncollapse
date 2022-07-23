from PIL import Image
import sys

def cmpim(im1, im2):
	# check hash, if different, not same
	if im1[1] != im2[1]:
		return False
	# hash is same, check pixel
	px1 = [p for p in im1[0].getdata()]
	px2 = [p for p in im2[0].getdata()]
	for c1, c2 in zip(px1, px2):
		if c1 != c2:
			return False
	return True

def get_image_hash(im):
	im.resize((8, 8))
	im = im.convert('L')
	pxl = list(im.getdata())
	av = sum(pxl) / len(pxl)
	bts = ''.join(['1' if (px >= av) else '0' for px in pxl])
	return int(bts,2)

def image_to_tiles(im, tw, th):
	# convert im into a list of tuples of (tw x th pixel tile, tile hash)
	tils = []
	im_w, im_h = im.size
	im_wt = im_w // tw
	im_ht = im_h // th
	for y in range(im_ht):
		for x in range(im_wt):
			til = im.crop((x*tw,y*th,x*tw+tw,y*th+th))
			tils.append((til, get_image_hash(til)))
	return tils

def tile_in_list(lst, til):
	for i,t in enumerate(lst):
		if cmpim(t, til):
			return i
	return -1

def get_unique_tiles(tilelist):
	# copies tilelist but without any duplicate tiles
	lst = []
	for t in tilelist:
		if tile_in_list(lst, t) == -1:
			lst.append(t)
	return lst

def make_tilemap(img, tiles):
	mapdata = []
	tw, th = tiles[0][0].size
	mw, mh = img.size
	mw //= tw
	mh //= th
	for y in range(mh):
		row = []
		for x in range(mw):
			til = img.crop((x*tw,y*th,x*tw+tw,y*th+th))
			cur = (til, get_image_hash(til))
			k = tile_in_list(tiles, cur)
			assert k != -1
			row.append(k)
		mapdata.append(row)
	return mapdata

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

def make_ruleset(tilemaps):
	lins = []
	cts = {}
	rules = {}
	for i,tmap in enumerate(tilemaps):
		print('getting rules for tilemap {}...'.format(i))
		maph = len(tmap)
		mapw = len(tmap[0])
		chkin = lambda x,y: ((x>=0)&(y>=0)&(x<mapw)&(y<maph))

		maxtil = -1
		for y in range(maph):
			for x in range(mapw):
				tt = tmap[y][x]
				if tt > maxtil:
					maxtil = tt
				if not tt in cts.keys():
					cts[tt] = 0
				cts[tt] += 1
				if chkin(x  ,y-1): add_rule(tmap, rules, x, y, 0)
				if chkin(x+1,y  ): add_rule(tmap, rules, x, y, 1)
				if chkin(x  ,y+1): add_rule(tmap, rules, x, y, 2)
				if chkin(x-1,y  ): add_rule(tmap, rules, x, y, 3)

	for i in range(maxtil + 1):
		currul = rules[i]
		curwgt = cts[i]
		rulparts = []
		for k in currul:
			if len(k) == 0:
				rulparts.append('-')
			else:
				rulparts.append(','.join([str(x) for x in k]))
		lins.append('{} {}'.format(curwgt, ' '.join(rulparts)))

	return '\n'.join(lins)

def get_nearest_factors(x):
	strt = int(x ** 0.5)
	while True:
		if x % strt == 0:
			return (strt, x // strt)
		strt -= 1

def make_tileset(lst):
	while True:
		setw, seth = get_nearest_factors(len(lst))
		if setw < 4:
			lst.append((Image.new('RGB', lst[0][0].size), 0))
		else:
			break
	tilw, tilh = lst[0][0].size
	im = Image.new('RGB', (tilw * setw, tilh * seth))
	for y in range(seth):
		for x in range(setw):
			tili = y * setw + x
			im.paste(lst[tili][0], (x * tilw, y * tilh))
	return im

if __name__ == '__main__':
	if len(sys.argv) < 5:
		print('usage: python {} outfiles tilewidth tileheight imgin...'.format(sys.argv[0]))
		exit()
	# get arguments
	img_fil_list = sys.argv[4:]
	tw = int(sys.argv[2])
	th = int(sys.argv[3])

	tilemaps = []
	tilelist = []
	for img_fn in img_fil_list:
		print('processing image "{}"...'.format(img_fn))
		img_in = Image.open(img_fn)
		# get current map tiles
		cur_tils = image_to_tiles(img_in, tw, th)
		# add to list and strip duplicates
		tilelist += cur_tils
		tilelist = get_unique_tiles(tilelist)
		# turn current map into tilemap
		tilemaps.append(make_tilemap(img_in, tilelist))
	# make rules based off of tilemaps
	print('making rules...')
	rules = make_ruleset(tilemaps)
	open(sys.argv[1] + '.txt', 'w').write(rules)
	# make tileset image
	print('making tileset image...')
	img_out = make_tileset(tilelist)
	img_out.save(sys.argv[1] + '.png')
