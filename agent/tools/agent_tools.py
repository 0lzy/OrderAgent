"""Agent 的知识库检索和订单查询工具。"""

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from langchain.tools import ToolRuntime, tool

from rag.rag_service import RagSummarizeService
from utils.path_tool import get_abs_path

RETAIL_DATABASE_URI = Path(get_abs_path("data/retail/retail.sqlite3")).as_uri() + "?mode=ro"


@dataclass
class OrderContext:
    user_id: str


rag = RagSummarizeService()


@tool(description="从向量存储中检索参考资料")
def rag_summarize(query: str) -> str:
    """根据知识库资料生成摘要。"""
    return rag.rag_summarize(query)


@tool(description=(
    "当用户想查看自己的订单列表，或找不到订单号、需要从自己的订单中选择时调用。"
    "无需传入参数，工具从会话上下文读取当前用户，返回该用户的订单号和订单状态。"
    "用户选定某笔订单后，可调用 get_order 查看该订单的商品明细。"
))
def list_my_orders(runtime: ToolRuntime[OrderContext]) -> list[dict[str, str]] | str:
    if runtime.context is None or not runtime.context.user_id:
        return "请先在侧边栏填写模拟用户 ID。"

    with closing(sqlite3.connect(RETAIL_DATABASE_URI, uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        orders = conn.execute("""
            SELECT order_id, status
            FROM orders
            WHERE user_id = ?
            ORDER BY order_id
        """, (runtime.context.user_id,)).fetchall()

    return [dict(order) for order in orders]


@tool(description=(
    "当用户询问某笔订单的状态、是否已签收或买了哪些商品时调用。"
    "传入完整订单号 order_id（例如 #W1023987）。"
    "工具按当前会话核对订单归属，返回订单状态及商品名称、规格和价格。"
    "查不到时返回提示。"
))
def get_order(order_id: str, runtime: ToolRuntime[OrderContext]) -> dict | str:
    if runtime.context is None or not runtime.context.user_id:
        return "请先在侧边栏填写模拟用户 ID。"

    order_id = order_id.strip()
    user_id = runtime.context.user_id
    with closing(sqlite3.connect(RETAIL_DATABASE_URI, uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("BEGIN")  # 两次查询读取同一个数据库快照。

        order = conn.execute("""
            SELECT order_id, user_id, status
            FROM orders
            WHERE order_id = ? AND user_id = ?
        """, (order_id, user_id)).fetchone()

        if order is None:
            return "查不到这笔订单。"

        item_rows = conn.execute("""
            SELECT line_no, item_id, product_id, name, price_cents, options_json
            FROM order_items
            WHERE order_id = ?
            ORDER BY line_no
        """, (order_id,)).fetchall()

    items = []
    for row in item_rows:
        item = dict(row)
        item["options"] = json.loads(item.pop("options_json"))
        items.append(item)

    result = dict(order)
    result["items"] = items
    return result
