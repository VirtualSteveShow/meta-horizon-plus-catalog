#!/usr/bin/env python3
"""
Meta Horizon+ Catalog — Atlas Extractor  (May 2026 — NEW GAMES ONLY)
========================================================================
Slices finished atlas PNGs into individual hero_art/ JPG files.
Only processes the new April 2026 games — existing art is untouched.

USAGE:
  python3 extract_atlas.py

Place your completed atlas files (atlas_catalog_01_done.png etc.) in
tools/atlas_output/, then run this script from anywhere.
Files are written directly to hero_art/ in the repo root.
"""

from PIL import Image
import os, re

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
ATLAS_DIR   = os.path.join(SCRIPT_DIR, "atlas_output")
OUTPUT_DIR  = os.path.join(SCRIPT_DIR, "..", "hero_art")

CARD_W      = 920
CARD_H      = 300
MARGIN      = 20
COLS        = 2
ROWS        = 4
JPG_QUALITY = 92

# ── MAY 2026: ALL NEW GAMES (catalog + monthly, alphabetical = atlas order) ──
CATALOG_GAMES = sorted([
    "A Fisherman's Tale 2",
    'Action Hero',
    'After the Fall',
    'Ancient Dungeon',
    'Banners & Bastions',
    'Crisis Brigade 2 reloaded',
    'Escaping Wonderland',
    'First Person Tennis - The Real Tennis Simulator',
    'Fruit Ninja',
    'Shave & Stuff',
    'Table Troopers',
])


def game_to_filename(name, suffix=''):
    """Convert game name to safe filename: lowercase, hyphens, no special chars."""
    name = name.lower()
    name = re.sub(r"['\"\!\?\+\:\.\,]", '', name)
    name = re.sub(r'[^a-z0-9]+', '-', name)
    name = name.strip('-')
    return name + (f'-{suffix}' if suffix else '') + '.jpg'


def extract_atlas(atlas_path, games, card_w, card_h, start_index, suffix=''):
    """Extract all card cells from a completed atlas image."""
    img = Image.open(atlas_path).convert('RGB')
    extracted = 0

    for i, game in enumerate(games):
        col = i % COLS
        row = i // COLS
        x = MARGIN + col * (card_w + MARGIN)
        y = MARGIN + row * (card_h + MARGIN)

        cell = img.crop((x, y, x + card_w, y + card_h))
        fname = game_to_filename(game, suffix)
        out_path = os.path.join(OUTPUT_DIR, fname)
        cell.save(out_path, 'JPEG', quality=JPG_QUALITY)
        print(f"  ✓ {fname}  ←  \"{game}\"")
        extracted += 1

    return extracted


def find_done_atlases(prefix):
    """Find all *_done.png atlas files for a given prefix."""
    if not os.path.isdir(ATLAS_DIR):
        return []
    files = []
    for f in sorted(os.listdir(ATLAS_DIR)):
        if f.startswith(prefix) and f.endswith('_done.png'):
            files.append(os.path.join(ATLAS_DIR, f))
    return files


if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    per_page = COLS * ROWS
    total = 0

    catalog_done = find_done_atlases('atlas_catalog')
    if catalog_done:
        print(f"\nFound {len(catalog_done)} completed atlas file(s)")
        for i, path in enumerate(catalog_done):
            start = i * per_page
            batch = CATALOG_GAMES[start:start + per_page]
            print(f"\n  Extracting {os.path.basename(path)} ({len(batch)} cards):")
            total += extract_atlas(path, batch, CARD_W, CARD_H, start)
    else:
        print("\nNo completed atlas files found.")
        print("  Name your finished file: atlas_catalog_01_done.png")

    if total:
        print(f"\n✓ Extracted {total} files to {os.path.normpath(OUTPUT_DIR)}/")
        print("\nFilename map (for reference):")
        for g in CATALOG_GAMES:
            print(f"  '{g}': 'hero_art/{game_to_filename(g)}',")
    else:
        print("\nNo files extracted. Finish painting and rename files with _done suffix.")
