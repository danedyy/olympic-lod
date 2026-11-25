"""Stage 4 — Map to RDF, following the constraints matrix (ldap/constraints-matrix.csv).

Only the terms of the matrix are used; instance IRIs are built from source keys (stable,
source-traceable, lowercase, no names):
  person/{n} · team/{noc}-{disc}[-{men|women}] · membership/{person}-{team key} · noc/{ioc}
  country/{iso3} · event/{disc}-{event} · medal/{person}-{disc}-{event} · games/tokyo2020
('+' in an event name is written 'plus': 'Men +80kg' → men-plus-80kg)
"""
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import DCAT, DCTERMS, FOAF, ORG, OWL, RDF, SKOS, XSD

from config import (CREATORS, DATASET, DBO, ID, ISSUED, KAGGLE, LICENSE, OLY, PREFIXES, RESULTS,
                    SCHEME, SEX, VERSION, WD, slug, unit_key)

SCHEMES = {"discipline": "Discipline", "function": "Function", "medal-type": "Medal type",
           "event-category": "Event category"}
CATEGORY_CODES = {"men": "M", "women": "W", "mixed": "X", "open": "O"}
GAMES = ID["games/tokyo2020"]


def person(p):
    return ID[f"person/{p}"]


def unit(noc, disc, sex=None):
    return ID["team/" + unit_key(noc, disc, sex)]


def concept(scheme, key):
    return SCHEME[f"{scheme}/{key}"]


def event_key(disc, name):
    """{disc}-{event}; '+' is spelled out, so 'Men +80kg' and 'Men -80kg' stay two events."""
    return f"{disc.lower()}-{slug(name.replace('+', ' plus '))}"


def event(disc, name):
    return ID["event/" + event_key(disc, name)]


