colors = [
    (0x48, 0x7A, 0x3B),
    (0xD3, 0xF2, 0x84),
    (0x8A, 0xBA, 0x43),
    (0x23, 0x1B, 0x12),
]

with open('palette.asm', 'w') as f:
    print >>f, "; palette"
    print >>f, "palette:"

    for r, g, b in colors:
        r1 = int(0x1f * (r / 255.))
        g1 = int(0x1f * (g / 255.))
        b1 = int(0x1f * (b / 255.))

        w = r1 | (g1 << 5) | (b1 << 10)
        print >>f, "dw $%04x" % (w, )

    print >>f, "palette_end:"
