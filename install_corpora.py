#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from mcp_corpora import BASE_CORPORA, GREEK_LITERATURE_CORPORA, ROOT


CORPORA_ROOT = ROOT / "corpora"
SOURCES = {
    "cuc": "https://github.com/DT-UCPH/cuc.git",
    "bhsa": "https://github.com/ETCBC/bhsa.git",
    "greek_literature": "https://github.com/pthu/greek_literature.git",
}


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def clone_if_missing(name: str, destination: Path) -> None:
    if (destination / ".git").is_dir():
        print(f"    {name} already cloned")
        return
    if destination.exists():
        raise SystemExit(
            f"ERROR: {destination} exists but is not a Git checkout; move it aside and rerun."
        )
    run(
        "git",
        "clone",
        "--depth",
        "1",
        SOURCES[name],
        str(destination),
    )


def greek_sparse_paths() -> list[str]:
    prefix = "corpora/greek_literature/"
    return [path.removeprefix(prefix) for path in GREEK_LITERATURE_CORPORA.values()]


def install_greek_literature() -> None:
    destination = CORPORA_ROOT / "greek_literature"
    if not (destination / ".git").is_dir():
        if destination.exists():
            raise SystemExit(
                f"ERROR: {destination} exists but is not a Git checkout; move it aside and rerun."
            )
        run(
            "git",
            "clone",
            "--depth",
            "1",
            "--filter=blob:none",
            "--sparse",
            SOURCES["greek_literature"],
            str(destination),
        )

    sparse_enabled = subprocess.run(
        ["git", "-C", str(destination), "config", "--bool", "core.sparseCheckout"],
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if sparse_enabled == "true":
        run(
            "git",
            "-C",
            str(destination),
            "sparse-checkout",
            "set",
            "--cone",
            *greek_sparse_paths(),
        )
    else:
        print("    Greek Literature already cloned as a full checkout")


def validate(profile: str) -> None:
    expected = {
        "cuc": BASE_CORPORA["cuc"],
        "bhsa": BASE_CORPORA["bhsa"],
    }
    if profile == "workshop":
        expected.update(GREEK_LITERATURE_CORPORA)

    missing = [
        f"{name}: {relative_path}"
        for name, relative_path in expected.items()
        if not (ROOT / relative_path / "otype.tf").is_file()
    ]
    if missing:
        details = "\n".join(f"  - {item}" for item in missing)
        raise SystemExit(f"ERROR: expected Text-Fabric data is missing:\n{details}")
    print(f"Validated {len(expected)} installed corpora for the {profile} profile.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Install the MCP demo corpora")
    parser.add_argument(
        "--profile",
        choices=["minimal", "workshop"],
        default="workshop",
        help="minimal installs CUC and BHSA; workshop also installs curated Greek works",
    )
    args = parser.parse_args()

    CORPORA_ROOT.mkdir(parents=True, exist_ok=True)
    clone_if_missing("cuc", CORPORA_ROOT / "cuc")
    clone_if_missing("bhsa", CORPORA_ROOT / "bhsa")
    if args.profile == "workshop":
        install_greek_literature()
    validate(args.profile)


if __name__ == "__main__":
    main()
