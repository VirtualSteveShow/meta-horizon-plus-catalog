#!/usr/bin/env python3
"""
Meta Horizon+ Catalog — Template Generator  (April 2026 — NEW GAMES ONLY)
==========================================================================
Only generates templates for games that need NEW art this month.
Existing hero_art/ files from prior months are untouched.

OUTPUTS per atlas page (written to tools/atlas_output/):
  atlas_catalog_01_template.png         <- blank canvas, paint on this
  atlas_catalog_01_overlay_pc.png       <- PC overlay (place above art layer)
  atlas_catalog_01_overlay_mobile.png   <- mobile overlay with safe zone guides

PAINTING WORKFLOW:
  1. Open _template.png as base layer
  2. Add _overlay_pc.png on top
  3. Paint your art BETWEEN those two layers
  4. Hide overlay, flatten, export as atlas_catalog_XX_done.png
  5. python3 extract_atlas.py

MONTHLY:
  Same process — atlas_monthly_01_done.png → extract_atlas.py
"""

from PIL import Image, ImageDraw
import os, math

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CARD_W    = 920
CARD_H    = 300
MONTHLY_W = 600
MONTHLY_H = 340
MARGIN    = 20
COLS      = 2
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "atlas_output")

MOB_SCALE      = 130 / CARD_H
MOB_RENDERED_W = CARD_W * MOB_SCALE
MOB_CROP_EACH  = (MOB_RENDERED_W - 360) / 2
MOB_SAFE_X     = MOB_CROP_EACH / MOB_SCALE  # ~44.5px

GENRE_COLORS = {
    'Shooter':    (239, 68,  68),
    'Puzzle':     (  6,182, 212),
    'Sports':     ( 34,197,  94),
    'Rhythm':     (236, 72, 153),
    'RPG':        (168, 85, 247),
    'Strategy':   (249,115,  22),
    'Fitness':    (132,204,  22),
    'Simulation': ( 14,165, 233),
    'Adventure':  (245,158,  11),
    'Action':     (251,146,  60),
    'Arcade':     (234,179,   8),
    'Casual':     (148,163, 184),
    'Other':      (100,116, 139),
}

def genre_group(genre):
    g = genre.lower()
    if any(x in g for x in ['shooter','fps','tactical','survival']): return 'Shooter'
    if any(x in g for x in ['puzzle','mystery']):                    return 'Puzzle'
    if any(x in g for x in ['sport','golf','cricket','soccer','boxing','bowling','fishing']): return 'Sports'
    if any(x in g for x in ['rhythm','music']):                      return 'Rhythm'
    if any(x in g for x in ['rpg','roguelike','roguelite']):         return 'RPG'
    if any(x in g for x in ['strategy','tower','tabletop']):         return 'Strategy'
    if any(x in g for x in ['fitness','workout']):                   return 'Fitness'
    if any(x in g for x in ['sim','simulation']):                    return 'Simulation'
    if any(x in g for x in ['adventure','narrative','exploration']): return 'Adventure'
    if 'action' in g:                                                return 'Action'
    if any(x in g for x in ['racing','arcade']):                     return 'Arcade'
    if any(x in g for x in ['education','creative','social','casual']): return 'Casual'
    return 'Other'

# ── APRIL 2026: NEW CATALOG GAMES ONLY ──
CATALOG_GAMES = sorted([
    ('Audio Trip',              'Rhythm',              'indie'),
    ('Barbaria',                'Strategy / Action',   'indie'),
    ('Barbershop Simulator VR', 'Simulation',          'indie'),
    ('Breachers',               'Tactical Shooter',    'games'),
    ('Grill on Wheels',         'Simulation',          'indie'),
    ('Prison Boss Prohibition', 'Simulation',          'games'),
    ('Vacation Simulator',      'Simulation / Comedy', 'games'),
], key=lambda x: x[0])

# ── APRIL 2026: NEW MONTHLY REDEEMABLES ──
MONTHLY_GAMES = sorted([
    ('The House of Da Vinci VR', 'Puzzle / Adventure', 'monthly'),
    ('Vendetta Forever',         'Action Shooter',     'monthly'),
], key=lambda x: x[0])


