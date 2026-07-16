from pathlib import Path


ROOT = Path(__file__).resolve().parent
GREEK_ROOT = ROOT / "corpora" / "greek_literature"
OUT = ROOT / "greek_literature_catalog.tsv"


def metadata(path):
    values = {"author": "", "title": "", "filename": "", "sectionTypes": ""}
    for line in path.read_text(errors="replace").splitlines():
        if not line.startswith("@") or "=" not in line:
            continue
        key, value = line[1:].split("=", 1)
        if key in values:
            values[key] = value
    return values


def main():
    rows = []
    for otext in sorted(GREEK_ROOT.glob("**/tf/1.0/otext.tf")):
        tf_dir = otext.parent
        meta = metadata(otext)
        rows.append(
            [
                str(tf_dir.relative_to(ROOT)),
                meta["author"],
                meta["title"],
                meta["filename"],
                meta["sectionTypes"],
            ]
        )

    with OUT.open("w") as fh:
        fh.write("path\tauthor\ttitle\tfilename\tsection_types\n")
        for row in rows:
            fh.write("\t".join(row) + "\n")
    print(f"Wrote {OUT} with {len(rows)} Greek Literature TF corpora")


if __name__ == "__main__":
    main()
