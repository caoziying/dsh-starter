"""Discover teaching Tools/Skills and run the packaged DSH Web instance.

The JSON written to ``.runtime/generated`` is a readable record of exactly
what was registered.  Edit ``tools/*/tool.json`` or ``skills/*/SKILL.md`` and
restart to see how DSH discovers new capabilities.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

HARNESS = Path(__file__).resolve().parent
ROOT = HARNESS.parent
CONFIG = HARNESS / "config"
TOOLS = HARNESS / "tools"
SKILLS = HARNESS / "skills"
RUNTIME = HARNESS / ".runtime"
NODE = RUNTIME / "node" / "node.exe"
DSH = RUNTIME / "packages" / "node_modules" / "@deepseek-ai" / "dsh" / "lib" / "bin.js"
STANDARD_PRESET = (
    RUNTIME / "packages" / "node_modules" / "@deepseek-ai"
    / "dsh-agent-presets" / "presets" / "standard" / "agent.cordis.yml"
)
GENERATED = RUNTIME / "generated"
PATCH = GENERATED / "harness.patch.yml"
INVENTORY = GENERATED / "inventory.json"
STATE = RUNTIME / "processes.json"
LOGS = HARNESS / "logs"
API_PORT = 8015
WEB_PORT = 3090


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _secret(name: str) -> str | None:
    """Read only the requested value, never print a secret."""
    if os.getenv(name):
        return os.environ[name]
    path = CONFIG / "secrets.env"
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == name:
            return value.strip().strip('"\'') or None
    return None


def _provider() -> tuple[str, str, dict[str, Any], dict[str, str]]:
    path = CONFIG / "provider.json"
    if not path.is_file():
        raise RuntimeError("Run setup.ps1 to select a model provider")
    config = _read_json(path)
    mode = config.get("provider")
    model = str(config.get("model", "")).strip()
    window = int(config.get("context_window", 8192))
    if not model or not 4096 <= window <= 131072:
        raise ValueError("provider.json requires a model and context_window 4096–131072")
    max_tokens = min(int(config.get("max_output_tokens", 4096)), window // 2)
    if max_tokens < 1:
        raise ValueError("max_output_tokens must be positive")
    model_info: dict[str, Any] = {
        "id": model,
        "name": model,
        "contextWindow": window,
        "maxTokens": max_tokens,
        "input": ["text"],
        "reasoningEfforts": False,
    }
    if mode == "deepseek":
        key = _secret("DEEPSEEK_API_KEY")
        if not key:
            raise RuntimeError("Set DEEPSEEK_API_KEY in harness/config/secrets.env")
        provider = "deepseek-api"
        model_info["compat"] = {
            "supportsDeveloperRole": False,
            "supportsStore": False,
            "maxTokensField": "max_tokens",
            "requiresReasoningContentOnAssistantMessages": True,
            "thinkingFormat": "deepseek",
        }
        route = {
            "displayName": "DeepSeek API",
            "apiKeyEnv": "DEEPSEEK_API_KEY",
            "api": "openai-completions",
            "baseURL": "https://api.deepseek.com",
            "models": [model_info],
        }
        environment = {"DEEPSEEK_API_KEY": key, "DEEPSEEK_BASE_URL": route["baseURL"]}
    elif mode == "school":
        key = _secret("SCHOOL_API_KEY")
        base_url = _secret("SCHOOL_BASE_URL")
        if not key or not base_url:
            raise RuntimeError("Set SCHOOL_API_KEY and SCHOOL_BASE_URL in secrets.env")
        if not base_url.startswith(("https://", "http://127.0.0.1", "http://localhost")):
            raise ValueError("SCHOOL_BASE_URL must use HTTPS or local loopback HTTP")
        provider = "school-api"
        route = {
            "displayName": "School OpenAI-compatible API",
            "apiKeyEnv": "SCHOOL_API_KEY",
            "api": "openai-completions",
            "baseURL": base_url.rstrip("/"),
            "models": [model_info],
        }
        environment = {"SCHOOL_API_KEY": key, "DEEPSEEK_API_KEY": key, "DEEPSEEK_BASE_URL": route["baseURL"]}
    elif mode == "ollama":
        provider = "ollama-local"
        route = {
            "displayName": "Local Ollama",
            "api": "openai-completions",
            "baseURL": "http://127.0.0.1:11434/v1",
            "headers": {"Authorization": "Bearer ollama-local"},
            "models": [model_info],
        }
        environment = {
            "DEEPSEEK_API_KEY": "unused-local-ollama",
            "DEEPSEEK_BASE_URL": route["baseURL"],
        }
    else:
        raise ValueError("provider.json provider must be deepseek, school or ollama")
    return provider, model, route, environment


def _skill_inventory() -> list[dict[str, str]]:
    result = []
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        content = path.read_text(encoding="utf-8-sig")
        match = re.match(r"^---\s*\n(?P<front>.*?)\n---\s*(?:\n|$)", content, re.DOTALL)
        if not match:
            raise ValueError(f"Missing Skill frontmatter: {path}")
        fields = {}
        for line in match.group("front").splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                fields[key.strip()] = value.strip()
        if fields.get("name") != path.parent.name or not fields.get("description"):
            raise ValueError(f"Skill name/description mismatch: {path}")
        result.append({"name": fields["name"], "description": fields["description"]})
    return result


def _tool_inventory() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    plugins = []
    inventory = []
    ids = set()
    server_names = set()
    for path in sorted(TOOLS.glob("*/tool.json")):
        item = _read_json(path)
        if not item.get("enabled", True):
            continue
        tool_id = str(item.get("id", ""))
        server_name = str(item.get("server_name", ""))
        entry = (path.parent / str(item.get("entry", ""))).resolve()
        if not tool_id or not server_name or not entry.is_file():
            raise ValueError(f"Invalid Tool manifest: {path}")
        if tool_id in ids or server_name in server_names:
            raise ValueError(f"Duplicate Tool id/server name: {path}")
        ids.add(tool_id)
        server_names.add(server_name)
        plugins.append({
            "id": tool_id,
            "name": "@deepseek-ai/dsh-mcp-client",
            "config": {
                "serverName": server_name,
                "transport": "stdio",
                "command": Path(sys.executable).as_posix(),
                "args": [entry.as_posix()],
                "env": {},
                "cwd": ROOT.as_posix(),
                "toolCallTimeoutMs": int(item.get("tool_call_timeout_ms", 30000)),
                "failOnStartupError": True,
            },
        })
        inventory.append({
            "id": tool_id,
            "server_name": server_name,
            "tools": item.get("tools", []),
            "entry": str(entry),
        })
    return plugins, inventory


def sync() -> dict[str, Any]:
    if not NODE.is_file() or not DSH.is_file() or not STANDARD_PRESET.is_file():
        raise RuntimeError("Packaged DSH runtime missing; use the release ZIP")
    provider, model, route, _ = _provider()
    prompt = (CONFIG / "system-prompt.md").read_text(encoding="utf-8-sig").strip()
    preset = STANDARD_PRESET.read_text(encoding="utf-8-sig")
    start = preset.index("- id: persona\n")
    end = preset.index("- id: agent-instructions\n", start)
    replacement = (
        "- id: persona\n"
        "  name: '@deepseek-ai/dsh-persona'\n"
        "  config:\n"
        f"    prefix: {json.dumps(prompt, ensure_ascii=False)}\n"
        "    complete: true\n"
        "    includeRuntimeContext: true\n\n"
    )
    presets = HARNESS / "presets" / "starter"
    presets.mkdir(parents=True, exist_ok=True)
    (presets / "agent.cordis.yml").write_text(preset[:start] + replacement + preset[end:], encoding="utf-8")
    (presets / "preset.yml").write_text(
        "name: DSH 教学模式\ndescription: 使用示例 Tools 和 Skills。\norder: 0\n",
        encoding="utf-8",
    )
    plugins, tools = _tool_inventory()
    skills = _skill_inventory()
    patch: list[dict[str, Any]] = [
        {"id": "system-prompt", "config": {"personaPrefix": prompt}},
        {"id": "agent-presets", "config": {
            "default": "starter",
            "roots": [{"path": (HARNESS / "presets").as_posix(), "trust": "system"}],
        }},
        {"id": "agent-default-model", "config": {"provider": provider, "model": model}},
        {"id": "llm-pi-ai", "config": {"providers": {provider: route}}},
        {"id": "skill-filesystem", "disabled": False, "config": {
            "providerName": "starter-skills",
            "includeDefaultRoots": False,
            "customSkillDirs": [SKILLS.as_posix()],
            "watch": True,
        }},
        {"id": "tool-skill", "config": {"catalogDescriptionMaxLength": 500}},
        {"insert": plugins},
    ]
    GENERATED.mkdir(parents=True, exist_ok=True)
    PATCH.write_text(json.dumps(patch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"provider": provider, "model": model, "tools": tools, "skills": skills}
    INVENTORY.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def _port_open(port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _owns_port(pid: int, port: int) -> bool:
    """Only stop a recorded PID if it still owns this starter's listen port."""
    query = (
        f"$targetPid={pid}; "
        f"$listeners=@(Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue); "
        "foreach($item in $listeners){ "
        "$currentPid=[int]$item.OwningProcess; "
        "while($currentPid -gt 0){ "
        "if($currentPid -eq $targetPid){ 'owned'; exit 0 }; "
        "$process=Get-CimInstance Win32_Process -Filter ('ProcessId=' + $currentPid); "
        "if(-not $process){ break }; "
        "$nextPid=[int]$process.ParentProcessId; "
        "if($nextPid -eq $currentPid){ break }; "
        "$currentPid=$nextPid "
        "} }; exit 1"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", query],
        capture_output=True, text=True, check=False,
    )
    return result.returncode == 0 and "owned" in result.stdout.split()


