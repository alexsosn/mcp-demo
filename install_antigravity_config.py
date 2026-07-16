#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

from mcp_corpora import ROOT


WORKSPACE_CONFIG = ROOT / ".agents" / "mcp_config.json"


def default_global_config() -> Path:
    candidates = [
        Path("~/.gemini/antigravity/mcp_config.json").expanduser(),
        Path("~/.gemini/config/mcp_config.json").expanduser(),
    ]
    for candidate in candidates:
        if candidate.exists() or candidate.is_symlink():
            return candidate
    return candidates[0]


def read_config(path: Path, *, required: bool) -> dict:
    if not path.exists():
        if required:
            raise SystemExit(f"ERROR: generated config is missing: {path}; run ./setup.sh first.")
        return {"mcpServers": {}}
    try:
        config = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"ERROR: cannot read JSON config {path}: {error}") from error
    if not isinstance(config, dict) or not isinstance(config.get("mcpServers"), dict):
        raise SystemExit(f"ERROR: {path} must contain an mcpServers object")
    return config


def atomic_write(path: Path, config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as temporary:
        json.dump(config, temporary, ensure_ascii=False, indent=2)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def install(workspace_path: Path, requested_global_path: Path) -> None:
    workspace = read_config(workspace_path, required=True)

    # Resolve an existing symlink so the shared target remains linked after the
    # atomic replacement.
    global_path = requested_global_path.resolve(strict=False)
    global_config = read_config(global_path, required=False)
    existing_servers = global_config["mcpServers"]
    project_servers = workspace["mcpServers"]
    preserved = sorted(set(existing_servers) - set(project_servers))

    backup_path = global_path.with_name(f"{global_path.name}.bak")
    if global_path.exists():
        shutil.copy2(global_path, backup_path)

    existing_servers.update(project_servers)
    atomic_write(global_path, global_config)

    print(f"Installed project MCP servers into {global_path}:")
    for name in sorted(project_servers):
        print(f"  - {name}")
    if preserved:
        print(f"Preserved existing MCP servers: {', '.join(preserved)}")
    if backup_path.exists():
        print(f"Previous config backed up to {backup_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge this project's generated servers into Antigravity's global config"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=default_global_config(),
        help="override the Antigravity global mcp_config.json path",
    )
    args = parser.parse_args()
    install(WORKSPACE_CONFIG, args.config.expanduser())


if __name__ == "__main__":
    main()
