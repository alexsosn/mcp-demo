import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_corpora import EXTENDED_CORPORA


async def main():
    params = StdioServerParameters(command="./run-mcp-extended.sh", args=[])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("list_corpora", {})
            text = result.content[0].text
            print(text)
            missing = [name for name in sorted(EXTENDED_CORPORA) if name not in text]
            if missing:
                raise SystemExit(f"Missing corpora: {', '.join(missing)}")


if __name__ == "__main__":
    anyio.run(main)
