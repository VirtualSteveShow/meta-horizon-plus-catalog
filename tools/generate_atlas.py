#!/usr/bin/env python3
"""
Meta Horizon+ Catalog — Atlas Generator  (April 2026 — NEW GAMES ONLY)
=======================================================================
Renders UI overlays using the REAL catalog CSS via headless Chromium (Playwright),
so overlays are pixel-perfect 1:1 with the actual app — same fonts, same emoji,
same element positions.

SETUP (one time):
  pip install playwright pillow --break-system-packages
  python3 -m playwright install chromium

OUTPUT FILES (per atlas, in tools/atlas_output/):
  atlas_catalog_01_ui.png      — transparent RGBA overlay, mobile layout
  masks/
    atlas_catalog_01_mask_cell_01-08.png  — individual cell masks
    atlas_catalog_01_mask.png             — full atlas mask
    atlas_catalog_01_mask_rounded.png     — full atlas mask with rounded corners

WORKFLOW:
  1. python3 generate_atlas.py   (generates overlays + masks)
  2. In GIMP: File -> New -> 920x300px canvas
  3. Open atlas_catalog_01_ui.png as a new layer on top
     - Shaded wings = mobile crop zone (~45px each side)
     - Dashed gold line = exact mobile safe boundary
  4. Paint art on a layer BELOW the overlay
  5. Hide overlay -> flatten -> export as atlas_catalog_01_done.png
  6. python3 extract_atlas.py -> slices into hero_art/
"""

import os, math, re, io
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(SCRIPT_DIR, "atlas_output")

# ══════════════════════════════════════════════════════════════
# CONFIG  (must match extract_atlas.py exactly)
# ══════════════════════════════════════════════════════════════
CARD_W      = 920
CARD_H      = 300
MARGIN      = 20
COLS        = 2
ROWS        = 4
CARD_RADIUS = 8

# Mobile viewport — S24 Ultra CSS width (1440px physical / DPR 3.5 ≈ 412px)
MOB_W, MOB_H   = 412, 130
MOB_BG_SCALE   = max(MOB_W / CARD_W, MOB_H / CARD_H)
MOB_CROP_L     = round((CARD_W * MOB_BG_SCALE - MOB_W) / 2 / MOB_BG_SCALE)

DEVICE_SCALE_FACTOR = 3

# Genre colors (exact match to app CSS)
GENRE_COLORS = {
    'Shooter':    (239,  68,  68),
    'Puzzle':     (  6, 182, 212),
    'Sports':     ( 34, 197,  94),
    'Rhythm':     (236,  72, 153),
    'RPG':        (168,  85, 247),
    'Strategy':   (249, 115,  22),
    'Fitness':    (132, 204,  22),
    'Simulation': ( 14, 165, 233),
    'Adventure':  (245, 158,  11),
    'Action':     (251, 146,  60),
    'Arcade':     (234, 179,   8),
    'Casual':     (148, 163, 184),
    'Other':      (100, 116, 139),
}

def genre_group(genre):
    g = genre.lower()
    if any(x in g for x in ['shooter','fps','tactical','survival']): return 'Shooter'
    if any(x in g for x in ['puzzle','mystery']):                    return 'Puzzle'
    if any(x in g for x in ['sport','golf','cricket','soccer',
                              'boxing','bowling','fishing']):         return 'Sports'
    if any(x in g for x in ['rhythm','music']):                      return 'Rhythm'
    if any(x in g for x in ['rpg','roguelike','roguelite']):         return 'RPG'
    if any(x in g for x in ['strategy','tower','tabletop','naval']): return 'Strategy'
    if any(x in g for x in ['fitness','workout']):                   return 'Fitness'
    if any(x in g for x in ['sim','simulation']):                    return 'Simulation'
    if any(x in g for x in ['adventure','narrative','exploration']): return 'Adventure'
    if 'action' in g:                                                 return 'Action'
    if any(x in g for x in ['racing','arcade']):                     return 'Arcade'
    if any(x in g for x in ['education','creative','social',
                              'casual','platformer']):                return 'Casual'
    return 'Other'


