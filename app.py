import os
import json
from datetime import datetime, timedelta
from uuid import uuid4
from werkzeug.utils import secure_filename
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash
)

# --- App setup ---
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_FILE = os.path.join(BASE_DIR, "products.json")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Admin credentials
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password")
SESSION_TTL = timedelta(hours=1)

# --- Category presets (top links + dropdowns) ---
PRESET_CATEGORIES = [
    "Buy Parts",
    "Wheels & Tires",
    "Electrical Components",
    "Interior Parts",
]

# -------- Helpers --------
def load_products():
    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_products(items):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)

def _s(v):
    return str(v).strip().lower() if v is not None else ""

def filter_products(items, year=None, make=None, model=None, category=None):
    """Filter by exact category + Y/M/M. Falls back to text search if keys missing."""
    yq = str(year).strip() if year else ""
    mq = make.strip() if make else ""
    mdq = model.strip() if model else ""
    cq = category.strip() if category else ""

    out = []
    for p in items:
        if cq and _s(p.get("category")) != _s(cq):
            continue

        hay = f"{p.get('name','')} {p.get('description','')} {p.get('make','')} {p.get('model','')} {p.get('year','')}"

        if yq:
            if "year" in p and str(p.get("year")) != yq:
                continue
            if "year" not in p and yq not in hay:
                continue

        if mq:
            if p.get("make") and _s(p.get("make")) != _s(mq):
                continue
            if not p.get("make") and _s(mq) not in _s(hay):
                continue

        if mdq:
            if p.get("model") and _s(p.get("model")) != _s(mdq):
                continue
            if not p.get("model") and _s(mdq) not in _s(hay):
                continue

        out.append(p)
    return out

def compute_categories(products):
    found = sorted({p.get("category","") for p in products if p.get("category")})
    return PRESET_CATEGORIES + [c for c in found if c and c not in PRESET_CATEGORIES]

def login_ok():
    if not session.get("admin"):
        return False
    last = session.get("last_activity")
    if not last:
        return False
    try:
        last_dt = datetime.fromisoformat(last)
    except ValueError:
        return False
    if datetime.utcnow() - last_dt > SESSION_TTL:
        session.clear()
        return False
    session["last_activity"] = datetime.utcnow().isoformat()
    return True

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"png","jpg","jpeg","webp","gif"}

# -------- Routes --------
@app.route("/", methods=["GET"])
def home():
    products = load_products()
    year = request.args.get("year", "")
    make = request.args.get("make", "")
    model = request.args.get("model", "")
    category = request.args.get("category", "")

    filtered = filter_products(products, year=year, make=make, model=model, category=category)
    return render_template(
        "index.html",
        products=filtered,
        categories=compute_categories(products),
        selected_category=category
    )

@app.route("/alt", methods=["GET"])
def alt_page():
    products = load_products()
    category = request.args.get("category", "")
    year = request.args.get("year", "")
    make = request.args.get("make", "")
    model = request.args.get("model", "")

    filtered = filter_products(products, year=year, make=make, model=model, category=category)
    return render_template(
        "alt.html",
        products=filtered,
        categories=compute_categories(products),
        selected_category=category
    )

# ---- Admin/auth ----
@app.route("/admin", methods=["GET"])
def admin():
    if not login_ok():
        return redirect(url_for("admin_login"))
    products = load_products()
    return render_template("admin_panel.html", products=products, categories=compute_categories(products))

@app.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            session["last_activity"] = datetime.utcnow().isoformat()
            return redirect(url_for("admin"))
        flash("Invalid credentials", "error")
    return render_template("admin_login.html")

@app.route("/admin_logout", methods=["GET"])
def admin_logout():
    session.clear()
    return redirect(url_for("home"))

# ---- Product management ----
@app.route("/add", methods=["POST"])
def add_product():
    if not login_ok():
        return redirect(url_for("admin_login"))

    products = load_products()

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    price_raw = request.form.get("price", "").strip()
    category = request.form.get("category", "").strip()

    year_raw = request.form.get("year", "").strip()
    make = request.form.get("make", "").strip()
    model = request.form.get("model", "").strip()

    # normalize types
    price = 0.0
    if price_raw:
        try: price = float(price_raw)
        except ValueError: price = 0.0

    year_val = ""
    if year_raw:
        try: year_val = int(year_raw)
        except ValueError: year_val = year_raw  # keep as string if non-numeric

    # upload image
    image_url = ""
    file = request.files.get("image")
    if file and file.filename and allowed_file(file.filename):
        fname = secure_filename(file.filename)
        root, ext = os.path.splitext(fname)
        final = f"{root}_{uuid4().hex[:8]}{ext}"
        file.save(os.path.join(UPLOAD_FOLDER, final))
        image_url = f"/static/uploads/{final}"

    # ALWAYS include year/make/model keys so they’re saved alongside product data
    prod = {
        "name": name,
        "description": description,
        "price": price,
        "category": category,
        "image": image_url,
        "year": year_val,
        "make": make,
        "model": model
    }

    products.append(prod)
    save_products(products)
    flash("Product added.", "success")
    return redirect(url_for("admin"))

@app.route("/delete/<int:index>", methods=["POST"])
def delete_product(index):
    if not login_ok():
        return redirect(url_for("admin_login"))

    products = load_products()
    if 0 <= index < len(products):
        img = products[index].get("image", "")
        if img and img.startswith("/static/uploads/"):
            try:
                os.remove(os.path.join(BASE_DIR, img.lstrip("/")))
            except OSError:
                pass
        products.pop(index)
        save_products(products)
        flash("Product deleted.", "success")
    else:
        flash("Invalid index.", "error")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
