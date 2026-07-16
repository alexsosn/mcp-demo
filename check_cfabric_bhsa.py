import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(
        command="./.venv/bin/cfabric-mcp",
        args=[
            "--corpus",
            "bhsa=corpora/bhsa/tf/4b",
            "--features",
            "g_cons g_word_utf8 lex book chapter verse language",
        ],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("TOOLS", [tool.name for tool in (await session.list_tools()).tools])
            for tool_name, args in [
                ("list_corpora", {}),
                ("describe_corpus", {"corpus": "bhsa"}),
                ("search", {"corpus": "bhsa", "template": "word lex=>CRH/"}),
            ]:
                result = await session.call_tool(tool_name, args)
                print(f"\n## {tool_name}")
                for item in result.content:
                    print(getattr(item, "text", item))


if __name__ == "__main__":
    anyio.run(main)
