# Meta Horizon+ Catalog — Monthly Update Instructions

This file is a guide for Claude Code. Read it in full before starting, then follow
the steps in order. Collect all information from the user before touching any code.

---

## Step 1 — Gather Information From the User

Ask the user for ALL of the following before making any changes. Do not start editing
until you have everything.

### 1a. What month is this update for?
You need the full month name and year (e.g. "May 2026"). This appears in many places.

### 1b. New Free Monthly Games
Ask: "What are the two new free monthly redeemable games this month?"
These replace last month's two monthly games entirely.

### 1c. Full game list from the Meta Horizon+ website
Ask the user to:
1. Open a **private/incognito browser window** (important — if signed in, already-redeemed
   titles may be hidden)
2. Go to the Meta Horizon+ catalog page
3. Select all text on the page (Ctrl+A) and copy/paste it here

This gives you the current full catalog with semi-current ratings. Use it to:
- Confirm which games were added this month
- Confirm which games were removed
- Pull updated ratings and review counts for new games

### 1d. Ratings for the new monthly free games
The monthly free games are often not shown on the main catalog page, or their ratings
may differ. Ask the user to also check each monthly game's individual Meta store page
and provide the current star rating and review count for each one. Example:

> "Can you check the store pages for [Game A] and [Game B] and tell me the current
> star rating and review count shown on each?"

Do not estimate or carry over ratings from a previous source — monthly games in
particular tend to have ratings that differ from what appears in catalog dumps.

### 1e. Optional second source
Ask if the user has a second source (e.g. an article listing additions/removals).
If yes, use it to cross-reference before touching any code.

> **Important:** Always cross-reference at least two sources before deciding what to
> add or remove. Games that appear to be "missing" from one source may still be in
> the catalog. Never remove a game based on a single source alone.

---

## Step 2 — Determine Exact Changes

From the sources gathered, produce two confirmed lists:

**Removed games** — present in current `index.html` data arrays but absent from the
new catalog. Verify against the official website before removing.

**Added games** — present in the new catalog but absent from `index.html`. For each,
note: name, genre, type (Main catalog = `"games"`, Indie catalog = `"indie"`),
multiplayer tags (`"multi"`, `"coop"`), star rating, review count.

**New monthly games** — the two free-this-month titles. These also appear in the
main catalog arrays (they are regular catalog games that happen to be free this month).

Show the user your confirmed add/remove lists and wait for approval before proceeding.

---

## Step 3 — Update `index.html`

Work through these sections in order. Search for the quoted strings to locate each one.

### 3a. Month tag CSS
Add a new CSS class for the new month tag near the other tag styles.
Search for `.tag-mar-inline` to find the right place.
Pattern to add (replace MAY / may / color as appropriate):
```css
.tag-may, .tag-may-inline { background: rgba(R,G,B,0.85); }
```
Color convention used so far:
- JAN → blue `rgba(59,130,246,0.85)`
- MAR → green `rgba(34,197,94,0.85)`
- APR → purple `rgba(168,85,247,0.85)`
Pick a distinct color for the new month.

### 3b. `tagClass()` function
Search for `if (tag === 'APR') return 'tag-apr';`
Add the new month above or below it:
```js
if (tag === 'MAY') return 'tag-may';
```

### 3c. Filter buttons — month tag rotation
The catalog has **3 month filter buttons max**. Each update, drop the oldest and add
the newest. There are **two sets** of filter buttons to update:
1. The main catalog toolbar (search for `data-cat="APR"` in the toolbar section)
2. The slide-out menu (search for `data-cat="APR"` in the menu section)

In both places: remove the oldest month button, add the new month button.

### 3d. `setCatalogFilter` — `isTag` check
Search for:
```js
const isTag  = val === 'APR' || val === 'MAR' || val === 'JAN';
```
Update to replace the oldest month with the new one:
```js
const isTag  = val === 'MAY' || val === 'APR' || val === 'MAR';
```
**Do not skip this step.** Missing it causes the new month filter button to do nothing
when clicked (this bug bit us on the April update).

### 3e. `syncMenuFilters()`
Search for `b.dataset.cat === 'APR'` inside `syncMenuFilters`.
Update the condition to include the new month and drop the oldest:
```js
} else if (b.dataset.cat === 'MAY' || b.dataset.cat === 'APR' || b.dataset.cat === 'MAR') {
```

### 3f. Legend
Search for `Added April 2026` to find the legend section.
Add a new legend item for the new month, remove the oldest one.

### 3g. Remove departed games
In `gamesData` and `indieData` arrays, delete the entries for removed games.

### 3h. Add new catalog games
In the appropriate array (`gamesData` for Main, `indieData` for Indie), add each new
game with `tag: "MAY"` (or whatever the new month tag is). Use this structure:
```js
{ name: "Game Name", genre: "Genre", tag: "MAY", type: "games", mp: [], rating: 4.5, reviews: 1200 },
```
Keep arrays in alphabetical order by name.

### 3i. Update `monthlyData`
Search for `monthlyData`. Replace the two entries with the new monthly games.
These games must also exist in `gamesData` or `indieData` — they are not added here,
just referenced. Set `isClaimable: true` for both.

### 3j. Update `renderMonthly()`
Search for `renderMonthly`. Update the hardcoded game name array to the two new
monthly titles:
```js
['New Monthly Game 1', 'New Monthly Game 2']
```