# ══════════════════════════════════════════════════════════════
# APRIL 2026: NEW GAMES ONLY (catalog + monthly combined)
# ══════════════════════════════════════════════════════════════
CATALOG_GAMES = sorted([
    {'name': 'Audio Trip',              'genre': 'Rhythm',              'type': 'indie', 'mp': [],              'tag': 'APR', 'rating': 4.6, 'reviews': 1700},
    {'name': 'Barbaria',                'genre': 'Strategy / Action',   'type': 'indie', 'mp': [],              'tag': 'APR', 'rating': 4.7, 'reviews': 514},
    {'name': 'Barbershop Simulator VR', 'genre': 'Simulation',          'type': 'indie', 'mp': [],              'tag': 'APR', 'rating': 4.7, 'reviews': 540},
    {'name': 'Breachers',               'genre': 'Tactical Shooter',    'type': 'games', 'mp': ['multi','coop'],'tag': 'APR', 'rating': 4.5, 'reviews': 5900},
    {'name': 'Grill on Wheels',         'genre': 'Simulation',          'type': 'indie', 'mp': [],              'tag': 'APR', 'rating': 4.5, 'reviews': 1200},
    {'name': 'Prison Boss Prohibition', 'genre': 'Simulation',          'type': 'games', 'mp': [],              'tag': 'APR', 'rating': 4.6, 'reviews': 573},
    {'name': 'The House of Da Vinci VR','genre': 'Puzzle / Adventure',  'type': 'games', 'mp': [],              'tag': 'APR', 'rating': 4.7, 'reviews': 836},
    {'name': 'Vacation Simulator',      'genre': 'Simulation / Comedy', 'type': 'games', 'mp': [],              'tag': 'APR', 'rating': 4.5, 'reviews': 4900},
    {'name': 'Vendetta Forever',        'genre': 'Action Shooter',      'type': 'games', 'mp': [],              'tag': 'APR', 'rating': 4.7, 'reviews': 185},
], key=lambda g: g['name'])

CLAIMABLE = {'Vendetta Forever', 'The House of Da Vinci VR'}


# ══════════════════════════════════════════════════════════════
# CSS EXTRACTION
# ══════════════════════════════════════════════════════════════