def _ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            return json.load(response).get("status") == "ready"
    except (OSError, ValueError, TimeoutError):
        return False


def _spawn(args: list[str], log_name: str, env: dict[str, str]) -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    with (LOGS / log_name).open("ab", buffering=0) as stream:
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        process = subprocess.Popen(
            args, cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
            stdout=stream, stderr=subprocess.STDOUT, creationflags=flags,
        )
    return process.pid


def _state() -> dict[str, Any]:
    if not STATE.is_file():
        return {}
    value = _read_json(STATE)
    return value if value.get("root") == str(ROOT) else {}


def _save_state(value: dict[str, Any]) -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"root": str(ROOT), **value}, indent=2), encoding="utf-8")


def start() -> int:
    inventory = sync()
    provider, model, _, provider_env = _provider()
    state = _state()
    if _port_open(API_PORT):
        if not _ready(f"http://127.0.0.1:{API_PORT}/readyz") or not _owns_port(
            int(state.get("api_pid", 0)), API_PORT
        ):
            raise RuntimeError(f"Port {API_PORT} is in use by another service")
    else:
        environment = os.environ.copy()
        api_pid = _spawn([
            sys.executable, "-m", "uvicorn", "services.sequence_demo.app:app",
            "--host", "127.0.0.1", "--port", str(API_PORT),
        ], "sequence-api.log", environment)
        state["api_pid"] = api_pid
        _save_state(state)
        for _ in range(60):
            if _ready(f"http://127.0.0.1:{API_PORT}/readyz"):
                break
            time.sleep(0.25)
        else:
            raise RuntimeError(f"Sequence API failed to start; see {LOGS / 'sequence-api.log'}")
    if _port_open(WEB_PORT):
        if state.get("web_pid") and _owns_port(int(state["web_pid"]), WEB_PORT):
            print(json.dumps({"status": "already_running", "url": f"http://127.0.0.1:{WEB_PORT}"}))
            return 0
        raise RuntimeError(f"Port {WEB_PORT} is in use by another application")
    environment = os.environ.copy()
    environment.update(provider_env)
    environment.update({
        "DSH_HOME": str(RUNTIME / "state"),
        "DSH_TELEMETRY_DISABLED": "1",
        "XDG_CACHE_HOME": str(RUNTIME / "cache"),
        "PKG_CACHE_PATH": str(RUNTIME / "cache" / "pkg"),
        "HARNESS_ROOT": str(HARNESS),
        "WORKSPACE_ROOT": str(ROOT),
        "SEQUENCE_API_URL": f"http://127.0.0.1:{API_PORT}",
    })
    log_path = LOGS / "web.log"
    LOGS.mkdir(parents=True, exist_ok=True)
    log_path.write_bytes(b"")
    web_pid = _spawn([
        str(NODE), str(DSH), "--profile", "web", "--patch", str(PATCH),
        "--no-open", "--host", "127.0.0.1", "--port", str(WEB_PORT),
    ], "web.log", environment)
    state["web_pid"] = web_pid
    _save_state(state)
    for _ in range(120):
        if _port_open(WEB_PORT):
            content = log_path.read_text(encoding="utf-8", errors="replace")
            for line in reversed(content.splitlines()):
                if line.startswith("dsh web: http://"):
                    print(json.dumps({
                        "status": "started", "open_url": line.removeprefix("dsh web: "),
                        "provider": provider, "model": model,
                        "tools": len(inventory["tools"]), "skills": len(inventory["skills"]),
                        "log": str(log_path),
                    }, ensure_ascii=False))
                    return 0
        time.sleep(0.25)
    raise RuntimeError(f"DSH Web failed to start; see {log_path}")


def stop() -> int:
    state = _state()
    for name, port in (("web_pid", WEB_PORT), ("api_pid", API_PORT)):
        pid = state.get(name)
        if pid and _owns_port(int(pid), port):
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           capture_output=True, check=False)
    STATE.unlink(missing_ok=True)
    print(json.dumps({"status": "stopped"}))
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sync-only", action="store_true")
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    if args.stop:
        return stop()
    if args.status:
        print(json.dumps({"api_ready": _ready(f"http://127.0.0.1:{API_PORT}/readyz"),
                          "web_listening": _port_open(WEB_PORT), "state": _state()}, ensure_ascii=False))
        return 0
    if args.sync_only:
        print(json.dumps(sync(), ensure_ascii=False, indent=2))
        return 0
    return start()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"DSH Starter: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
