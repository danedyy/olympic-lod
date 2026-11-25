"""The SHACL file itself, checked against hand-made cases and the LDAP.

1. shacl/examples/valid-sample.ttl conforms (warnings for missing recommended values allowed).
2. Every shacl/examples/broken/*.ru (a SPARQL update that breaks one rule of the sample) fails,
   and the report names the term on its '# expect:' line. Every allowed/*.ru (it removes only a
   recommended value) still conforms, with a warning naming that term.
3. Every row of ldap/constraints-matrix.csv is found in the shapes with the same cardinality;
   a recommended (R) row as: no violation-level minimum + a warning when missing.
4. No schema.org term in the shapes or the examples.
"""
import csv
import glob
import os
import re

import pytest
from pyshacl import validate
from rdflib import Graph, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import SH

from config import PREFIXES, ROOT, SHAPES

EXAMPLES = os.path.join(ROOT, "shacl", "examples")
VALID = os.path.join(EXAMPLES, "valid-sample.ttl")
OLYSH = Namespace("https://w3id.org/olympic-lod/shapes#")

# matrix class -> shape; rows on role-specific properties go to the role shapes
CLASS_SHAPES = {
    "Person": ["PersonShape"], "Team": ["TeamShape"], "Squad": ["SquadShape"],
    "Coaching role": ["MembershipShape"], "NOC": ["NocShape"], "Country": ["CountryShape"],
    "Event": ["EventShape"], "The Games": ["GamesShape"], "Medal award": ["MedalAwardShape"],
    "Code list entry": ["ConceptShape"], "Code list": ["ConceptSchemeShape"], "Dataset": ["DatasetShape"],
}
ROW_SHAPES = {4: ["AthleteShape", "CoachShape", "OfficialShape"], 5: ["AthleteShape"],
              6: ["OfficialShape"], 7: ["OfficialShape"], 8: ["OfficialShape"]}


@pytest.fixture(scope="module")
def shapes():
    return Graph().parse(SHAPES)


def check(shapes, data):
    conforms, _, text = validate(data, shacl_graph=shapes, inference="none", allow_warnings=True)
    return conforms, text


def iri(curie):
    prefix, local = curie.split(":", 1)
    return URIRef(PREFIXES[prefix] + local)


def cases(folder):
    return sorted(glob.glob(os.path.join(EXAMPLES, folder, "*.ru")))


def test_valid_sample_conforms(shapes):
    assert check(shapes, Graph().parse(VALID))[0]


@pytest.mark.parametrize("path, should_conform",
                         [(p, False) for p in cases("broken")] + [(p, True) for p in cases("allowed")],
                         ids=lambda v: os.path.basename(v)[:-3] if isinstance(v, str) else None)
def test_case(shapes, path, should_conform):
    with open(path, encoding="utf-8") as f:
        update = f.read()
    expect = re.match(r"# expect: (\S+)", update).group(1)
    data = Graph().parse(VALID)
    data.update(update)
    conforms, text = check(shapes, data)
    assert conforms == should_conform and expect in text


def test_case_counts():
    assert (len(cases("broken")), len(cases("allowed"))) == (21, 4)


def warns_on(shapes, term):
    for w in shapes.subjects(SH.severity, SH.Warning):
        members = [w] + [m for lst in shapes.objects(w, SH["or"]) for m in Collection(shapes, lst)]
        if any(shapes.value(m, SH.path) == term and shapes.value(m, SH.minCount) is not None for m in members):
            return True
    return False


def matrix_rows():
    with open(os.path.join(ROOT, "ldap", "constraints-matrix.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.mark.parametrize("row", matrix_rows(), ids=lambda r: f"row{r['#']}-{r['RDF term']}")
def test_matrix_row_in_shapes(shapes, row):
    n, term = int(row["#"]), row["RDF term"]
    lo, hi = re.match(r"(\d)\.\.(\d|n)", row["Cardinality"]).groups()
    if term == "rdf:type":
        assert iri(row["Range"]) in set(shapes.objects(None, SH.targetClass))
        return
    for name in ROW_SHAPES.get(n, CLASS_SHAPES[row["Class"]]):
        props = [p for p in shapes.objects(OLYSH[name], SH.property) if shapes.value(p, SH.path) == iri(term)]
        strict = [p for p in props if shapes.value(p, SH.severity) != SH.Warning]
        mins = [int(shapes.value(p, SH.minCount)) for p in strict if shapes.value(p, SH.minCount) is not None]
        maxs = [int(shapes.value(p, SH.maxCount)) for p in strict if shapes.value(p, SH.maxCount) is not None]
        card = f"{max(mins, default=0)}..{min(maxs) if maxs else 'n'}"
        assert props, f"{name} has no property shape for {term}"
        if row["Obligation"] == "R":
            assert card == f"0..{hi}" and warns_on(shapes, iri(term))
        else:
            assert card == f"{lo}..{hi}", f"{name}: {card}"


def test_matrix_has_54_rows():
    assert len(matrix_rows()) == 54


def test_no_schema_org():
    files = [SHAPES, VALID] + cases("broken") + cases("allowed")
    hits = [f"{p}:{i}" for p in files for i, line in enumerate(open(p, encoding="utf-8"), 1)
            if re.search(r"schema\.org|\bschema:", line)]
    assert hits == []



def test_turtle_without_escaped_slashes():
    r"""Names like id:person\/1 are valid Turtle 1.1, but some parsers (the SHACL Playground's) reject them."""
    files = [SHAPES, VALID, os.path.join(ROOT, "ontology", "oly.ttl"), os.path.join(ROOT, "data", "rdf", "tokyo2020.ttl")]
    assert [p for p in files if "\\/" in open(p, encoding="utf-8").read()] == []
