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

while len(tiles) > 384:
    tiles = collapse_similar(tiles)
    print len(tiles)

tilenos = {}
for i, (t, n, c) in enumerate(tiles):
    tilenos[t] = i

print len(tilenos)

# output the tile data in gameboy format
# http://www.huderlem.com/demos/gameboy2bpp.html
def write_tiles(bank):
    start = bank * 256
    end = bank * 256 + 256

    with open('tiles-%u.asm' % (bank, ), 'w') as f:
        print >>f, "; tile bank %u" % (bank, )
        print >>f, "tiles%u:" % (bank, )
        print >>f

        for i, (t, n, c) in enumerate(tiles[start:end]):
            print >>f, "; tile %u" % (i, )

            for j in range(8):
                low  = sum(((t[8 * j + k] & 1) >> 0) << (7 - k) for k in range(8))
                high = sum(((t[8 * j + k] & 2) >> 1) << (7 - k) for k in range(8))
                print >>f, "db $%02x, $%02x" % (low, high)

            print >>f

        print >>f, "tiles%u_end:" % (bank, )

for i in range((len(tiles) + 255) // 256):
    write_tiles(i)

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
            map.append(tilenos[t])

        for x in range(w, 32 * 8, 8):
            map.append(0)

    frame.save('output/%04u.gif' % i)
    maps.append(map)

# print out frame 0 as the initial map
with open('maps.asm', 'w') as f:
    print >>f, "; bank 0"
    print >>f, "frame_init_0:"
    for tileno in maps[0]:
        print >>f, "db $%02x" % (tileno & 255, )
    print >>f, "frame_init_0_end:"
    print >>f
    print >>f, "; bank 1"
    print >>f, "frame_init_1:"
    for tileno in maps[0]:
        print >>f, "db $%02x" % ((tileno > 255) << 3, )
    print >>f, "frame_init_1_end:"
    print >>f

    for i, (prev, map) in enumerate(zip(maps, maps[1:] + maps[:1])):
        print >>f, "frame%u:" % (i, )

        # find differences that need to be written in each bank
        bank0 = []
        bank1 = []
        for j, (tileno0, tileno1) in enumerate(zip(prev, map)):
            t0_lo = tileno0 & 255
            t1_lo = tileno1 & 255
            if t0_lo != t1_lo:
                bank0.append((j, t1_lo))

            t0_hi = (tileno0 > 256) << 3
            t1_hi = (tileno1 > 256) << 3
            if t0_hi != t1_hi:
                bank1.append((j, t1_hi))

        def write_bank(bank):
            print "frame %u has %u changes in bank" % (i, len(bank))

            prev_j = 0

            for j, val in bank:
                # TODO: this encoding doesn't handle a change in the top-left tile (index 0)...
                assert j - prev_j > 0
                assert j - prev_j < 256
                print >>f, "db $%02x, $%02x" % (j - prev_j, val)
                prev_j = j

            print >>f, "db 0"

        print >>f, "; bank 0"
        write_bank(bank0)
        print >>f, "; bank 1"
        write_bank(bank1)

        print >>f, "frame%u_end:" % (i, )
        print >>f

    print >>f, "frames:"

    for i, map in enumerate(maps):
        print >>f, "dw frame%u" % (i, )

    print >>f, "frames_end:"
