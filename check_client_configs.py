from __future__ import annotations

import json
import tomllib
from pathlib import Path

from generate_mcp_configs import ROOT, SEFARIA_URL, installed_corpora


def read_json(path: Path) -> dict:
    with path.open("rb") as handle:
        return json.load(handle)


def validate_ancient_corpora(client: str, server: dict) -> None:
    command = Path(server["command"])
    if not command.is_file():
        raise SystemExit(f"{client}: missing MCP command: {command}")
    expected = installed_corpora()
    args = server.get("args", [])
    configured = {
        value.split("=", 1)[0]
        for flag, value in zip(args[::2], args[1::2])
        if flag == "--corpus"
    }
    missing = set(expected) - configured
    if missing:
        raise SystemExit(f"{client}: missing corpora: {', '.join(sorted(missing))}")
    print(f"{client}: ancient-corpora configured with {len(configured)} corpora")


def main() -> None:
    antigravity_path = ROOT / ".agents" / "mcp_config.json"
    codex_path = ROOT / ".codex" / "config.toml"
    claude_path = ROOT / "clients" / "claude_desktop_config.extended.generated.json"

    antigravity = read_json(antigravity_path)["mcpServers"]
    with codex_path.open("rb") as handle:
        codex = tomllib.load(handle)["mcp_servers"]
    claude = read_json(claude_path)["mcpServers"]

    validate_ancient_corpora("Antigravity", antigravity["ancient-corpora"])
    validate_ancient_corpora("Codex", codex["ancient-corpora"])
    validate_ancient_corpora("Claude", claude["ancient-corpora"])

    for client, server in [
        ("Antigravity", antigravity["sefaria"]),
        ("Codex", codex["sefaria"]),
    ]:
        if Path(server["command"]).name not in {"mcp-proxy", "mcp-proxy.exe"}:
            raise SystemExit(f"{client}: Sefaria must use the local mcp-proxy bridge")
        if server.get("args") != [SEFARIA_URL]:
            raise SystemExit(f"{client}: unexpected Sefaria proxy arguments")
        print(f"{client}: Sefaria SSE-to-STDIO proxy configuration is valid")

    print("All generated client configurations are valid.")


if __name__ == "__main__":
    main()
