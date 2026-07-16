import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_corpora import EXTENDED_CORPORA


async def check_corpus(name, path):
    params = StdioServerParameters(
        command="./.venv/bin/cfabric-mcp",
        args=["--corpus", f"{name}={path}"],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.call_tool("list_corpora", {})
            described = await session.call_tool("describe_corpus", {"corpus": name})
            searched = await session.call_tool(
                "search", {"corpus": name, "template": "word", "limit": 1}
            )
            print(f"\n## {name}")
            for label, result in [
                ("list_corpora", listed),
                ("describe_corpus", described),
                ("search word", searched),
            ]:
                print(f"# {label}")
                for item in result.content:
                    print(getattr(item, "text", item))


async def main():
    for name, path in EXTENDED_CORPORA.items():
        await check_corpus(name, path)


if __name__ == "__main__":
    anyio.run(main)
