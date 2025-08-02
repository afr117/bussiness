#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import timedelta
import json
import os
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production
app.permanent_session_lifetime = timedelta(hours=1)

PRODUCTS_FILE = 'products.json'
ADMIN_PASSWORD = 'admin123'
SESSION_TIMEOUT = 3600  # 1 hour in seconds

def load_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_products(products):
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(products, f, indent=4)

def is_session_expired():
    login_time = session.get('login_time')
    return not login_time or time.time() - login_time > SESSION_TIMEOUT

@app.route('/')
def home():
    products = load_products()
    search = request.args.get('search', '').lower()
    selected_category = request.args.get('category', '')

    filtered_products = [
        p for p in products
        if (not search or search in p['name'].lower()) and
           (not selected_category or p['category'] == selected_category)
    ]

    categories = sorted(set(p.get('category', '') for p in products if p.get('category')))
    return render_template('index.html', products=filtered_products,
                           search=search, selected_category=selected_category,
                           categories=categories)

@app.route('/alt')
def alt_page():
    return render_template('alt.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['login_time'] = time.time()
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Invalid password')
    else:
        if session.get('logged_in') and not is_session_expired():
            return redirect(url_for('admin_panel'))
        session.clear()
        return render_template('admin_login.html')

@app.route('/admin/panel')
def admin_panel():
    if not session.get('logged_in') or is_session_expired():
        session.clear()
        return redirect(url_for('admin'))
    products = load_products()
    categories = sorted(set(p.get('category', '') for p in products if p.get('category')))
    return render_template('admin_panel.html', products=products, categories=categories)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin'))

@app.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('logged_in') or is_session_expired():
        session.clear()
        return redirect(url_for('admin'))

    products = load_products()

    image_file = request.files.get("image")
    image_filename = ''
    if image_file and image_file.filename:
        upload_path = os.path.join('static', 'uploads')
        os.makedirs(upload_path, exist_ok=True)
        image_filename = os.path.join('uploads', image_file.filename)
        image_file.save(os.path.join('static', image_filename))

    new_product = {
        "name": request.form.get("name"),
        "price": float(request.form.get("price", 0)),
        "image": f"/static/{image_filename}" if image_filename else "",
        "description": request.form.get("description"),
        "phone": request.form.get("phone", ""),
        "category": request.form.get("category")
    }

    products.append(new_product)
    save_products(products)
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete/<int:index>', methods=['POST'])
def delete_product(index):
    if not session.get('logged_in') or is_session_expired():
        session.clear()
        return redirect(url_for('admin'))

    products = load_products()
    if 0 <= index < len(products):
        products.pop(index)
        save_products(products)
    return redirect(url_for('admin_panel'))

@app.route('/admin/edit/<int:index>', methods=['POST'])
def edit_product(index):
    if not session.get('logged_in') or is_session_expired():
        session.clear()
        return redirect(url_for('admin'))

    products = load_products()
    if 0 <= index < len(products):
        products[index] = {
            "name": request.form.get("name"),
            "price": float(request.form.get("price", 0)),
            "image": request.form.get("image"),
            "description": request.form.get("description"),
            "phone": request.form.get("phone", ""),
            "category": request.form.get("category")
        }
        save_products(products)
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)
