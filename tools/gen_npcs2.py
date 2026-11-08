#!/usr/bin/env python3
"""Generate the settlement NPC sprites (Settlements batch).

The original four townsfolk are generated portraits on the shared
512x688 canvas. The four settlement folk are drawn HERE as chunky pixel
art: primitives on a 128x172 grid (the same 512:688 aspect), flat
grade-palette tones with one shade tone per fur, then NEAREST x4 to
512x688 so the pixel grain matches the family's chunk. Every visible
channel is >= 26 (the no-true-black art law; tools/lift_shadows.py).

Draws: Bramble the hedgehog innkeeper, Tansy the squirrel shopkeep,
Scout Vex the fox, the Hermit badger. Feet sit at the canvas bottom,
figures fill ~90% of the height — the def.h / def.head convention the
painter expects (adults .240 / .224).

Run from the repo root:  python3 tools/gen_npcs2.py
"""
from PIL import Image, ImageDraw

GW, GH, SC = 128, 172, 4          # grid, then x4 -> 512x688
OUT = 'assets/img/npc-{}.png'

INK = (34, 30, 27)                # lifted near-black (eyes, details)
GLINT = (246, 241, 227)


def canvas():
    im = Image.new('RGBA', (GW, GH), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def E(d, cx, cy, w, h, fill):
    d.ellipse([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], fill=fill)


def eye(d, cx, cy, w=7, h=10):
    E(d, cx, cy, w, h, INK)
    E(d, cx - w * .18, cy - h * .22, max(2, w * .34), max(2, h * .3), GLINT)


def finish(im, name):
    im.resize((GW * SC, GH * SC), Image.NEAREST).save(OUT.format(name))
    a = im.getchannel('A')
    print(name, 'bbox', a.getbbox())


def bramble():
    im, d = canvas()
    SP, SPL, SPD = (74, 56, 38), (112, 88, 58), (50, 38, 27)
    CRM, CRM2 = (232, 211, 172), (242, 224, 188)
    E(d, 50, 166, 17, 8, (90, 66, 44)); E(d, 78, 166, 17, 8, (90, 66, 44))       # feet
    d.ellipse([13, 24, 115, 158], fill=SP)                                       # spine dome
    d.ellipse([58, 30, 115, 152], fill=SPD)                                      # shaded right mass
    d.ellipse([20, 28, 104, 150], fill=SP)
    import math
    for row in range(6):                                                         # spike texture rows
        y = 38 + row * 19
        for i in range(7):
            x = 24 + i * 13 + (row % 2) * 6
            if (x - 64) ** 2 / 46 ** 2 + (y - 92) ** 2 / 62 ** 2 > .92: continue
            d.polygon([(x - 5, y + 6), (x + 5, y + 6), (x, y - 7)], fill=SPL if (i + row) % 2 else SP)
    E(d, 33, 52, 13, 13, SP); E(d, 95, 52, 13, 13, SP)                           # ears under spines
    E(d, 33, 52, 7, 7, CRM); E(d, 95, 52, 7, 7, CRM)
    E(d, 26, 122, 13, 22, SP); E(d, 102, 122, 13, 22, SP)                        # side arms (spiny)
    d.ellipse([36, 74, 92, 134], fill=CRM)                                       # face
    E(d, 64, 116, 26, 15, CRM2)                                                  # muzzle
    E(d, 64, 109, 10, 7, (122, 74, 58))                                          # nose
    eye(d, 50, 98); eye(d, 78, 98)
    E(d, 40, 114, 9, 6, (216, 166, 132)); E(d, 88, 114, 9, 6, (216, 166, 132))   # blush
    d.rounded_rectangle([43, 130, 85, 165], 6, fill=(239, 230, 207))             # apron
    d.rectangle([43, 130, 85, 135], fill=(150, 120, 84))                         # apron strap band
    d.rectangle([57, 144, 71, 155], outline=(150, 120, 84), width=2)             # pocket
    E(d, 47, 138, 10, 12, CRM); E(d, 81, 138, 10, 12, CRM)                       # paws resting on the apron
    finish(im, 'bramble')


def tansy():
    im, d = canvas()
    FU, FUD, FUL = (176, 106, 52), (138, 79, 36), (200, 134, 76)
    CRM = (240, 220, 184)
    for (x, y, r, c) in [(98, 138, 15, FU), (106, 116, 15, FU), (108, 92, 14, FU),   # tail curl up the right side
                         (104, 68, 13, FU), (96, 48, 12, FU), (86, 36, 10, FUL), (80, 30, 8, CRM),
                         (100, 124, 11, FUD), (102, 98, 10, FUD), (98, 74, 9, FUD)]:
        E(d, x, y, r * 2, r * 2, c)
    E(d, 47, 166, 16, 8, FUD); E(d, 79, 166, 16, 8, FUD)                         # feet
    d.ellipse([33, 82, 95, 168], fill=FU)                                        # body
    d.ellipse([58, 86, 95, 164], fill=FUD)                                       # shade side
    d.ellipse([35, 84, 90, 166], fill=FU)
    d.ellipse([45, 102, 83, 164], fill=CRM)                                      # belly
    d.ellipse([34, 26, 94, 92], fill=FU)                                         # head
    d.polygon([(38, 34), (42, 4), (52, 28)], fill=FU)                            # ears + tufts
    d.polygon([(76, 28), (86, 4), (90, 34)], fill=FU)
    d.polygon([(41, 26), (43, 12), (48, 24)], fill=CRM)
    d.polygon([(80, 24), (85, 12), (87, 26)], fill=CRM)
    d.polygon([(34, 58), (26, 66), (35, 70)], fill=FUL)                          # cheek tufts
    d.polygon([(94, 58), (102, 66), (93, 70)], fill=FUL)
    E(d, 64, 72, 34, 20, CRM)                                                    # muzzle
    E(d, 64, 63, 10, 7, (90, 54, 40))                                            # nose
    eye(d, 50, 50, 8, 11); eye(d, 78, 50, 8, 11)
    E(d, 33, 116, 12, 20, FU); E(d, 95, 116, 12, 20, FU)                         # arms
    E(d, 64, 128, 17, 19, (201, 160, 106))                                       # acorn nut
    d.polygon([(54, 122), (74, 122), (70, 114), (58, 114)], fill=(110, 74, 38))  # acorn cap
    E(d, 64, 112, 4, 5, (110, 74, 38))                                           # stem
    E(d, 50, 124, 10, 12, FU); E(d, 78, 124, 10, 12, FU)                         # paws on the acorn
    finish(im, 'tansy')


def vex():
    im, d = canvas()
    FU, FUD = (201, 122, 48), (164, 94, 36)
    WHT = (242, 234, 216); DRK = (74, 52, 33)
    for (x, y, w, h, c) in [(26, 128, 34, 44, FU), (18, 148, 26, 30, FU), (14, 160, 20, 18, WHT)]:   # tail, white tip low-left
        E(d, x, y, w, h, c)
    d.rectangle([45, 148, 58, 170], fill=DRK); d.rectangle([70, 148, 83, 170], fill=DRK)              # socks
    d.ellipse([35, 78, 93, 160], fill=FU)                                        # body
    d.ellipse([60, 82, 93, 156], fill=FUD)
    d.ellipse([37, 80, 88, 158], fill=FU)
    d.ellipse([47, 94, 81, 156], fill=WHT)                                       # chest
    d.polygon([(35, 76), (93, 76), (93, 88), (35, 88)], fill=(85, 125, 60))      # scout scarf band
    d.polygon([(35, 82), (93, 82), (93, 88), (35, 88)], fill=(64, 98, 44))
    d.polygon([(76, 86), (88, 86), (84, 106), (74, 100)], fill=(85, 125, 60))    # scarf tail
    d.ellipse([33, 22, 95, 86], fill=FU)                                         # head
    d.polygon([(36, 30), (43, 2), (55, 24)], fill=FU)                            # ears
    d.polygon([(73, 24), (85, 2), (92, 30)], fill=FU)
    d.polygon([(40, 18), (43, 5), (49, 16)], fill=DRK)                           # ear tips
    d.polygon([(79, 16), (85, 5), (88, 18)], fill=DRK)
    d.polygon([(47, 56), (81, 56), (72, 82), (56, 82)], fill=WHT)                # muzzle
    E(d, 64, 60, 11, 8, (40, 34, 30))                                            # nose
    eye(d, 49, 46, 8, 10); eye(d, 79, 46, 8, 10)
    E(d, 42, 60, 8, 5, (222, 168, 120)); E(d, 86, 60, 8, 5, (222, 168, 120))     # cheek warmth
    E(d, 31, 112, 11, 20, FU); E(d, 97, 112, 11, 20, FU)                         # arms
    finish(im, 'vex')


def hermit():
    im, d = canvas()
    GY, GYD, GYL = (141, 146, 145), (96, 102, 101), (170, 174, 170)
    WHT = (238, 233, 220); STR = (51, 48, 44)
    d.line([(106, 58), (97, 170)], fill=(110, 74, 38), width=5)                  # staff (behind body)
    d.line([(106, 58), (103, 96)], fill=(84, 58, 30), width=2)
    E(d, 104, 50, 13, 10, (101, 168, 90)); E(d, 112, 56, 10, 8, (66, 140, 60))   # leaf sprout on the staff
    E(d, 45, 166, 18, 8, (70, 74, 72)); E(d, 83, 166, 18, 8, (70, 74, 72))       # feet
    d.ellipse([23, 76, 105, 168], fill=GY)                                       # stout body
    d.ellipse([62, 80, 105, 164], fill=GYD)                                      # shade side
    d.ellipse([25, 78, 100, 166], fill=GY)
    d.ellipse([39, 106, 89, 164], fill=GYL)                                      # belly
    d.polygon([(23, 96), (105, 96), (96, 74), (32, 74)], fill=(84, 94, 88))      # cloak shoulders
    E(d, 28, 112, 12, 22, GY); E(d, 100, 112, 12, 22, GY)                        # arms
    E(d, 33, 24, 14, 12, GY); E(d, 95, 24, 14, 12, GY)                           # ears
    E(d, 33, 22, 8, 7, STR); E(d, 95, 22, 8, 7, STR)
    d.ellipse([31, 16, 97, 88], fill=WHT)                                        # white face
    d.polygon([(48, 18), (57, 18), (55, 52), (46, 78), (40, 78), (42, 48)], fill=STR)   # badger stripes
    d.polygon([(71, 18), (80, 18), (86, 48), (88, 78), (82, 78), (73, 52)], fill=STR)
    eye(d, 49, 56, 7, 9); eye(d, 79, 56, 7, 9)                                   # eyes ride the stripes (glint sells them)
    E(d, 64, 74, 24, 13, (226, 219, 203))                                        # muzzle
    E(d, 64, 68, 11, 8, (138, 106, 98))                                          # nose
    d.line([(58, 79), (70, 79)], fill=(120, 112, 100), width=2)                  # mouth
    E(d, 99, 118, 10, 13, GYL)                                                   # paw resting by the staff
    finish(im, 'hermit')


if __name__ == '__main__':
    bramble(); tansy(); vex(); hermit()
