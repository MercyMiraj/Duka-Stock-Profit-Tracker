import sqlite3
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
DB_NAME = "inventory.db"


def get_db():
  conn = sqlite3.connect(DB_NAME)
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  with get_db() as conn:
    conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                buying_price REAL NOT NULL,
                selling_price REAL NOT NULL,
                quantity INTEGER NOT NULL
            )
        """)


@app.route("/")
def index():
  with get_db() as conn:
    products = conn.execute(
        "SELECT * FROM products ORDER BY quantity ASC"
    ).fetchall()

  total_cost = sum(p["buying_price"] * p["quantity"] for p in products)
  expected_revenue = sum(p["selling_price"] * p["quantity"] for p in products)
  expected_profit = expected_revenue - total_cost
  low_stock_count = sum(1 for p in products if p["quantity"] <= 5)

  return render_template(
      "index.html",
      products=products,
      total_cost=total_cost,
      expected_profit=expected_profit,
      low_stock_count=low_stock_count,
  )


@app.route("/add", methods=["POST"])
def add_product():
  name = request.form["name"].strip()
  category = request.form["category"].strip()
  buying_price = float(request.form["buying_price"])
  selling_price = float(request.form["selling_price"])
  quantity = int(request.form["quantity"])

  with get_db() as conn:
    conn.execute(
        "INSERT INTO products (name, category, buying_price, selling_price,"
        " quantity) VALUES (?, ?, ?, ?, ?)",
        (name, category, buying_price, selling_price, quantity),
    )
  return redirect(url_for("index"))


@app.route("/update/<int:product_id>/<action>", methods=["POST"])
def update_stock(product_id, action):
  with get_db() as conn:
    if action == "sell":
      conn.execute(
          "UPDATE products SET quantity = MAX(0, quantity - 1) WHERE id = ?",
          (product_id,),
      )
    elif action == "restock":
      conn.execute(
          "UPDATE products SET quantity = quantity + 1 WHERE id = ?",
          (product_id,),
      )
    elif action == "delete":
      conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
  return redirect(url_for("index"))


if __name__ == "__main__":
  init_db()
  app.run(debug=True)
