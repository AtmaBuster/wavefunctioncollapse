from PIL import Image
import argparse, struct

def image_to_tiles(im, tw, th):
	# convert im into a list of (tw x th pixel tile)s
	tils = []
	im_w, im_h = im.size
	im_wt = im_w // tw
	im_ht = im_h // th
	for y in range(im_ht):
		for x in range(im_wt):
			til = im.crop((x*tw,y*th,x*tw+tw,y*th+th))
			tils.append(til)
	return tils

def make_map(tiles, tilemap):
	w, h = len(tilemap[0]), len(tilemap)
	tw, th = tiles[0].size
	imout = Image.new('RGB', (tw * w, th * h))
	for y in range(h):
		for x in range(w):
			imout.paste(tiles[tilemap[y][x]], (x * tw, y * th))
	return imout

def main(args):
	tilelist = image_to_tiles(Image.open(args.tileset), args.tilewidth, args.tileheight)
	tilemap = []
	rawmap = open(args.tilemap, 'rb').read()
	mapheight = (len(rawmap) // 4) // args.mapwidth
	for y in range(mapheight):
		row = []
		for x in range(args.mapwidth):
			i = y * args.mapwidth + x
			tbin = rawmap[i*4:i*4+4]
			row.append(struct.unpack('I', tbin)[0])
		tilemap.append(row)
	mapim = make_map(tilelist, tilemap)
	mapim.save(args.mapout)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Make a map from a tileset and binary map data')
	parser.add_argument('tileset', type=str, help='tileset image')
	parser.add_argument('tilewidth', type=int, help='width of each tile')
	parser.add_argument('tileheight', type=int, help='height of each tile')
	parser.add_argument('tilemap', type=str, help='tilemap file')
	parser.add_argument('mapwidth', type=int, help='map width')
	parser.add_argument('mapout', type=str, help='map image output')
	args = parser.parse_args()
	main(args)