def extract_css(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        src = f.read()
    blocks = re.findall(r'<style>(.*?)</style>', src, re.DOTALL)
    return '\n'.join(blocks)


# ══════════════════════════════════════════════════════════════
# CARD HTML BUILDER
# ══════════════════════════════════════════════════════════════

def rating_html(g):
    count = f"{g['reviews']/1000:.1f}K".replace('.0K','K') if g['reviews'] >= 1000 else str(g['reviews'])
    return f'<div class="game-rating"><span class="stars">★</span><span class="rating-num">{g["rating"]:.1f}</span><span class="review-count">({count})</span></div>'

def build_card_html(g):
    gg = genre_group(g['genre'])
    is_claimable = g['name'] in CLAIMABLE
    classes = 'game-card'
    if g['type'] == 'indie':   classes += ' indie'
    if is_claimable:           classes += ' claimable'

    mp_badges = ''
    for m in g.get('mp', []):
        if m == 'multi': mp_badges += '<span class="mp-badge multi">👥 MULTI</span>'
        if m == 'coop':  mp_badges += '<span class="mp-badge coop">🤝 CO-OP</span>'

    tag_html = ''
    if g.get('tag'):
        tag_html = f'<span class="tag-{g["tag"].lower()}-inline">{g["tag"]}</span>'

    indie_span = ''
    if g['type'] == 'indie':
        indie_span = ' · <span class="game-genre-indie">INDIE</span>'

    tags_row = ''
    if mp_badges or is_claimable:
        claim = '<span class="claim-badge">⚡ FREE THIS MONTH</span>' if is_claimable else ''
        tags_row = f'<div class="card-tags-row">{claim}{mp_badges}</div>'

    rating = rating_html(g) if g.get('rating') else ''
    name_esc = g['name'].replace("'", "&#39;").replace('"', '&quot;')

    return f'''
    <div class="{classes}" data-genre-group="{gg}">
      <div class="card-title-block">
        <div class="card-name-row">
          <div class="game-name">{name_esc}</div>
          {tag_html}
        </div>
        <span class="game-genre">{g["genre"]}{indie_span}</span>
        {tags_row}
      </div>
      <div class="card-top-right">
        <button class="star-btn">&#11088;</button>
      </div>
      <div class="card-bottom-left">
        {rating}
      </div>
      <div class="card-bottom-center">
        <a class="store-btn" href="#">&#x1F6D2; <span>Store</span></a>
      </div>
      <div class="card-bottom-right">
        <button class="remove-btn">✕</button>
      </div>
    </div>'''


# ══════════════════════════════════════════════════════════════
# PLAYWRIGHT RENDERER
# ══════════════════════════════════════════════════════════════

STRIP_CSS = """
  html, body { background: transparent !important; }
  .game-card {
    background: transparent !important;
    background-image: none !important;
    border: none !important;
    box-shadow: none !important;
  }
  .game-card::after  { display: none !important; }
  .game-card::before { opacity: 1 !important; }
"""

def render_card_transparent(page, card_html, card_css, mob_w, mob_h):
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ background:transparent; width:{mob_w}px; overflow:hidden; }}
{card_css}
{STRIP_CSS}
</style></head>
<body>{card_html}</body></html>"""

    page.set_content(html)
    page.wait_for_timeout(80)
    png = page.screenshot(
        omit_background=True,
        clip={'x': 0, 'y': 0, 'width': mob_w, 'height': mob_h}
    )
    return Image.open(io.BytesIO(png)).convert('RGBA')


def render_all_cards(games, card_css, mob_w, mob_h, canvas_w, canvas_h, label=""):
    results = []
    total = len(games)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': mob_w, 'height': mob_h},
                                   device_scale_factor=DEVICE_SCALE_FACTOR)
        for i, g in enumerate(games):
            card_html = build_card_html(g)
            mob_img = render_card_transparent(page, card_html, card_css, mob_w, mob_h)
            canvas_img = mob_img.resize((canvas_w, canvas_h), Image.LANCZOS)
            results.append(canvas_img)
            print(f"  rendered {i+1}/{total}  {g['name']}", end='\r', flush=True)
        browser.close()
    print(f"  {label}done — {total} cards rendered{' '*30}")
    return results


# ══════════════════════════════════════════════════════════════
# CROP WING OVERLAY
# ══════════════════════════════════════════════════════════════

def add_crop_wings(canvas_img, card_w, card_h, mob_crop_l):
    if mob_crop_l <= 0:
        return canvas_img
    d = ImageDraw.Draw(canvas_img)
    d.rectangle([0, 0, mob_crop_l - 1, card_h - 1], fill=(0, 0, 0, 70))
    d.rectangle([card_w - mob_crop_l, 0, card_w - 1, card_h - 1], fill=(0, 0, 0, 70))
    for ly in range(0, card_h, 6):
        d.line([(mob_crop_l, ly), (mob_crop_l, ly+3)], fill=(255,190,0,160), width=1)
        d.line([(card_w-mob_crop_l-1, ly), (card_w-mob_crop_l-1, ly+3)], fill=(255,190,0,160), width=1)
    return canvas_img


# ══════════════════════════════════════════════════════════════
# MASK GENERATION
# ══════════════════════════════════════════════════════════════

def rounded_rect_mask(draw, x, y, w, h, r, fill):
    draw.rectangle([x+r, y, x+w-r, y+h], fill=fill)
    draw.rectangle([x, y+r, x+w, y+h-r], fill=fill)
    draw.ellipse([x,       y,       x+2*r,   y+2*r  ], fill=fill)
    draw.ellipse([x+w-2*r, y,       x+w,     y+2*r  ], fill=fill)
    draw.ellipse([x,       y+h-2*r, x+2*r,   y+h    ], fill=fill)
    draw.ellipse([x+w-2*r, y+h-2*r, x+w,     y+h    ], fill=fill)

def generate_masks(games_in_atlas, prefix, card_w, card_h, masks_dir):
    atlas_w = MARGIN + COLS * (card_w + MARGIN)
    atlas_h = MARGIN + ROWS * (card_h + MARGIN)
    n = len(games_in_atlas)

    mask   = Image.new('L', (atlas_w, atlas_h), 0)
    md     = ImageDraw.Draw(mask)
    mask_r = Image.new('L', (atlas_w, atlas_h), 0)
    mdr    = ImageDraw.Draw(mask_r)
    for i in range(n):
        col, row = i % COLS, i // COLS
        x = MARGIN + col * (card_w + MARGIN)
        y = MARGIN + row * (card_h + MARGIN)
        md.rectangle([x, y, x+card_w-1, y+card_h-1], fill=255)
        rounded_rect_mask(mdr, x, y, card_w-1, card_h-1, CARD_RADIUS, 255)
    mask.save(os.path.join(masks_dir, f"{prefix}_mask.png"))
    mask_r.save(os.path.join(masks_dir, f"{prefix}_mask_rounded.png"))

    for cell in range(COLS * ROWS):
        cm  = Image.new('L', (atlas_w, atlas_h), 0)
        cmd = ImageDraw.Draw(cm)
        col, row = cell % COLS, cell // COLS
        x = MARGIN + col * (card_w + MARGIN)
        y = MARGIN + row * (card_h + MARGIN)
        cmd.rectangle([x, y, x+card_w-1, y+card_h-1], fill=255)
        cm.save(os.path.join(masks_dir, f"{prefix}_mask_cell_{cell+1:02d}.png"))


# ══════════════════════════════════════════════════════════════
# GENERATE ALL ATLASES
# ══════════════════════════════════════════════════════════════

def game_to_filename(name):
    name = name.lower()
    name = re.sub(r"['\"\!\?\+\:\.\,]", '', name)
    name = re.sub(r'[^a-z0-9]+', '-', name)
    return name.strip('-') + '.jpg'

def generate_atlases(games, prefix, card_w, card_h, mob_w, mob_h, card_css):
    per_page    = COLS * ROWS
    atlas_w     = MARGIN + COLS * (card_w + MARGIN)
    atlas_h     = MARGIN + ROWS * (card_h + MARGIN)
    num_atlases = math.ceil(len(games) / per_page)
    masks_dir   = os.path.join(OUTPUT_DIR, "masks")
    os.makedirs(masks_dir, exist_ok=True)

    bg_scale    = max(mob_w / card_w, mob_h / card_h)
    crop_canvas = round((card_w * bg_scale - mob_w) / 2 / bg_scale)

    print(f"\n{prefix.upper()} — {len(games)} games → {num_atlases} atlas(es)")
    print(f"  Card: {card_w}×{card_h}px | Mobile viewport: {mob_w}×{mob_h}px | Crop: {crop_canvas}px each side")
    print(f"  Rendering cards via Playwright...")

    rendered = render_all_cards(games, card_css, mob_w, mob_h, card_w, card_h, label=prefix + " ")

    for atlas_idx in range(num_atlases):
        start = atlas_idx * per_page
        batch = games[start:start + per_page]
        atlas = Image.new('RGBA', (atlas_w, atlas_h), (0, 0, 0, 0))

        for i, g in enumerate(batch):
            col, row = i % COLS, i // COLS
            cx = MARGIN + col * (card_w + MARGIN)
            cy = MARGIN + row * (card_h + MARGIN)
            card_img = rendered[start + i].copy()
            add_crop_wings(card_img, card_w, card_h, crop_canvas)
            atlas.paste(card_img, (cx, cy), card_img)

        fname = f"{prefix}_{atlas_idx+1:02d}_ui.png"
        atlas.save(os.path.join(OUTPUT_DIR, fname))

        if atlas_idx == 0:
            generate_masks(batch, f"{prefix}_{atlas_idx+1:02d}", card_w, card_h, masks_dir)
            print(f"  ✓ {fname}  +  masks/")
        else:
            print(f"  ✓ {fname}")

        for i, g in enumerate(batch):
            col, row = i % COLS, i // COLS
            x = MARGIN + col * (card_w + MARGIN)
            y = MARGIN + row * (card_h + MARGIN)
            print(f"      [{start+i+1:3d}] x={x:<5} y={y:<5}  {g['name']}")


# ══════════════════════════════════════════════════════════════
# PLACEHOLDER ART
# ══════════════════════════════════════════════════════════════

def generate_placeholders(games, card_w, card_h):
    ph_dir = os.path.join(OUTPUT_DIR, "place_holders")
    os.makedirs(ph_dir, exist_ok=True)
    system_fonts = [
        "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    font_path = next((p for p in system_fonts if os.path.exists(p)), None)
    def make_font(size):
        if font_path:
            try: return ImageFont.truetype(font_path, size)
            except: pass
        return ImageFont.load_default()

    print(f"\nPLACEHOLDERS → {ph_dir}/")
    for g in games:
        img  = Image.new('RGB', (card_w, card_h), (12, 18, 30))
        draw = ImageDraw.Draw(img)
        f    = make_font(48)
        words = g['name'].split()
        lines, cur = [], ''
        for w in words:
            test = (cur + ' ' + w).strip()
            try: tw = f.getbbox(test)[2] - f.getbbox(test)[0]
            except: tw = len(test) * 28
            if tw <= card_w - 60: cur = test
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        try: lh = f.getbbox('Ag')[3] - f.getbbox('Ag')[1]
        except: lh = 52
        ty = (card_h - len(lines) * (lh + 6)) // 2
        for line in lines:
            try: lw = f.getbbox(line)[2] - f.getbbox(line)[0]
            except: lw = len(line) * 28
            tx = (card_w - lw) // 2
            draw.text((tx+2, ty+2), line, fill=(0,0,0), font=f)
            draw.text((tx,   ty),   line, fill=(220,230,255), font=f)
            ty += lh + 6
        fname = game_to_filename(g['name'])
        img.save(os.path.join(ph_dir, fname), 'JPEG', quality=90)
    print(f"  {len(games)} placeholder files written.")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    candidates = [
        os.path.join(SCRIPT_DIR, 'index.html'),
        os.path.join(SCRIPT_DIR, '..', 'index.html'),
    ]
    catalog_html = next((p for p in candidates if os.path.exists(p)), None)
    if not catalog_html:
        print("ERROR: Could not find index.html (expected in repo root, one level up from tools/)")
        sys.exit(1)

    print("=" * 62)
    print("  META HORIZON+  |  ATLAS GENERATOR  (April 2026 new games)")
    print("=" * 62)
    print(f"  Catalog HTML: {catalog_html}")

    card_css = extract_css(catalog_html)

    generate_atlases(
        CATALOG_GAMES, "atlas_catalog",
        CARD_W, CARD_H, MOB_W, MOB_H,
        card_css
    )

    generate_placeholders(CATALOG_GAMES, CARD_W, CARD_H)

    print(f"\nAll files saved to: {OUTPUT_DIR}/")
    print("\nWORKFLOW:")
    print("  1. In GIMP: File -> New -> 920x300px (or open a blank canvas)")
    print("  2. File -> Open as Layers -> atlas_catalog_01_ui.png  (goes on top)")
    print("     - Dark shaded wings = mobile crop zone (~45px each side)")
    print("     - Dashed gold line  = exact mobile safe boundary")
    print("  3. Paint on a layer BELOW the overlay")
    print("  4. Hide overlay -> flatten -> export as atlas_catalog_01_done.png")
    print("  5. python3 extract_atlas.py")
