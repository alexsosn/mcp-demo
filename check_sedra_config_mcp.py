import json
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


CONFIG = Path(
    "/Users/alexandersosnovschenko/Library/Application Support/Claude/claude_desktop_config.json"
)


async def main():
    config = json.loads(CONFIG.read_text())
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
    anyio.run(main)
