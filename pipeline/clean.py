"""Stage 2 — Clean & prepare, with deterministic rules only (see README, Design choices).

* Personal data not needed by the model is dropped: only the columns read here survive.
* Person ID = the number after '-n' in the profile link; the link is made absolute.
* Medal dates lose their dummy time; medals.athlete_sex becomes the event category.
* Official function spellings are merged; country names become ISO 3166-1 alpha-3.
* Duplicates and gaps are kept as the source gives them and written to the issues log.
"""
import collections
import re

import pycountry

from config import RESULTS, table

_PID = re.compile(r"-n(\d+)-")
_RELATIVE = "../../../en/results/"
MEDALS = {"Gold Medal": "gold", "Silver Medal": "silver", "Bronze Medal": "bronze"}
SEX = {"Male": "men", "Female": "women"}


def pid(url):
    m = _PID.search(url)
    if not m:
        raise ValueError("no person id in " + url)
    return m.group(1)


def absolute(url):
    if not url.startswith(_RELATIVE):
        raise ValueError("unexpected profile link " + url)
    return RESULTS + url[len(_RELATIVE):]


def iso3(name, overrides):
    if name in overrides:
        return overrides[name][0]
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return pycountry.countries.search_fuzzy(name)[0].alpha_3


def clean(raw, log):
    rules = table("mapping_rules")
    a, c, o, m = raw["athletes"], raw["coaches"], raw["technical_officials"], raw["medals"]

    disciplines = {x["discipline_code"]: x["discipline"] for x in a + m if x["discipline_code"]}
    disc_code = {name: code for code, name in disciplines.items()}
    nocs = {x["country_code"]: x["country"] for x in a}
    for code, note in rules["noc_notes"].items():
        log.add("clean", "athletes.csv", "", code, f"NOC name '{nocs[code]}': {note}", "name kept as in the source")

    people = {}

    def person(row, file, line, sex):
        p = pid(row["url"])
        rec = people.setdefault(p, {"name": row["name"], "sex": sex, "pages": set()})
        if rec["sex"] != sex:
            raise SystemExit(f"{file}:{line}: person {p} has a second sex")
        if rec["name"] != row["name"]:
            log.add("clean", file, line, p, f"second spelling of the name: '{row['name']}'",
                    f"kept the first spelling '{rec['name']}' (foaf:name is 1..1)")
        rec["pages"].add(absolute(row["url"]))
        return p

    athletes = []
    for i, x in enumerate(a, 2):
        sex = SEX.get(x["gender"])
        p = person(x, "athletes.csv", i, sex)
        if not sex:
            log.add("clean", "athletes.csv", i, p, "no gender in the source", "dbo:gender left empty (never guessed)")
        athletes.append({"pid": p, "noc": x["country_code"], "disc": x["discipline_code"], "sex": sex, "line": i})

    coaches = []
    for i, x in enumerate(c, 2):
        p = person(x, "coaches.csv", i, SEX[x["gender"]])
        coaches.append({"pid": p, "noc": x["country_code"], "disc": disc_code[x["discipline"]],
                        "function": x["function"], "unit_sex": rules["coach_event_to_gender"][x["event"]]})

    overrides = rules["country_name_overrides"]
    countries = {}
    officials = collections.defaultdict(lambda: {"function": set(), "disc": set(), "country": set(), "lines": []})
    for i, x in enumerate(o, 2):
        p = person(x, "technical_officials.csv", i, SEX[x["gender"]])
        iso = iso3(x["country"], overrides)
        countries[iso] = pycountry.countries.get(alpha_3=iso).name
        rec = officials[p]
        rec["function"].add(rules["function_merges"].get(x["function"], x["function"]))
        rec["disc"].add(disc_code[x["discipline"]])
        rec["country"].add(iso)
        rec["lines"].append(i)
    for p, rec in sorted(officials.items()):
        if len(rec["lines"]) < 2:
            continue
        line = rec["lines"][0]
        if len(rec["function"]) > 1:
            raise SystemExit(f"official {p} has two functions: {rec['function']}")
        if len(rec["disc"]) > 1:
            log.add("clean", "technical_officials.csv", line, p,
                    f"listed in {' and '.join(sorted(disciplines[d] for d in rec['disc']))} (possible scraping error)",
                    "kept both oly:officiatesIn links")
        if len(rec["country"]) > 1:
            log.add("clean", "technical_officials.csv", line, p,
                    f"same ID under two nationalities: {', '.join(sorted(rec['country']))}",
                    "kept both dbo:nationality links")
        if len(rec["disc"]) == 1 and len(rec["country"]) == 1:
            log.add("clean", "technical_officials.csv", line, p, "same official on two identical rows", "merged into one person")

    medals = []
    for i, x in enumerate(m, 2):
        medals.append({"pid": pid(x["athlete_link"]), "medal": MEDALS[x["medal_type"]],
                       "date": x["medal_date"][:10], "category": rules["medal_event_category"][x["athlete_sex"]],
                       "noc": x["country_code"], "disc": x["discipline_code"], "event": x["event"]})
        if pid(x["athlete_link"]) not in people:
            raise SystemExit(f"medals.csv:{i}: medal winner is not in athletes.csv")

    return {
        "people": people, "athletes": athletes, "coaches": coaches, "officials": dict(officials),
        "medals": medals, "disciplines": disciplines, "nocs": nocs, "countries": countries,
        "functions": sorted({x["function"] for x in coaches} | {f for r in officials.values() for f in r["function"]}),
        "medals_total": raw["medals_total"],
    }