### 3k. `MONTHLY_VERSION`
Search for `MONTHLY_VERSION`. Increment to the new month:
```js
const MONTHLY_VERSION = '2026-05';
```
This triggers the monthly section to auto-expand for users on their first visit of
the new month.

### 3l. Hero art map
Search for `const heroArt =` (or similar). 
- Remove entries for departed games.
- Add entries for all new games pointing to files that don't exist yet:
  ```js
  'Game Name': 'hero_art/game-name.jpg',
  ```
- Update the monthly sub-map (two entries) to the new monthly game names.

### 3m. `APP_IDS`
- Remove entries for departed games.
- Add entries for all new games. Look up each ID at:
  `https://www.meta.com/experiences/[game-slug]/`
  The numeric ID is in the URL.
- If an ID can't be found, omit the entry — the app falls back to a Meta search URL.

### 3n. Update counts and month references
Search for each of these and update to the new month/count:
- `stat-total` — total game count (e.g. "102 games")
- `header-sub` — subtitle line (e.g. "102 games · April 2026")
- `show-label` — label above the free monthly section
- Footer meta tag — `content="102 games"`
- Canvas `fillText` — month/year string drawn on the share image
- Page `<title>` and OG meta tags — title and description
- `CLAIM DEADLINE` — search for `CLAIM DEADLINE` and update to the last day of the
  new month (e.g. `April 30, 2026` → `May 31, 2026`)

To get the new total count: count all entries across `gamesData` + `indieData` +
`monthlyData` (monthly games that are not already in the other arrays).

---

## Step 4 — Update Art Workflow Tools

These three files in `tools/` need to reflect the new month's games only.

### `tools/generate_atlas.py`
Update `CATALOG_GAMES` to the full list of all new games this month (catalog +
monthly combined, sorted alphabetically). Update `CLAIMABLE` to the two new monthly
game names.

### `tools/extract_atlas.py`
Update `CATALOG_GAMES` to match the same full list as above (sorted alphabetically).
Order matters — it must match the atlas layout order exactly.

### `tools/art_search.html`
Update the game list to the new games only, with correct search mode hints
(`'plain'` or `'vr'` per game). Update the header count.

---

## Step 5 — Generate Art Templates and Paint New Art

```
cd tools
python generate_atlas.py
```

This requires Playwright to be installed:
```
pip install playwright pillow
python -m playwright install chromium
```

Output goes to `tools/atlas_output/`:
- `atlas_catalog_01_ui.png` — transparent overlay to use in GIMP
- `atlas_catalog_01_mask*.png` — cell masks
- `atlas_output/place_holders/` — placeholder JPGs for reference

**GIMP workflow for each atlas:**
1. File → New → 920×300px canvas
2. File → Open as Layers → `atlas_catalog_01_ui.png` (goes on top)
3. Paint art on a layer below the overlay
   - Dark shaded wings = mobile crop zone (~45px each side)
   - Gold dashed line = exact mobile safe boundary — keep key content inside
4. Hide the overlay layer → Flatten → Export as `atlas_catalog_01_done.png`
   (place in `tools/atlas_output/`)
5. Use `tools/art_search.html` in a browser to find reference art for each game

Once all atlas pages are painted:
```
python extract_atlas.py
```
This slices the done PNGs into individual `hero_art/*.jpg` files.

All card art is 920×300px regardless of whether the game is a monthly title or
regular catalog game — they use the same format.

---

## Step 6 — Verify Before Committing

Open `index.html` directly in a browser and check:

- [ ] New month filter button is visible and works (filters to new games only)
- [ ] Old month filter button (3 months ago) is gone
- [ ] Removed games no longer appear in any section
- [ ] New games appear with the correct month tag badge
- [ ] Monthly section shows the correct two free games with "FREE THIS MONTH" badge
- [ ] Store buttons on new game cards open the correct Meta store page
- [ ] Hero art loads for all new cards (no broken image placeholders)
- [ ] Game count in the header matches the actual number of cards
- [ ] Monthly section auto-expands on first load (clear localStorage to test:
      `localStorage.clear()` in browser console, then reload)

---

## Step 7 — Commit and Push

```
git add index.html tools/generate_atlas.py tools/extract_atlas.py tools/art_search.html
git add hero_art/<all new art files>
git commit -m "May 2026 catalog update — X games, new monthly redeemables, art tools"
git push
```

---

## Reference: File Map

| What | Where |
|------|-------|
| All game data | `index.html` — `gamesData`, `indieData`, `monthlyData` arrays |
| Monthly version key | `index.html` — `const MONTHLY_VERSION` |
| Hero art paths | `index.html` — `const heroArt` object |
| Store deep links | `index.html` — `const APP_IDS` object |
| Tag CSS | `index.html` — `.tag-xxx` and `.tag-xxx-inline` styles |
| Filter buttons | `index.html` — two sets: toolbar + slide-out menu |
| Filter logic | `index.html` — `setCatalogFilter()`, `syncMenuFilters()`, `tagClass()` |
| Art overlay generator | `tools/generate_atlas.py` |
| Art atlas slicer | `tools/extract_atlas.py` |
| Art reference search | `tools/art_search.html` |
| Hero art images | `hero_art/*.jpg` |
| GIMP source file | `card_art_generator.xcf` |
