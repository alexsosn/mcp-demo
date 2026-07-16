import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(
        command="node",
        args=["servers/bethmardutho/dist/index.js"],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("SEDRA tools:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            for label, args in [
                ("word id 30862", {"id": "30862"}),
                ("word consonantal ܐܒܪܐ", {"id": "ܐܒܪܐ"}),
            ]:
                print(f"\n## {label}")
                result = await session.call_tool("get__word__id_", args)
                for item in result.content:
                    print(getattr(item, "text", item)[:4000])


if __name__ == "__main__":
    anyio.run(main)
