"""The published 5-star data (data/rdf/tokyo2020.ttl): it is what the pipeline produces, it
conforms to the profile, and it keeps every figure measured on the source CSVs."""
import csv
import os
import re

import pytest
from rdflib import Graph, URIRef
from rdflib.namespace import FOAF, ORG, OWL, RDF, SKOS

from clean import clean
from config import DBO, ID, OLY, OUT, PREFIXES, ROOT, SCHEME, SOURCE
from derive import derive
from ingest import ingest
from issues import IssuesLog
from reconcile import reconcile
from teams import build
from to_rdf import to_rdf
from validate import validate

PUBLISHED = os.path.join(OUT, "tokyo2020.ttl")


@pytest.fixture(scope="module")
def built():
    log = IssuesLog()
    c = clean(ingest(), log)
    g = to_rdf(c, build(c, log), reconcile(c, log))
    derive(g)
    return g


@pytest.fixture(scope="module")
def g():
    return Graph().parse(PUBLISHED)


def count(g, sparql):
    return int(next(iter(g.query(sparql, initNs=PREFIXES)))[0])


def test_published_file_is_what_the_pipeline_builds(built):
    with open(PUBLISHED, "rb") as f:
        assert built.serialize(format="turtle").encode() == f.read()


def test_conforms_to_the_profile(g):
    conforms, results = validate(g)
    assert conforms and not [r for r in results if r[0] == "Violation"]


@pytest.mark.parametrize("sparql, expected", [
    ("SELECT (COUNT(?p) AS ?n) { ?p a foaf:Person FILTER isIRI(?p) }", 12913),
    ("SELECT (COUNT(?t) AS ?n) { ?t a dbo:SportsTeam FILTER NOT EXISTS { ?t dbo:gender ?g } }", 2143),
    ("SELECT (COUNT(?t) AS ?n) { ?t a dbo:SportsTeam ; dbo:gender ?g }", 3153),
    ("SELECT (COUNT(?t) AS ?n) { ?t a dbo:SportsTeam FILTER NOT EXISTS { ?t dbo:gender ?g }"
     " FILTER NOT EXISTS { ?a org:memberOf ?t } FILTER NOT EXISTS { ?a org:memberOf/org:subOrganizationOf ?t } }", 4),
    ("SELECT (COUNT(?m) AS ?n) { ?m a org:Membership }", 394),
    ("SELECT (COUNT(DISTINCT ?c) AS ?n) { ?m org:member ?c }", 393),
    ("SELECT (COUNT(DISTINCT ?a) AS ?n) { ?a org:memberOf ?t }", 11645),
    ("SELECT (COUNT(DISTINCT ?o) AS ?n) { ?o oly:officiatesIn ?d }", 875),
    ("SELECT (COUNT(?a) AS ?n) { ?a a oly:MedalAward }", 2401),
    ("SELECT (COUNT(*) AS ?n) { SELECT DISTINCT ?e ?t ?team { ?a oly:inEvent ?e ; oly:medalType ?t ; oly:wonBy ?team } }", 1080),
    ("SELECT (COUNT(?e) AS ?n) { ?e a dbo:SportsEvent }", 339),
    ("SELECT (COUNT(?n) AS ?x) { ?n a org:FormalOrganization }", 206),
    ("SELECT (COUNT(?c) AS ?n) { ?c a dbo:Country }", 111),
    ("SELECT (COUNT(*) AS ?n) { ?c oly:coachesAthlete ?a }", 6423),
    ("SELECT (COUNT(?p) AS ?n) { ?p a foaf:Person FILTER isIRI(?p) FILTER NOT EXISTS { ?p dbo:gender ?g } }", 159),
])
def test_figure(g, sparql, expected):
    assert count(g, sparql) == expected


@pytest.mark.parametrize("scheme, expected", [("discipline", 46), ("function", 13), ("medal-type", 3),
                                              ("event-category", 4)])
def test_code_list_size(g, scheme, expected):
    assert len(set(g.subjects(SKOS.inScheme, SCHEME[scheme]))) == expected


