#!/usr/bin/env python3
from __future__ import annotations

import json

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client


CFABRIC_FEATURES = "g_cons g_word_utf8 lex book chapter verse language line tablet"


def print_text_result(name: str, result) -> None:
    print(f"\n## {name}")
    for item in result.content:
        text = getattr(item, "text", item)
        try:
            parsed = json.loads(text)
        except Exception:
            print(text)
        else:
            print(json.dumps(parsed, ensure_ascii=False, indent=2)[:2000])


async def verify_cfabric() -> None:
    params = StdioServerParameters(
        command="./.venv/bin/cfabric-mcp",
        args=[
            "--corpus",
            "cuc=corpora/cuc/tf/0.2.7",
            "--corpus",
            "bhsa=corpora/bhsa/tf/4b",
            "--features",
            CFABRIC_FEATURES,
        ],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = [tool.name for tool in (await session.list_tools()).tools]
            print("ContextFabric tools:", ", ".join(tools))
            print_text_result("list_corpora", await session.call_tool("list_corpora", {}))
            print_text_result(
                "CUC aṯrt",
                await session.call_tool(
                    "search",
                    {"corpus": "cuc", "template": "word g_cons=aṯrt", "limit": 3},
                ),
            )
            print_text_result(
                "BHSA >CRH/",
                await session.call_tool(
                    "search",
                    {"corpus": "bhsa", "template": "word lex=>CRH/", "limit": 3},
                ),
            )


async def verify_sefaria() -> None:
    async with sse_client("https://mcp.sefaria.org/sse", sse_read_timeout=60) as (
        read,
        write,
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = [tool.name for tool in (await session.list_tools()).tools]
            print("Sefaria tools:", ", ".join(tools))
            print_text_result(
                "Sefaria Genesis 1:1",
                await session.call_tool(
                    "get_text",
                    {"reference": "Genesis 1:1", "version_language": "both"},
                ),
            )
            print_text_result(
                "Sefaria Deuteronomy 16:21",
                await session.call_tool(
                    "get_text",
                    {"reference": "Deuteronomy 16:21", "version_language": "both"},
                ),
            )


async def main() -> None:
    print("==> Verifying local ContextFabric MCP")
    await verify_cfabric()
    print("\n==> Verifying hosted Sefaria Texts MCP")
    await verify_sefaria()
    print("\nALL THREE INTERROGABLE")


if __name__ == "__main__":
    anyio.run(main)
