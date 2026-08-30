"""Database tool.

Actions: query, insert, create_table, list_tables, backup
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class DatabaseTool(BaseTool):
    metadata = ToolMetadata(
        name="database",
        description="Database operations: query, insert, create tables, backup",
        version="1.0.0",
        author="Jarvis",
        actions=["query", "insert", "create_table", "list_tables", "backup"],
        permissions=["database.read", "database.write"],
        tags=["database", "sql", "sqlite", "postgres"],
    )

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(f"Unsupported action: {action}").to_dict()

        try:
            if action == "query":
                return self._query(kwargs)

            if action == "insert":
                return self._insert(kwargs)

            if action == "create_table":
                return self._create_table(kwargs)

            if action == "list_tables":
                return self._list_tables(kwargs)

            if action == "backup":
                return self._backup(kwargs)

        except Exception as exc:
            return ToolResult.fail(str(exc)).to_dict()

        return ToolResult.fail(f"Unhandled action: {action}").to_dict()

    def _get_connection(self, kwargs):
        db_path = kwargs.get("path") or kwargs.get("database") or kwargs.get("db_path", ":memory:")
        import sqlite3
        return sqlite3.connect(db_path)

    def _query(self, kwargs) -> dict:
        sql = kwargs.get("sql") or kwargs.get("query")
        if not sql:
            return ToolResult.fail("SQL query is required").to_dict()
        with self._get_connection(kwargs) as conn:
            cursor = conn.execute(sql)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            return ToolResult.ok(output={"columns": columns, "rows": rows}).to_dict()

    def _insert(self, kwargs) -> dict:
        table = kwargs.get("table")
        data = kwargs.get("data", {})
        if not table or not data:
            return ToolResult.fail("Table and data are required").to_dict()
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        with self._get_connection(kwargs) as conn:
            conn.execute(sql, list(data.values()))
            conn.commit()
        return ToolResult.ok(output=f"Inserted into {table}").to_dict()

    def _create_table(self, kwargs) -> dict:
        table = kwargs.get("table")
        schema = kwargs.get("schema") or kwargs.get("columns")
        if not table or not schema:
            return ToolResult.fail("Table name and schema are required").to_dict()
        if isinstance(schema, list):
            schema_sql = ", ".join(schema)
        else:
            schema_sql = str(schema)
        sql = f"CREATE TABLE IF NOT EXISTS {table} ({schema_sql})"
        with self._get_connection(kwargs) as conn:
            conn.execute(sql)
            conn.commit()
        return ToolResult.ok(output=f"Created table: {table}").to_dict()

    def _list_tables(self, kwargs) -> dict:
        with self._get_connection(kwargs) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
        return ToolResult.ok(output=tables).to_dict()

    def _backup(self, kwargs) -> dict:
        src = kwargs.get("source") or kwargs.get("path") or ":memory:"
        dest = kwargs.get("destination")
        if not dest:
            return ToolResult.fail("Destination path is required").to_dict()
        import shutil
        shutil.copy2(src, dest)
        return ToolResult.ok(output=dest, artifacts=[dest]).to_dict()
