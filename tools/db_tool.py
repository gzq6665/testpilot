# -*- coding: utf-8 -*-
"""MySQL 查询工具：用于测试后的数据核对（前后端数据一致性验证）。"""
import json

from langchain_core.tools import tool

from config import MYSQL_CONFIG


@tool
def db_query(sql: str) -> str:
    """执行只读 SQL 查询（仅允许 SELECT），用于核对业务数据。返回查询结果 JSON。

    Args:
        sql: 要执行的 SELECT 语句。
    """
    if not sql.strip().lower().startswith("select"):
        return "出于安全考虑，仅允许执行 SELECT 查询"
    if not MYSQL_CONFIG.get("database"):
        return "MySQL 未配置（config.py 中 MYSQL_CONFIG.database 为空），跳过数据库核对"
    try:
        import pymysql

        conn = pymysql.connect(
            host=MYSQL_CONFIG["host"], port=MYSQL_CONFIG["port"],
            user=MYSQL_CONFIG["user"], password=MYSQL_CONFIG["password"],
            database=MYSQL_CONFIG["database"], charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor, connect_timeout=5,
        )
        with conn, conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchmany(20)
        return json.dumps(rows, ensure_ascii=False, default=str)
    except Exception as e:
        return f"数据库查询失败: {type(e).__name__}: {e}"
