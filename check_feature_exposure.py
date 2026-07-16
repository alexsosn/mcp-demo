import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


CHECKS = {
    "bhsa": ["sp", "vt", "vs", "ps", "gn", "nu", "st", "pdp", "typ", "function", "lex"],
    "dss": ["morpho", "morph_etcbc", "sp", "ps", "gn", "nu", "lex"],
    "extrabiblical": ["sp", "vt", "vs", "ps", "gn", "nu", "st", "pdp", "lex"],
    "peshitta": ["lex", "book", "chapter", "verse"],
    "syriac": ["sp", "vt", "vs", "ps", "gn", "nu", "st", "lex"],
}

SEARCHES = [
    ("bhsa", "word sp=verb", 3),
    ("bhsa", "word vt=perf", 3),
    ("bhsa", "word ps=p1", 3),
    ("dss", "word morpho", 3),
    ("extrabiblical", "word sp=verb", 3),
    ("syriac", "word sp=verb", 3),
]


async def main():
    params = StdioServerParameters(command="./run-mcp-extended.sh", args=[])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for corpus, expected in CHECKS.items():
                result = await session.call_tool("list_features", {"corpus": corpus})
                text = result.content[0].text
                print(f"\n## {corpus} features")
                for feature in expected:
                    print(f"{feature}: {'yes' if feature in text else 'NO'}")

            for corpus, template, limit in SEARCHES:
                result = await session.call_tool(
                    "search", {"corpus": corpus, "template": template, "limit": limit}
                )
                print(f"\n## {corpus} search {template!r}")
                for item in result.content:
                    print(getattr(item, "text", item))


if __name__ == "__main__":
    anyio.run(main)
