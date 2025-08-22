# Recycled Auto Parts / Local Product Catalog (Flask)

![Homepage screenshot](docs/screenshot-bussiness.png)

A clean, small-business–friendly catalog app where non-coders can add, edit, and publish products in minutes. It’s built with Flask + Jinja templates and stores items in `products.json`, with images under `static/uploads`. There’s an admin panel with session login and a mirrored alternate landing page (`alt.html`). The UI uses a three-row header (title, quick links, controls bar) and a responsive product grid with a blended background image for a “market stall” feel.

## Why this exists (the story)
I built this for mom-and-pop shops that need a site they can actually maintain without a developer or a CMS learning curve. No database admin, no plugin maze—just JSON + images. The goal: “update a product in under a minute.”

## Features (implemented)
- Admin CRUD for products (title, price, description, image, category)
- Image upload to `static/uploads`
- Category filtering + search
- Alternate landing page (`alt.html`) mirroring layout
- Session-based admin login (1-hour timeout)
- PWA-ready (manifest + service worker stubs)

## Roadmap (next)
- CSV/Excel bulk import & export
- Drag-and-drop image reordering and cropping
- Full offline cache and install banner (PWA)
- Electron desktop wrapper for in-store kiosk
- Role-based access (viewer/editor/admin)

## Quickstart
```bash
# 1) Clone
git clone https://github.com/afr117/bussiness.git
cd bussiness

# 2) Create a venv
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows
# .venv\Scripts\activate

# 3) Install deps
pip install -r requirements.txt

# 4) Run
python app.py
Visit http://localhost:5000
Admin: http://localhost:5000/admin (change the default password in config!)

Project structure
pgsql
Copy
Edit
app.py
products.json
static/
  uploads/
  icons/
  scripts/
  styles/
templates/
  index.html
  alt.html
  admin/*.html
Screenshots
docs/screenshot-bussiness.png – homepage with header bars and product grid
(Replace this file with your own screenshot.)

Hardest challenges
Keeping the three header bars pixel-aligned across breakpoints

Preventing stale cached images after uploads

Balancing simplicity (JSON storage) with safe concurrent edits

Developer
I’m Alfred Figueroa—full-stack & ML developer based in Tulsa. I like shipping pragmatic tools for small teams.

LinkedIn: https://www.linkedin.com/in/alfred-figueroa-rosado-10b010208

Twitter/X: https://twitter.com/your_handle

Portfolio Project repo: https://github.com/afr117/portfolio

bash
Copy
Edit
