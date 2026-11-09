import json
import sqlite3
from contextlib import closing
from decimal import Decimal
from pathlib import Path


def main():
    retail_dir = Path(__file__).resolve().parent / "data" / "retail"
    with (retail_dir / "db.json").open(encoding="utf-8") as file:
        source = json.load(file, parse_float=Decimal)

    order_rows = []
    item_rows = []

    for order in source["orders"].values():
        order_id = order["order_id"]
        order_rows.append((order_id, order["user_id"], order["status"]))

        for line_no, item in enumerate(order["items"], start=1):
            item_rows.append((
                order_id,
                line_no,
                item["item_id"],
                item["product_id"],
                item["name"],
                int(item["price"] * 100),
                json.dumps(item["options"], ensure_ascii=False),
            ))

    database_path = retail_dir / "retail.sqlite3"

    with closing(sqlite3.connect(database_path)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        with conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY NOT NULL,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    order_id TEXT NOT NULL REFERENCES orders(order_id),
                    line_no INTEGER NOT NULL,
                    item_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    price_cents INTEGER NOT NULL,
                    options_json TEXT NOT NULL,
                    PRIMARY KEY (order_id, line_no)
                )
            """)

            if conn.execute("SELECT 1 FROM orders LIMIT 1").fetchone():
                print("订单已经导入，本次跳过。")
                return

            conn.executemany(
                "INSERT INTO orders (order_id, user_id, status) VALUES (?, ?, ?)",
                order_rows,
            )
            conn.executemany("""
                INSERT INTO order_items (
                    order_id, line_no, item_id, product_id,
                    name, price_cents, options_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, item_rows)

    print(f"已导入 {len(order_rows)} 笔订单、{len(item_rows)} 条商品明细。")
    print(f"数据库文件：{database_path}")


if __name__ == "__main__":
    main()
