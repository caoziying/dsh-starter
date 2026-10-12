"""Exercise the real MCP transport and local FastAPI service without an LLM."""

from __future__ import annotations

import asyncio
import argparse
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


async def call(server: str, tool: str, arguments: dict) -> dict:
    script = ROOT / "harness" / "tools" / server / "server.py"
    params = StdioServerParameters(command=sys.executable, args=[str(script)])
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            registered = {item.name for item in (await session.list_tools()).tools}
            if tool not in registered:
                raise AssertionError(f"{tool} missing from {server}: {registered}")
            result = await session.call_tool(tool, arguments)
            if result.isError:
                raise AssertionError(f"{tool} failed: {result.content}")
            if result.structuredContent:
                return result.structuredContent
            return json.loads(result.content[0].text)


async def main(online: bool = False) -> None:
    echo = await call("diagnostics", "probe_echo", {"text": "SKILL_MCP_OK"})
    assert echo["echo"] == "SKILL_MCP_OK" and echo["source"] == "python-mcp", echo
    stats = await call("sequence", "sequence_analyze", {"sequence": "ACDEFGHIKLMNPQRSTVWY"})
    assert stats["length"] == 20 and sum(stats["amino_acid_counts"].values()) == 20, stats
    if online:
        fasta = await call("uniprot", "uniprot_get_fasta", {"entry": "A5PLL7"})
        assert fasta["accession"] == "A5PLL7" and fasta["length"] > 0, fasta
    print(json.dumps({"passed": True, "mcp_tools": ["probe_echo", "sequence_analyze"],
                      "sequence_length": stats["length"], "online_checked": online}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--online", action="store_true", help="Also call UniProt REST")
    asyncio.run(main(parser.parse_args().online))
