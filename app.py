from datetime import datetime
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
    conn.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                sale_price REAL NOT NULL,
                profit REAL NOT NULL,
                sold_at TEXT NOT NULL
            )
        """)


@app.route("/")
def index():
  today_str = datetime.now().strftime("%Y-%m-%d")

  with get_db() as conn:
    products = conn.execute(
        "SELECT * FROM products ORDER BY quantity ASC"
    ).fetchall()

    recent_sales = conn.execute(
        "SELECT * FROM sales ORDER BY id DESC LIMIT 10"
    ).fetchall()

    today_stats = conn.execute(
        """
            SELECT 
                COALESCE(SUM(sale_price), 0) AS revenue,
                COALESCE(SUM(profit), 0) AS profit
            FROM sales
            WHERE sold_at LIKE ?
            """,
        (f"{today_str}%",),
    ).fetchone()

  total_cost = sum(p["buying_price"] * p["quantity"] for p in products)
  expected_revenue = sum(p["selling_price"] * p["quantity"] for p in products)
  expected_profit = expected_revenue - total_cost
  low_stock_count = sum(1 for p in products if p["quantity"] <= 5)

  return render_template(
      "index.html",
      products=products,
      recent_sales=recent_sales,
      total_cost=total_cost,
      expected_profit=expected_profit,
      low_stock_count=low_stock_count,
      today_revenue=today_stats["revenue"],
      today_profit=today_stats["profit"],
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
      product = conn.execute(
          "SELECT * FROM products WHERE id = ?", (product_id,)
      ).fetchone()

      if product and product["quantity"] > 0:
        profit = product["selling_price"] - product["buying_price"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn.execute(
            "UPDATE products SET quantity = quantity - 1 WHERE id = ?",
            (product_id,),
        )
        conn.execute(
            "INSERT INTO sales (product_name, sale_price, profit, sold_at)"
            " VALUES (?, ?, ?, ?)",
            (product["name"], product["selling_price"], profit, timestamp),
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
