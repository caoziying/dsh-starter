"""Minimal deterministic Python MCP server."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("diagnostics")


@mcp.tool()
def probe_echo(text: str) -> dict[str, str]:
    """Return text unchanged and mark the result as a Python MCP response."""
    if not text or len(text) > 1000:
        raise ValueError("text must contain 1–1000 characters")
    return {"echo": text, "source": "python-mcp"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