def test_medal_table_rebuilt_from_awards(g):
    """Medal counts are computed, not stored : they must equal medals_total.csv for all 93 NOCs."""
    rows = g.query("""
        SELECT ?code ?type (COUNT(*) AS ?n) {
          SELECT DISTINCT ?code ?type ?e ?team {
            ?a oly:inEvent ?e ; oly:medalType ?t ; oly:wonBy ?team .
            ?team org:subOrganizationOf/org:identifier ?code . ?t skos:prefLabel ?type } }
        GROUP BY ?code ?type""", initNs=PREFIXES)
    got = {(str(code), str(t)): int(n) for code, t, n in rows}
    with open(os.path.join(SOURCE, "medals_total.csv"), encoding="utf-8") as f:
        table = list(csv.DictReader(f))
    assert len(table) == 93
    for r in table:
        for t in ("Gold", "Silver", "Bronze"):
            assert got.get((r["Country Code"], t), 0) == int(r[f"{t} Medal"]), (r["Country Code"], t)


def test_every_noc_and_country_links_to_wikidata_except_logged(g):
    without = sorted(str(s) for cls in (ORG.FormalOrganization, DBO.Country)
                     for s in g.subjects(RDF.type, cls) if (s, OWL.sameAs, None) not in g)
    assert without == [str(ID["noc/eor"])]


def test_no_schema_org(g):
    assert not [t for t in g for x in t if "schema.org" in str(x)]


def test_minted_terms_are_the_ontology(g):
    onto = Graph().parse(os.path.join(ROOT, "ontology", "oly.ttl"))
    declared = {s for s in onto.subjects(RDF.type, None) if str(s).startswith(str(OLY))}
    used = {x for t in g for x in (t[1], t[2]) if isinstance(x, URIRef) and str(x).startswith(str(OLY))}
    assert used == declared and len(declared) == 9


def test_sample_is_part_of_the_data(g):
    """The hand-written SHACL sample (real source rows) is reproduced by the pipeline, except the
    dataset record (its date and description belong to the release)."""
    sample = Graph().parse(os.path.join(ROOT, "shacl", "examples", "valid-sample.ttl"))
    missing = [t for t in sample if isinstance(t[0], URIRef) and not str(t[0]).endswith("/dataset")
               and t not in g]
    assert missing == []


def test_iris_are_source_keys_without_names(g):
    pattern = re.compile(r"^https://w3id\.org/olympic-lod/tokyo2020/id/[a-z]+/[a-z0-9-]+$")
    assert all(pattern.match(str(s)) for s in set(g.subjects()) if str(s).startswith(str(ID)))
    assert (URIRef(ID["person/1440267"]), FOAF.name, None) in g


def test_no_dangling_internal_links(g):
    """Every IRI of ours that is used as a value is also described in the graph."""
    ours = (str(ID), str(SCHEME))
    described = set(g.subjects(RDF.type, None))
    dangling = {o for o in g.objects() if isinstance(o, URIRef) and str(o).startswith(ours) and o not in described}
    assert dangling == set()


def test_every_person_has_a_role(g):
    """Roles are links (athlete: member of; coach: coaching role; official: officiates in)."""
    assert count(g, """SELECT (COUNT(?p) AS ?n) { ?p a foaf:Person FILTER isIRI(?p)
        FILTER NOT EXISTS { ?p org:memberOf ?t } FILTER NOT EXISTS { ?m org:member ?p }
        FILTER NOT EXISTS { ?p oly:officiatesIn ?d } }""") == 0


def test_hand_chosen_wikidata_items_are_in_the_snapshot():
    from config import table
    links, snap = table("wikidata_links"), table("wikidata_snapshot")
    chosen = {links["games"], *links["medal_type"].values(), *links["discipline"].values(),
              *(q for k, q in links["noc_overrides"].items() if not k.startswith("_"))} - {None}
    assert chosen <= set(snap["labels"])


@pytest.mark.parametrize("corrupt", [
    "DELETE WHERE { <https://w3id.org/olympic-lod/tokyo2020/id/person/1440267> foaf:name ?n }",
    "DELETE { ?a oly:wonBy ?t } INSERT { ?a oly:wonBy <https://w3id.org/olympic-lod/tokyo2020/id/team/kor-arc-men> }"
    " WHERE { ?a oly:wonBy ?t FILTER (?t = <https://w3id.org/olympic-lod/tokyo2020/id/team/kor-arc>) }",
    "INSERT DATA { <https://w3id.org/olympic-lod/tokyo2020/id/person/1440267> foaf:birthday \"1990-01-01\" }",
], ids=["person-without-name", "medal-won-by-squad", "personal-data-added"])
def test_pipeline_refuses_a_corrupted_graph(built, corrupt):
    """The validation stage fails on the full graph, not only on the hand-made sample."""
    bad = Graph()
    for t in built:
        bad.add(t)
    bad.update(corrupt, initNs=PREFIXES)
    conforms, results = validate(bad)
    assert not conforms and any(r[0] == "Violation" for r in results)
