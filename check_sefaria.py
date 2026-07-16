import anyio
from mcp import ClientSession
from mcp.client.sse import sse_client


async def main():
    async with sse_client("https://mcp.sefaria.org/sse", sse_read_timeout=60) as (
        read,
        write,
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("TOOLS", [tool.name for tool in (await session.list_tools()).tools])
            for tool_name, args in [
                ("get_text", {"reference": "Genesis 1:1", "version_language": "both"}),
                ("get_text", {"reference": "Deuteronomy 16:21", "version_language": "both"}),
                ("search_in_book", {"query": "אברהם", "book_name": "Genesis", "size": 3}),
            ]:
                result = await session.call_tool(tool_name, args)
                print(f"\n## {tool_name}")
                for item in result.content:
                    print(getattr(item, "text", item))


if __name__ == "__main__":
    anyio.run(main)
