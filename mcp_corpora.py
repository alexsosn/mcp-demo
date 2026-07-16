from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FEATURES = "g_cons g_word_utf8 lex book chapter verse language line tablet"


BASE_CORPORA = OrderedDict(
    [
        ("cuc", "corpora/cuc/tf/0.2.7"),
        ("bhsa", "corpora/bhsa/tf/4b"),
        ("lxx", "corpora/lxx/tf/1935"),
        ("dss", "corpora/dss/tf/2.0"),
        ("extrabiblical", "corpora/extrabiblical/tf/0.2"),
        ("peshitta", "corpora/peshitta/tf/0.2"),
        ("syriac", "corpora/syriac/tf/0.7"),
        ("akkadian_oldbabylonian", "corpora/oldbabylonian/tf/1.0.6"),
        ("akkadian_oldassyrian", "corpora/oldassyrian/tf/0.1"),
    ]
)


GREEK_LITERATURE_CORPORA = OrderedDict(
    [
        (
            "greek_homer_iliad",
            "corpora/greek_literature/canonical-greekLit/tlg0012/tlg001/perseus-grc2/1/tf/1.0",
        ),
        (
            "greek_homer_odyssey",
            "corpora/greek_literature/canonical-greekLit/tlg0012/tlg002/perseus-grc2/1/tf/1.0",
        ),
        (
            "greek_sophocles_antigone",
            "corpora/greek_literature/canonical-greekLit/tlg0011/tlg002/perseus-grc2/1/tf/1.0",
        ),
        (
            "greek_aeschylus_agamemnon",
            "corpora/greek_literature/canonical-greekLit/tlg0085/tlg005/perseus-grc2/1/tf/1.0",
        ),
        (
            "greek_plato_euthyphro",
            "corpora/greek_literature/canonical-greekLit/tlg0059/tlg001/perseus-grc1/1/tf/1.0",
        ),
        (
            "greek_plato_phaedo",
            "corpora/greek_literature/canonical-greekLit/tlg0059/tlg004/perseus-grc2/1/tf/1.0",
        ),
        (
            "greek_plato_cratylus",
            "corpora/greek_literature/canonical-greekLit/tlg0059/tlg005/perseus-grc2/1/tf/1.0",
        ),
        (
            "greek_xenophon_hellenica",
            "corpora/greek_literature/canonical-greekLit/tlg0032/tlg001/perseus-grc2/1/tf/1.0",
        ),
    ]
)


EXTENDED_CORPORA = OrderedDict()
EXTENDED_CORPORA.update(BASE_CORPORA)
EXTENDED_CORPORA.update(GREEK_LITERATURE_CORPORA)


def absolute_path(relative_path: str) -> str:
    return str(ROOT / relative_path)


def corpus_args(
    corpora: OrderedDict[str, str], *, absolute: bool = False, include_features: bool = True
) -> list[str]:
    args = []
    for name, path in corpora.items():
        args.extend(["--corpus", f"{name}={absolute_path(path) if absolute else path}"])
    if include_features:
        args.extend(["--features", FEATURES])
    return args
