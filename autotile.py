import os
import random
import sys

from glob import glob
from PIL import Image

# frame size (after downscaling)
size = (180, 170)

xoff = 0
yoff = 3

frames = []
for filename in sorted(glob('frames/*.gif.*')):
    im = Image.open(filename)
    im = im.resize(size, Image.NEAREST)

    frames.append(im.crop((xoff, yoff, xoff + 8 * ((size[0] - xoff) // 8), yoff + 8 * ((size[1] - yoff) // 8))))

tiles = {}
tile_ims = {}
immutable = set()

for i, frame in enumerate(frames):
    w, h = frame.size

    for y in range(0, h, 8):
        for x in range(0, w, 8):
            tile = frame.crop((x, y, x + 8, y + 8))
            #tile.save('tiles/%04u.png' % len(tiles))
            t = tuple(tile.getdata())
            tiles[t] = tiles.get(t, 0) + 1
            tile_ims[t] = tile

            #if i == 0 and x == 8 * 8 and y <= 6 * 8:
            if x in [56, 64]:
                immutable.add(t)

            #if x == 0 and y == 64:
            #    print t

def entropy(t):
    # this just counts the number of distinct colors for now... quite pathetic

    c = {}
    for p in t:
        c[p] = c.get(p, 0) + 1

    # the fewer distinct colors, the harder this tile should be to collapse
    return 100 * (4 - len(c))

# try to reduce the number of tiles by collapsing the two most similar tiles into one

def delta(t1, t2):
    return sum(abs(x - y) for x, y in zip(t1, t2))

def dither(i, a, b):
    #return (a + b) // 2

    # https://en.wikipedia.org/wiki/Ordered_dithering
    matrix = [
         0, 48, 12, 60,  3, 51, 15, 63,
        32, 16, 44, 28, 35, 19, 47, 31,
         8, 56,  4, 52, 11, 59,  7, 55,
        40, 24, 36, 20, 43, 27, 39, 23,
         2, 50, 14, 62,  1, 49, 13, 61,
        34, 18, 46, 30, 33, 17, 45, 29,
        10, 58,  6, 54,  9, 57,  5, 53,
        42, 26, 38, 22, 41, 25, 37, 21,
    ]

    if a == b:
        return a

    a, b = sorted((a, b))
    if a + 2 == b:
        return a + 1

    if a + 3 == b:
        a = a + 1
        b = b - 1

    #if a + .5 < matrix[i] / 63.:
    #    return a
    #else:
    #    return b

    if random.random() < matrix[i] / 64.:
        return a
    else:
        return b

    # in the end, this looks better to me
    #return random.choice((a, b))

def collapse_similar(tiles):
    min_d = None

    #print immutable

    for i, (t1, n1, c1) in enumerate(tiles):
        if t1 in immutable:
            continue

        for ioff, (t2, n2, c2) in enumerate(tiles[i + 1:]):
            if t2 in immutable:
                continue

            #if t1 in immutable and t2 in immutable:
            #    continue

            j = i + ioff + 1
            d = (n1 + n2) * (delta(t1, t2) + c1 + c2)
            if min_d is None or d < min_d:
                min_d = d
                min_i = i
                min_j = j

    # remove the larger index first so the first remains valid
    assert min_i < min_j, (min_i, min_j)
    t2, n2, c2 = tiles.pop(min_j)
    t1, n1, c1 = tiles.pop(min_i)
    print min_d, n1, n2, c1, c2

    # pick the one with fewer modifications, if possible
    if c1 < c2 or t1 in immutable:
        tiles.append((t1, n1 + n2, max(c1, c2) + 1))
        tile_ims[t2] = tile_ims[t1]
    elif c2 < c1 or t2 in immutable:
        tiles.append((t2, n1 + n2, max(c1, c2) + 1))
        tile_ims[t1] = tile_ims[t2]
    else:
        #t3 = tuple((x + y) // 2 for x, y in zip(t1, t2))
        t3 = tuple(dither(i, x, y) for i, (x, y) in enumerate(zip(t1, t2)))
        print t3
        im = tile_ims[t1].copy()
        im.putdata(list(t3))
        tile_ims[t3] = im

        #t3 = random.choice((t1, t2))
        #if sum(t1) < sum(t2):
        #    t3 = t2
        #else:
        #    t3 = t1

        tiles.append((t3, n1 + n2, max(c1, c2) + 1))
        tile_ims[t1] = tile_ims[t3]
        tile_ims[t2] = tile_ims[t3]

    return tiles

tiles = [(t, n, entropy(t)) for t, n in tiles.iteritems()]

while len(tiles) > 256:
    tiles = collapse_similar(tiles)
    print len(tiles)

# output the tile data in gameboy format
# http://www.huderlem.com/demos/gameboy2bpp.html
tilenos = {}
with open('tiles.asm', 'w') as f:
    for i, (t, n, c) in enumerate(tiles):
        tilenos[t] = i

        print >>f, "; tile %u" % (i, )

        for j in range(8):
            low  = sum(((t[8 * j + k] & 1) >> 0) << k for k in range(8))
            high = sum(((t[8 * j + k] & 2) >> 1) << k for k in range(8))
            print >>f, "db $%02x, $%02x" % (low, high)

        print >>f

print len(tilenos)

#for t, n, c in tiles:
#    assert t in tilenos

#for t, im in tile_ims.iteritems():
#    assert t in tilenos

maps = []
for i, frame in enumerate(frames):
    w, h = frame.size

    map = []
    for y in range(0, h, 8):
        for x in range(0, w, 8):
            tile = frame.crop((x, y, x + 8, y + 8))
            t = tuple(tile.getdata())

            while True:
                tile = tile_ims[t]
                t2 = tuple(tile.getdata())
                if t2 == t:
                    break

                t = t2

            frame.paste(tile, (x, y))

            if t in tilenos:
                map.append(tilenos[t])
            else:
                print "warning: %r not in tilenos" % (t, )

    frame.save('output/%04u.gif' % i)
    maps.append(map)

# print out frame 0 as the initial map
with open('maps.asm', 'w') as f:
    print >>f, "frame_init:"

    for tileno in maps[0]:
        print >>f, "db $%02x" % (tileno, )

    print >>f

    for i, (prev, map) in enumerate(zip(maps, maps[1:] + maps[:1])):
        print >>f, "frame%u:" % (i, )

        for j, (tileno0, tileno1) in enumerate(zip(prev, map)):
            if tileno0 != tileno1:
                print >>f, "dw $%02x" % (j, )
                print >>f, "db $%02x" % (tileno1, )

        print >>f
