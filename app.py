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
            # ensure list
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_products(items):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)

def _s(v):
    return str(v).strip().lower() if v is not None else ""

def filter_products(items, year=None, make=None, model=None, category=None):
    """Filter by exact category match if provided and by Y/M/M fields when present.
       Falls back to simple text search if fields aren’t in the JSON."""
    yq = str(year).strip() if year else ""
    mq = make.strip() if make else ""
    mdq = model.strip() if model else ""
    cq = category.strip() if category else ""

    out = []
    for p in items:
        # category
        if cq and _s(p.get("category")) != _s(cq):
            continue

        # text haystack for fallback
        hay = f"{p.get('name','')} {p.get('description','')} {p.get('make','')} {p.get('model','')} {p.get('year','')}"

        # year
        if yq:
            if "year" in p and str(p.get("year")) != yq:
                continue
            if "year" not in p and yq not in hay:
                continue

        # make
        if mq:
            if p.get("make") and _s(p.get("make")) != _s(mq):
                continue
            if not p.get("make") and _s(mq) not in _s(hay):
                continue

        # model
        if mdq:
            if p.get("model") and _s(p.get("model")) != _s(mdq):
                continue
            if not p.get("model") and _s(mdq) not in _s(hay):
                continue

        out.append(p)
    return out

def compute_categories(products):
    found = sorted({p.get("category","") for p in products if p.get("category")})
    merged = PRESET_CATEGORIES + [c for c in found if c and c not in PRESET_CATEGORIES]
    return merged

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
    # refresh TTL "touch"
    session["last_activity"] = datetime.utcnow().isoformat()
    return True

def require_login():
    if not login_ok():
        return redirect(url_for("admin_login"))

ALLOWED_EXT = {"png","jpg","jpeg","webp","gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

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
    return render_template(
        "admin_panel.html",
        products=products,
        categories=compute_categories(products)
    )

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
    price = float(request.form.get("price", 0) or 0)
    category = request.form.get("category", "").strip()
    make = request.form.get("make", "").strip() if "make" in request.form else ""
    model = request.form.get("model", "").strip() if "model" in request.form else ""
    year = request.form.get("year", "").strip() if "year" in request.form else ""

    # default image path None
    image_url = ""

    file = request.files.get("image")
    if file and file.filename and allowed_file(file.filename):
        fname = secure_filename(file.filename)
        # de-conflict name
        name_part, ext = os.path.splitext(fname)
        final = f"{name_part}_{uuid4().hex[:8]}{ext}"
        file.save(os.path.join(UPLOAD_FOLDER, final))
        image_url = f"/static/uploads/{final}"

    prod = {
        "name": name,
        "description": description,
        "price": price,
        "category": category,
        "image": image_url
    }
    # optional fields if present
    if year: prod["year"] = year
    if make: prod["make"] = make
    if model: prod["model"] = model

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
        # try to remove image file if it lives under /static/uploads
        img = products[index].get("image", "")
        if img and img.startswith("/static/uploads/"):
            path = os.path.join(BASE_DIR, img.lstrip("/"))
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        products.pop(index)
        save_products(products)
        flash("Product deleted.", "success")
    else:
        flash("Invalid index.", "error")
    return redirect(url_for("admin"))

# ------------- Run -------------
if __name__ == "__main__":
    # Enable reloader for local dev
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
