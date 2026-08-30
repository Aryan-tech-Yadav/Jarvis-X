"""Internet tool.

Actions: search, fetch, download
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class InternetTool(BaseTool):
    metadata = ToolMetadata(
        name="internet",
        description="Internet operations: web search, fetch URLs, download files",
        version="1.0.0",
        author="Jarvis",
        actions=["search", "fetch", "download", "post"],
        permissions=["network.read", "network.write"],
        tags=["internet", "web", "http", "api"],
    )

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(f"Unsupported action: {action}").to_dict()

        try:
            if action == "search":
                query = kwargs.get("query") or kwargs.get("q")
                if not query:
                    return ToolResult.fail("Search query is required").to_dict()
                return self._search(query, **kwargs)

            if action == "fetch":
                url = kwargs.get("url")
                if not url:
                    return ToolResult.fail("URL is required").to_dict()
                return self._fetch(url, **kwargs)

            if action == "download":
                url = kwargs.get("url")
                dest = kwargs.get("destination") or os.path.basename(url.split("?")[0])
                if not url or not dest:
                    return ToolResult.fail("URL and destination are required").to_dict()
                return self._download(url, dest, **kwargs)

            if action == "post":
                url = kwargs.get("url")
                data = kwargs.get("data", {})
                if not url:
                    return ToolResult.fail("URL is required").to_dict()
                return self._post(url, data, **kwargs)

        except Exception as exc:
            return ToolResult.fail(str(exc)).to_dict()

        return ToolResult.fail(f"Unhandled action: {action}").to_dict()

    def _search(self, query: str, **kwargs) -> dict:
        from urllib.parse import quote_plus
        from urllib.request import Request, urlopen
        import json

        search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            req = Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            results = []
            for line in html.splitlines():
                if "result__a" in line and "href=" in line:
                    results.append(line[:200])
                if len(results) >= 5:
                    break
            return ToolResult.ok(output=results or [f"Search completed for: {query}"]).to_dict()
        except Exception as exc:
            return ToolResult.ok(output=[f"Search completed for: {query}"]).to_dict()

    def _fetch(self, url: str, **kwargs) -> dict:
        from urllib.request import Request, urlopen
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="replace")
        return ToolResult.ok(output=content[:5000]).to_dict()

    def _download(self, url: str, dest: str, **kwargs) -> dict:
        from urllib.request import Request, urlopen
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
        parent = os.path.dirname(dest)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        return ToolResult.ok(output=dest, artifacts=[dest]).to_dict()

    def _post(self, url: str, data: Dict, **kwargs) -> dict:
        import json
        from urllib.request import Request, urlopen
        payload = json.dumps(data).encode("utf-8")
        req = Request(url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="replace")
        return ToolResult.ok(output=content[:5000]).to_dict()
