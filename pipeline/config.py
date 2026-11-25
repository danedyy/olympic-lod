"""Paths, namespaces and IRI patterns shared by every pipeline stage.

IRI patterns and namespaces follow the application profile (ldap/constraints-matrix.csv).
"""
import json
import os
import re

from rdflib import Namespace
from rdflib.namespace import DCAT, DCTERMS, FOAF, ORG, OWL, RDF, RDFS, SKOS, XSD

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOURCE = os.path.join(ROOT, "data", "source")
OUT = os.path.join(ROOT, "data", "rdf")
TABLES = os.path.join(HERE, "decision_tables")
SHAPES = os.path.join(ROOT, "shacl", "olympic-lod-shapes.ttl")

FILES = ["athletes", "coaches", "technical_officials", "medals", "medals_total"]

# Release metadata of this snapshot (dcat:Dataset). Fixed, so that a re-run
# gives a byte-identical graph.
VERSION = "1.0.0"
ISSUED = "2026-11-25"

BASE = "https://w3id.org/olympic-lod/"
OLY = Namespace(BASE + "ontology#")
SCHEME = Namespace(BASE + "scheme/")
ID = Namespace(BASE + "tokyo2020/id/")
DATASET = BASE + "tokyo2020/dataset"
DBO = Namespace("http://dbpedia.org/ontology/")
EUSEX = Namespace("http://publications.europa.eu/resource/authority/human-sex/")
WD = Namespace("http://www.wikidata.org/entity/")

# Absolute base of the source's relative profile links (../../../en/results/…);
# confirmed on the Wayback Machine (snapshot of 4 Aug 2021).
RESULTS = "https://olympics.com/tokyo-2020/olympic-games/en/results/"
KAGGLE = "https://www.kaggle.com/datasets/piterfm/tokyo-2020-olympics"
LICENSE = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
CREATORS = ["Daniel Samuel Edim", "Ahmad Imran"]

PREFIXES = {
    "rdf": RDF, "rdfs": RDFS, "xsd": XSD, "owl": OWL, "foaf": FOAF, "org": ORG,
    "dbo": DBO, "skos": SKOS, "dcterms": DCTERMS, "dcat": DCAT, "eusex": EUSEX,
    "oly": OLY, "wd": WD,
}

SEX = {"men": EUSEX.MALE, "women": EUSEX.FEMALE}


def table(name):
    with open(os.path.join(TABLES, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def unit_key(noc, disc, gender=None):
    """{noc}-{discipline}[-{men|women}]: the key of a Team or a Squad."""
    return "-".join(k.lower() for k in (noc, disc, gender) if k)
