"""MCP adapter for the independent local FastAPI example service."""

import json
import os
import urllib.error
import urllib.request

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("sequence")


@mcp.tool()
def sequence_analyze(sequence: str) -> dict:
    """Return deterministic length and amino-acid counts for one protein sequence."""
    if not sequence or len(sequence) > 12_000:
        raise ValueError("sequence must contain 1–12000 characters")
    base_url = os.getenv("SEQUENCE_API_URL", "http://127.0.0.1:8015").rstrip("/")
    request = urllib.request.Request(
        base_url + "/analyze",
        data=json.dumps({"sequence": sequence}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise ValueError(f"Sequence API rejected input (HTTP {exc.code}): {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Sequence API unavailable at {base_url}; run start.ps1") from exc


if __name__ == "__main__":
    mcp.run(transport="stdio")