def make_card_overlay(card_w, card_h, genre, mode='pc'):
    img  = Image.new('RGBA', (card_w, card_h), (0,0,0,0))
    draw = ImageDraw.Draw(img)

    gg = genre_group(genre)
    trim_rgb = GENRE_COLORS.get(gg, (14,165,233))
    trim_px = 3 if mode == 'pc' else 7
    radius  = 9 if mode == 'pc' else 19

    for y in range(card_h):
        t = y / card_h
        a = int(25 + (5-25)*(t/0.45)) if t < 0.45 else int(5 + (60-5)*((t-0.45)/0.55))
        draw.line([(0,y),(card_w-1,y)], fill=(0,0,0,a))

    for y in range(0, card_h, 4):
        draw.line([(0,y),(card_w-1,y)], fill=(0,0,0,28))

    r,g,b = trim_rgb
    draw.rectangle([(0,0),(trim_px-1,card_h-1)], fill=(r,g,b,210))
    draw.rounded_rectangle([(0,0),(card_w-1,card_h-1)], radius=radius,
                            outline=(255,255,255,18), width=1)

    if mode == 'mobile':
        sx = int(MOB_SAFE_X)
        for ex in [sx, card_w-sx]:
            y, on = 0, True
            while y < card_h:
                seg = 8 if on else 4
                if on:
                    draw.line([(ex,y),(ex,min(y+seg-1,card_h-1))], fill=(255,200,0,110), width=1)
                y += seg; on = not on
        draw.rectangle([(sx+2,4),(sx+82,14)], fill=(255,200,0,70))
        draw.text((sx+4,4), "MOB SAFE", fill=(255,220,0,200))

    mask = Image.new('L', (card_w, card_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0,0),(card_w-1,card_h-1)], radius=radius, fill=255)
    try:
        import numpy as np
        _,_,_,a_ch = img.split()
        new_a = Image.fromarray((np.array(a_ch,dtype=np.uint16)*np.array(mask,dtype=np.uint16)//255).astype('uint8'))
        img.putalpha(new_a)
    except ImportError:
        img.putalpha(mask)

    return img


def make_atlas_overlay(games, card_w, card_h, mode='pc'):
    rows   = math.ceil(len(games)/COLS)
    aw     = MARGIN + COLS*(card_w+MARGIN)
    ah     = MARGIN + rows*(card_h+MARGIN)
    atlas  = Image.new('RGBA',(aw,ah),(0,0,0,0))
    for i,(name,genre,_) in enumerate(games):
        col = i%COLS; row = i//COLS
        x = MARGIN+col*(card_w+MARGIN); y = MARGIN+row*(card_h+MARGIN)
        atlas.alpha_composite(make_card_overlay(card_w,card_h,genre,mode),(x,y))
    return atlas


def make_atlas_template(games, card_w, card_h):
    rows  = math.ceil(len(games)/COLS)
    aw    = MARGIN+COLS*(card_w+MARGIN)
    ah    = MARGIN+rows*(card_h+MARGIN)
    atlas = Image.new('RGBA',(aw,ah),(8,14,24,255))
    draw  = ImageDraw.Draw(atlas)
    for i,(name,genre,_) in enumerate(games):
        col = i%COLS; row = i//COLS
        x = MARGIN+col*(card_w+MARGIN); y = MARGIN+row*(card_h+MARGIN)
        draw.rectangle([(x,y),(x+card_w-1,y+card_h-1)], fill=(13,26,46,255))
        if card_w == CARD_W:
            sx = int(MOB_SAFE_X)
            draw.rectangle([(x+sx,y),(x+card_w-sx-1,y+card_h-1)], fill=(10,37,64,255))
        r,g,b = GENRE_COLORS.get(genre_group(genre),(14,165,233))
        draw.rectangle([(x,y),(x+2,y+card_h-1)], fill=(r,g,b,180))
        draw.rounded_rectangle([(x,y),(x+card_w-1,y+card_h-1)], radius=8,
                                outline=(255,255,255,25), width=1)
        draw.text((x+card_w//2, y+card_h//2-10), name,
                  fill=(100,150,200,200), anchor='mm')
        draw.text((x+card_w//2, y+card_h//2+16), f"[ {genre} ]",
                  fill=(60,100,140,150), anchor='mm')
        pos = f"col={col+1} row={row+1}  x={x} y={y}  {card_w}x{card_h}"
        draw.text((x+6, y+card_h-13), pos, fill=(70,90,110,170))
    return atlas


if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    per_page = COLS*4  # ROWS=4

    print(f"\n{'='*60}")
    print("  META HORIZON+ — TEMPLATE GENERATOR  (April 2026 new games)")
    print(f"{'='*60}")

    # Catalog new games
    num_a = math.ceil(len(CATALOG_GAMES)/per_page)
    print(f"\nCATALOG (NEW): {len(CATALOG_GAMES)} games → {num_a} atlas  ({CARD_W}x{CARD_H}px/card)")
    print(f"  Mobile safe zone: canvas x={int(MOB_SAFE_X)} – x={CARD_W-int(MOB_SAFE_X)}")
    for a in range(num_a):
        batch  = CATALOG_GAMES[a*per_page:(a+1)*per_page]
        num    = a+1
        pre    = os.path.join(OUTPUT_DIR, f"atlas_catalog_{num:02d}")
        print(f"\n  Atlas {num:02d}:")
        make_atlas_template(batch, CARD_W, CARD_H).save(f"{pre}_template.png")
        print(f"    [template]       {pre}_template.png")
        make_atlas_overlay(batch, CARD_W, CARD_H,'pc').save(f"{pre}_overlay_pc.png")
        print(f"    [overlay PC]     {pre}_overlay_pc.png")
        make_atlas_overlay(batch, CARD_W, CARD_H,'mobile').save(f"{pre}_overlay_mobile.png")
        print(f"    [overlay mobile] {pre}_overlay_mobile.png")
        print(f"    Card positions:")
        for i,(name,genre,_) in enumerate(batch):
            col=i%COLS; row=i//COLS
            cx=MARGIN+col*(CARD_W+MARGIN); cy=MARGIN+row*(CARD_H+MARGIN)
            print(f"      [{i+1:>2}] {name:<46} x={cx} y={cy}")

    # Monthly new games
    print(f"\nMONTHLY (NEW): {len(MONTHLY_GAMES)} games → 1 atlas  ({MONTHLY_W}x{MONTHLY_H}px/card)")
    pre = os.path.join(OUTPUT_DIR, "atlas_monthly_01")
    make_atlas_template(MONTHLY_GAMES,MONTHLY_W,MONTHLY_H).save(f"{pre}_template.png")
    print(f"    [template]       {pre}_template.png")
    make_atlas_overlay(MONTHLY_GAMES,MONTHLY_W,MONTHLY_H,'pc').save(f"{pre}_overlay_pc.png")
    print(f"    [overlay PC]     {pre}_overlay_pc.png")
    make_atlas_overlay(MONTHLY_GAMES,MONTHLY_W,MONTHLY_H,'mobile').save(f"{pre}_overlay_mobile.png")
    print(f"    [overlay mobile] {pre}_overlay_mobile.png")

    print(f"\n{'='*60}")
    print(f"  Done — all files in {OUTPUT_DIR}/")
    print(f"{'='*60}")
    print("""
LAYER STACK IN YOUR PAINT APP:
  TOP    overlay_pc.png     (gradient + scanlines + trim + border)
  MID    YOUR ART           (paint here)
  BOTTOM _template.png      (safe zone guides + game labels)

  Flip overlay to _mobile to check phone crop.
  Yellow dashed lines on mobile overlay = screen edge.

After painting, name your file atlas_catalog_01_done.png (or _monthly_)
then run:  python3 extract_atlas.py
""")
