import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_corpora import GREEK_LITERATURE_CORPORA


async def main():
    params = StdioServerParameters(command="./run-mcp-extended.sh", args=[])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for name in GREEK_LITERATURE_CORPORA:
                result = await session.call_tool(
                    "search", {"corpus": name, "template": "word", "limit": 1}
                )
                print(f"\n## {name}")
                for item in result.content:
                    print(getattr(item, "text", item))


if __name__ == "__main__":
    anyio.run(main)
