#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, session, url_for
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this for security in production

PRODUCTS_FILE = 'products.json'
ADMIN_PASSWORD = 'admin123'

def load_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_products(products):
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(products, f, indent=4)

@app.route('/')
def home():
    products = load_products()
    return render_template('index.html', products=products)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Invalid password')
    else:
        if session.get('logged_in'):
            return redirect(url_for('admin_panel'))
        return render_template('admin_login.html')

@app.route('/admin/panel')
def admin_panel():
    if not session.get('logged_in'):
        return redirect(url_for('admin'))
    products = load_products()
    return render_template('admin_panel.html', products=products)

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin'))

@app.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('logged_in'):
        return redirect(url_for('admin'))
    products = load_products()
    new_product = {
        "name": request.form.get("name"),
        "image": request.form.get("image"),
        "description": request.form.get("description"),
        "phone": request.form.get("phone"),
        "category": request.form.get("category")
    }
    products.append(new_product)
    save_products(products)
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete/<int:index>', methods=['POST'])
def delete_product(index):
    if not session.get('logged_in'):
        return redirect(url_for('admin'))
    products = load_products()
    if 0 <= index < len(products):
        products.pop(index)
        save_products(products)
    return redirect(url_for('admin_panel'))

@app.route('/admin/edit/<int:index>', methods=['POST'])
def edit_product(index):
    if not session.get('logged_in'):
        return redirect(url_for('admin'))
    products = load_products()
    if 0 <= index < len(products):
        products[index] = {
            "name": request.form.get("name"),
            "image": request.form.get("image"),
            "description": request.form.get("description"),
            "phone": request.form.get("phone"),
            "category": request.form.get("category")
        }
        save_products(products)
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)
