import json
import stat

from mcp_corpora import EXTENDED_CORPORA, FEATURES, ROOT, absolute_path, corpus_args


def write_executable(path, text):
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def main():
    launcher = ROOT / "run-mcp-extended.sh"
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f'cd "{ROOT}"',
        'exec "./.venv/bin/cfabric-mcp" \\',
    ]
    args = corpus_args(EXTENDED_CORPORA, include_features=False)
    for index in range(0, len(args), 2):
        flag, value = args[index], args[index + 1]
        suffix = " \\" if index + 2 < len(args) else ""
        lines.append(f'  {flag} "{value}"{suffix}')
    write_executable(launcher, "\n".join(lines) + "\n")

    desktop_config = {
        "mcpServers": {
            "ancient-corpora": {
                "command": absolute_path(".venv/bin/cfabric-mcp"),
                "args": corpus_args(
                    EXTENDED_CORPORA, absolute=True, include_features=False
                ),
            }
        }
    }
    config_path = ROOT / "clients" / "claude_desktop_config.extended.generated.json"
    config_path.write_text(json.dumps(desktop_config, ensure_ascii=False, indent=2) + "\n")

    code_setup = ROOT / "clients" / "claude_code_extended_setup.generated.sh"
    code_lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f'claude mcp add ancient-corpora -- "{absolute_path(".venv/bin/cfabric-mcp")}" \\',
    ]
    args = corpus_args(EXTENDED_CORPORA, absolute=True, include_features=False)
    for index in range(0, len(args), 2):
        flag, value = args[index], args[index + 1]
        suffix = " \\" if index + 2 < len(args) else ""
        code_lines.append(f'  {flag} "{value}"{suffix}')
    code_lines.extend(
        [
            "claude mcp add --transport sse sefaria https://mcp.sefaria.org/sse",
            "claude mcp list",
        ]
    )
    write_executable(code_setup, "\n".join(code_lines) + "\n")

    print(f"Wrote {launcher}")
    print(f"Wrote {config_path}")
    print(f"Wrote {code_setup}")
    print(f"Configured {len(EXTENDED_CORPORA)} corpora, including {sum(name.startswith('greek_') for name in EXTENDED_CORPORA)} from greek_literature.")


if __name__ == "__main__":
    main()
