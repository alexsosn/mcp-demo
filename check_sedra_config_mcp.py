import argparse
import json
import os
import sys
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def default_claude_config() -> Path:
    override = os.environ.get("CLAUDE_DESKTOP_CONFIG")
    if override:
        return Path(override).expanduser()
    if sys.platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        )
    if os.name == "nt":
        return Path(os.environ["APPDATA"]) / "Claude" / "claude_desktop_config.json"
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / "Claude" / "claude_desktop_config.json"


async def main(config_path: Path):
    config = json.loads(config_path.read_text())
    server = config["mcpServers"]["bethmardutho"]
    params = StdioServerParameters(
        command=server["command"],
        args=server.get("args", []),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = [tool.name for tool in (await session.list_tools()).tools]
            print("SEDRA config tools:", ", ".join(tools))
            result = await session.call_tool("get__lexeme__id_", {"id": "11820"})
            for item in result.content:
                print(getattr(item, "text", item)[:4000])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verify the Beth Mardutho server from a Claude Desktop config."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=default_claude_config(),
        help=(
            "Claude Desktop config path; defaults to the platform location or "
            "$CLAUDE_DESKTOP_CONFIG"
        ),
    )
    args = parser.parse_args()
    anyio.run(main, args.config.expanduser())