def to_rdf(clean, teams, links):
    g = Graph()
    for prefix, ns in PREFIXES.items():
        g.bind(prefix, ns)
    add = g.add

    # Code lists (rows 42–47)
    for key, title in SCHEMES.items():
        add((SCHEME[key], RDF.type, SKOS.ConceptScheme))
        add((SCHEME[key], SKOS.prefLabel, Literal(title, lang="en")))

    def entry(scheme, key, label, notation=None, match=None, extra_type=None):
        c = concept(scheme, key)
        add((c, RDF.type, SKOS.Concept))
        if extra_type:
            add((c, RDF.type, extra_type))
        add((c, SKOS.prefLabel, Literal(label, lang="en")))
        add((c, SKOS.inScheme, SCHEME[scheme]))
        if notation:
            add((c, SKOS.notation, Literal(notation)))
        if match:
            add((c, SKOS.exactMatch, WD[match]))

    for code, name in clean["disciplines"].items():
        entry("discipline", code.lower(), name, code, links["discipline"].get(code))
    for f in clean["functions"]:
        entry("function", slug(f), f, extra_type=ORG.Role)
    for key, q in links["medal_type"].items():
        entry("medal-type", key, key.capitalize(), match=q)
    for key, code in CATEGORY_CODES.items():
        entry("event-category", key, key, code)

    # People (rows 1–9); roles come from the links below
    for p, rec in clean["people"].items():
        s = person(p)
        add((s, RDF.type, FOAF.Person))
        add((s, FOAF.name, Literal(rec["name"])))
        if rec["sex"]:
            add((s, DBO.gender, SEX[rec["sex"]]))
        for page in rec["pages"]:
            add((s, FOAF.isPrimaryTopicOf, URIRef(page)))
    for p, units in teams["member"].items():
        for key in units:
            add((person(p), ORG.memberOf, unit(*key)))
    for p, rec in clean["officials"].items():
        s = person(p)
        for f in rec["function"]:
            add((s, OLY.officiatesAs, concept("function", slug(f))))
        for d in rec["disc"]:
            add((s, OLY.officiatesIn, concept("discipline", d.lower())))
        for iso in rec["country"]:
            add((s, DBO.nationality, ID[f"country/{iso.lower()}"]))

    # Teams and squads (rows 10–15)
    for noc, disc in teams["teams"]:
        t = unit(noc, disc)
        add((t, RDF.type, DBO.SportsTeam))
        add((t, FOAF.name, Literal(f"{clean['nocs'][noc]} · {clean['disciplines'][disc]}")))
        add((t, ORG.subOrganizationOf, ID[f"noc/{noc.lower()}"]))
        add((t, DBO.sport, concept("discipline", disc.lower())))
    for noc, disc, sex in teams["squads"]:
        s = unit(noc, disc, sex)
        add((s, RDF.type, DBO.SportsTeam))
        add((s, ORG.subOrganizationOf, unit(noc, disc)))
        add((s, DBO.gender, SEX[sex]))

    # Coaching roles (rows 16–19)
    for p, units in teams["coach_of"].items():
        for noc, disc, sex, function in units:
            m = ID[f"membership/{p}-{unit_key(noc, disc, sex)}"]
            add((m, RDF.type, ORG.Membership))
            add((m, ORG.member, person(p)))
            add((m, ORG.organization, unit(noc, disc, sex)))
            add((m, ORG.role, concept("function", slug(function))))

    # NOCs and countries (rows 20–27)
    for code, name in clean["nocs"].items():
        n = ID[f"noc/{code.lower()}"]
        add((n, RDF.type, ORG.FormalOrganization))
        add((n, FOAF.name, Literal(name)))
        add((n, ORG.identifier, Literal(code)))
        if code in links["noc"]:
            add((n, OWL.sameAs, WD[links["noc"][code]]))
    for iso, name in clean["countries"].items():
        c = ID[f"country/{iso.lower()}"]
        add((c, RDF.type, DBO.Country))
        add((c, FOAF.name, Literal(name)))
        add((c, DCTERMS.identifier, Literal(iso)))
        if iso in links["country"]:
            add((c, OWL.sameAs, WD[links["country"][iso]]))

    # The Games, events and medal awards (rows 28–41)
    add((GAMES, RDF.type, DBO.Olympics))
    add((GAMES, FOAF.name, Literal("Tokyo 2020 Olympic Games")))
    add((GAMES, OWL.sameAs, WD[links["games"]]))
    for x in clean["medals"]:
        e = event(x["disc"], x["event"])
        add((e, RDF.type, DBO.SportsEvent))
        add((e, FOAF.name, Literal(x["event"])))
        add((e, DBO.sport, concept("discipline", x["disc"].lower())))
        add((e, OLY.eventCategory, concept("event-category", x["category"])))
        add((e, DCTERMS.isPartOf, GAMES))
        a = ID[f"medal/{x['pid']}-{event_key(x['disc'], x['event'])}"]
        add((a, RDF.type, OLY.MedalAward))
        add((a, OLY.awardedTo, person(x["pid"])))
        add((a, OLY.inEvent, e))
        add((a, OLY.wonBy, unit(x["noc"], x["disc"])))
        add((a, OLY.medalType, concept("medal-type", x["medal"])))
        add((a, DCTERMS.date, Literal(x["date"], datatype=XSD.date)))

    # The dataset (rows 48–54)
    d = URIRef(DATASET)
    add((d, RDF.type, DCAT.Dataset))
    add((d, DCTERMS.title, Literal("Tokyo 2020 Olympic Games as Linked Open Data", lang="en")))
    add((d, DCTERMS.description, Literal(
        "Athletes, coaches, technical officials, teams, events and medals of the Tokyo 2020 Olympic Games, "
        "converted from the Kaggle CSV dump (a 2021 snapshot) to 5-star Linked Open Data and validated "
        f"against the Olympic LOD application profile (SHACL). Release {VERSION}; links to Wikidata from a "
        f"snapshot retrieved on {links['retrieved']}.", lang="en")))
    add((d, DCTERMS.license, URIRef(LICENSE)))
    for i, name in enumerate(CREATORS, 1):
        c = BNode(f"creator{i}")
        add((d, DCTERMS.creator, c))
        add((c, RDF.type, FOAF.Person))
        add((c, FOAF.name, Literal(name)))
    add((d, DCTERMS.source, URIRef(KAGGLE)))
    add((d, DCTERMS.source, URIRef(RESULTS)))
    add((d, DCTERMS.issued, Literal(ISSUED, datatype=XSD.date)))
    return g
