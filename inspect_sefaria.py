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
            tools = (await session.list_tools()).tools
            for tool in tools:
                print(f"\n## {tool.name}")
                if tool.description:
                    print(tool.description)
                print(tool.inputSchema)


if __name__ == "__main__":
    anyio.run(main)
