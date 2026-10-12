"""Preflight checks with actionable errors and no secret-value output."""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from launcher import CONFIG, DSH, NODE, ROOT, STANDARD_PRESET, _provider, _skill_inventory, _tool_inventory


def check(label: str, ok: bool, detail: str) -> bool:
    print(f"{'OK' if ok else 'FAIL'}  {label}: {detail}")
    return ok


def main() -> int:
    results = []
    results.append(check("Python", sys.version_info[:2] in {(3, 11), (3, 12), (3, 13)},
                         sys.version.split()[0]))
    results.append(check("Node runtime", NODE.is_file(), str(NODE)))
    results.append(check("DSH runtime", DSH.is_file() and STANDARD_PRESET.is_file(), str(DSH)))
    try:
        import fastapi  # noqa: F401
        import mcp  # noqa: F401
        import uvicorn  # noqa: F401
        results.append(check("Python packages", True, "FastAPI, MCP, Uvicorn installed"))
    except ImportError as exc:
        results.append(check("Python packages", False, f"Run setup.ps1: {exc}"))
    try:
        provider, model, _, _ = _provider()
        results.append(check("Model configuration", True, f"{provider} / {model}"))
        if provider == "ollama-local":
            try:
                with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3) as response:
                    installed = json.load(response)
                names = {item.get("name") for item in installed.get("models", [])}
                results.append(check("Ollama model", model in names,
                                     model if model in names else f"Run ollama pull {model}"))
            except (OSError, ValueError) as exc:
                results.append(check("Ollama", False, f"Start Ollama: {exc}"))
    except (OSError, ValueError, RuntimeError) as exc:
        results.append(check("Model configuration", False, str(exc)))
    try:
        _, tools = _tool_inventory()
        skills = _skill_inventory()
        results.append(check("Examples", len(tools) == 3 and len(skills) == 2,
                             f"{len(tools)} MCP servers, {len(skills)} Skills"))
    except (OSError, ValueError) as exc:
        results.append(check("Examples", False, str(exc)))
    print("Local sequence API starts automatically with start.ps1 (port 8015).")
    print("DSH Web starts on port 3090 and prints its token URL.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
