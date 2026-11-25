# Olympic LOD — Tokyo 2020 Olympic Games as 5-star Linked Open Data

**Authors:** Daniel Samuel Edim (up202400301, <up202400301@edu.fe.up.pt>) · Ahmad Imran (up202403072, <up202403072@edu.fe.up.pt>) — Faculty of Engineering, University of Porto
**Release:** 1.0.0 (25 Nov 2026) · **DOI:** _added after the Zenodo release_

The Kaggle *Tokyo 2020 Olympic Summer Games* dataset is five CSV files with no identifiers and no
links, so it is worth 3 stars at most on the 5-star Open Data scale. This project turns it into
**5-star Linked Open Data**:

* **application profile:** the terms used, how they combine and the constraints a valid record meets;
* **SHACL shapes:** the same profile in a form a machine can check;
* **pipeline:** converts the CSVs into an RDF graph and refuses to publish it unless it conforms.

| | |
|---|---|
| The 5-star data | [`data/rdf/tokyo2020.ttl`](data/rdf/tokyo2020.ttl): 109,679 triples, **0 SHACL violations** |
| The profile as SHACL | [`shacl/olympic-lod-shapes.ttl`](shacl/olympic-lod-shapes.ttl): 24 node shapes, SHACL Core |
| The profile as tables | [`ldap/`](ldap/): vocabulary alignment, constraints matrix (54 rows), terms to mint |
| The minted terms | [`ontology/oly.ttl`](ontology/oly.ttl): 9 terms, `https://w3id.org/olympic-lod/ontology#` |

## From 3 to 5 stars

| Star | Source (Kaggle CSV) | This dataset |
|---|---|---|
| ★ open licence | CC BY-NC-SA 4.0 (NC: limited openness, see [`LICENSE-DATA.md`](LICENSE-DATA.md)) | same licence, declared in DCAT |
| ★★ machine-readable | yes | yes |
| ★★★ open format | CSV | RDF (Turtle) |
| ★★★★ URIs | none (only relative profile links) | every person, team, NOC, event, medal and code has an IRI under `https://w3id.org/olympic-lod/` |
| ★★★★★ linked | none | `owl:sameAs` / `skos:exactMatch` to Wikidata for 205 NOCs, 111 countries, 45 disciplines, 3 medal types and the Games; profile pages on olympics.com |

## The model

| Thing | Class | Key links |
|---|---|---|
| Person (athlete, coach or official) | `foaf:Person` | `foaf:name`, `dbo:gender` (EU human-sex), `foaf:isPrimaryTopicOf` |
| Team (NOC + discipline) / Squad (Team + men/women) | `dbo:SportsTeam` | `org:subOrganizationOf`, `dbo:sport`; athletes `org:memberOf` |
| Coaching role | `org:Membership` | `org:member`, `org:organization`, `org:role` |
| NOC / Country | `org:FormalOrganization` / `dbo:Country` | `org:identifier` (IOC), `dcterms:identifier` (ISO), `owl:sameAs` |
| Medal event / the Games | `dbo:SportsEvent` / `dbo:Olympics` | `oly:eventCategory`, `dcterms:isPartOf` |
| Medal award | `oly:MedalAward` | `oly:awardedTo`, `oly:inEvent`, `oly:wonBy`, `oly:medalType`, `dcterms:date` |
| Code lists | `skos:Concept` in 4 `skos:ConceptScheme`s | discipline, function (also `org:Role`), medal type, event category |
| Dataset | `dcat:Dataset` | title, description, licence, creators, sources, issued |

IRI patterns (every key comes from a source value; lowercase; no names):

| Thing | Pattern | Example |
|---|---|---|
| Person | `tokyo2020/id/person/{n}` | `…/id/person/1440267` |
| Team · Squad | `tokyo2020/id/team/{noc}-{disc}[-{men\|women}]` | `…/id/team/egy-fbl-men` |
| Coaching role | `tokyo2020/id/membership/{person}-{team key}` | `…/id/membership/1378828-egy-fbl` |
| NOC · Country | `tokyo2020/id/noc/{ioc}` · `tokyo2020/id/country/{iso3}` | `…/id/noc/kor` · `…/id/country/uzb` |
| Event · Medal | `tokyo2020/id/event/{disc}-{event}` · `tokyo2020/id/medal/{person}-{disc}-{event}` | `…/id/event/arc-mixed-team` |
| Code-list entry | `scheme/{list}/{value}` | `https://w3id.org/olympic-lod/scheme/discipline/arc` |

## Design choices

**The model follows the data.** It was built from what the five files actually contain, not from an ideal schema.

People:
* **One Person class.** Being an athlete, a coach or an official is a link (member of, coaching role,
  officiates in), not a subclass. No person appears in two files.
* **Personal data left out.** Birth dates, birthplaces, residences and heights are not needed, so they are dropped.
  Sex is kept because competition is organised by sex.
* **Never guess.** 159 athletes have no sex in the source, so they get none (a SHACL warning, not an error).
  - 19 of them won a medal in a men's or women's event, which places them in that squad.
  - The other 140 belong to their Team directly.

Teams and coaches:
* **Team and Squad.** A Team is one nation in one discipline. A Squad is its men's or women's side, only where the
  sport is split by sex (none in Equestrian). Every athlete and every coach belongs to one.
* **Coaching roles.** A coach is linked to a Team or Squad through an `org:Membership` with a role
  (Coach / Head Coach), following the `event` column: Men → men's squad, Women/Duet/Team → women's squad,
  empty → the whole Team.
* **`oly:coachesAthlete` is derived, never stored.** The source never says which athlete a coach coaches.
  The pipeline derives it from the memberships (6,423 pairs). A women's coach is never linked to men.

Medals and events:
* **Medal award as its own node.** One property cannot connect a person, an event, a medal type and the
  team the medal counts for, so a medal award is a node of its own.
  - The team is always a Team, never a Squad.
  - Medal counts and the ranking are computed by query, not stored. The tests rebuild the official
    medal table from the awards for all 93 NOCs.
* **Event category.** The medals file's `athlete_sex` column (M/W/X/O) describes the event (men / women /
  mixed / open), not the person.

Vocabularies:
* **Ontologies only.** Every term comes from FOAF, the W3C ORG ontology, the DBpedia ontology, SKOS,
  DCTERMS, DCAT or OWL. Sex values come from the EU human-sex authority table.
  - schema.org was considered but not used: it declares no formal domains or ranges.
  - Terms are minted (`oly:`) only where no existing term fits: medal awards, event categories, technical officials.
* **Candidate scoring.** Each candidate was scored on semantic fit, adoption (LOV figures) and parsimony
  (prefer vocabularies already used). [`ldap/vocabulary-alignment.csv`](ldap/vocabulary-alignment.csv) shows every candidate and the reason for each choice.

Links and data quality:
* **Links to Wikidata.** Each NOC links to its own "national Olympic committee" item, never to the
  country (a NOC is not a country). There are 16 ambiguous cases, chosen by hand and listed in
  [`pipeline/decision_tables/wikidata_links.json`](pipeline/decision_tables/wikidata_links.json).
  No link was added where there is no exact item:
  - the Refugee Olympic Team (a delegation, not a committee);
  - Baseball/Softball.
* **Source problems are kept and logged, not fixed silently.** For example:
  - 77 officials listed in both Diving and Water Polo;
  - one official with two nationalities;
  - one person with two spellings of the name (the first is kept);
  - NOC names missing in the source (LBN, EOR).

  All of them are in `data/rdf/issues-log.csv`.

## The pipeline

**Is it needed?** Yes. The SHACL file only *describes* valid data, and the 5-star graph has to be produced.
The pipeline is that production step. It is a script and not a one-off manual conversion so that
anyone can rebuild the published file from the CSVs, check that it is exactly what we published, and
see every rule that was applied.

The dataset is **static** (Kaggle: "update frequency: never"). The pipeline still runs the same way every time. It is:
* deterministic: a re-run gives a byte-identical file;
* offline: Wikidata is read from a saved snapshot;
* strict: a changed source file is rejected.

| Stage | File | What it does |
|---|---|---|
| 1. Ingest | `ingest.py` | reads the 5 CSVs; their SHA-256 must match `data/source/SHA256SUMS` |
| 2. Clean | `clean.py` | keeps only the columns the model needs; turns relative profile links into absolute olympics.com URLs; takes the person ID from the link; strips the dummy time from medal dates; maps officials' country names to ISO codes; merges two spellings of one function; logs duplicates and gaps |
| 2b. Teams | `teams.py` | builds Teams, Squads and coaching roles with the rules above |
| 3. Reconcile | `reconcile.py` | adds Wikidata links from the saved snapshot (`decision_tables/wikidata_snapshot.json`) and the hand choices |
| 4. Map | `to_rdf.py` | writes the RDF with exactly the terms and IRI patterns of the constraints matrix |
| 4b. Derive | `derive.py` | adds `oly:coachesAthlete` with a SPARQL CONSTRUCT |
| 5. Validate | `validate.py` | runs pySHACL against `shacl/olympic-lod-shapes.ttl`; any violation stops the run and nothing is published |
| 6. Publish | `run.py` | writes `data/rdf/` |

`fetch_wikidata.py` is separate. It queries Wikidata once and saves the snapshot with its date.
Run it again only to refresh the links, and commit the new snapshot on purpose.

### Run it

```bash
make setup           # create .venv and install the pinned dependencies
make run             # rebuild data/rdf/ in about 10 s; fails on any SHACL violation
make test            # run the 116 tests
make check           # before a release: run + test + check that data/rdf/ matches the last commit
make fetch-wikidata  # refresh the Wikidata snapshot (network), then run make check
make clean           # remove caches (make distclean also removes .venv)
```

`make` alone lists the tasks. Without make: `python3 pipeline/run.py` and `python3 -m pytest tests`, run inside the venv.

### Outputs

* `data/rdf/tokyo2020.ttl`: the 5-star dataset.
* `data/rdf/validation-report.csv`: every SHACL result. There are 0 violations and 161 warnings, all expected:
  * 159 people without sex;
  * the Refugee Olympic Team has no Wikidata committee item;
  * Baseball/Softball has no exact Wikidata item.
* `data/rdf/issues-log.csv`: 413 cases kept as the source gives them and flagged for manual review.

### Tests

* `tests/test_shacl.py` checks that the shapes say what the profile says:
  * a hand-written sample of real rows conforms;
  * 21 broken variants each fail for the intended reason;
  * 4 variants that only drop a recommended value still conform;
  * every one of the 54 matrix rows is in the shapes with the same cardinality;
  * no schema.org term is used.
* `tests/test_pipeline.py` checks the published data:
  * it is byte-identical to a fresh build and conforms to the shapes;
  * the counts measured on the CSVs hold: 12,913 people, 2,143 teams, 3,153 squads, 394 coaching roles, 2,401 medal awards = 1,080 team medals, 339 events, 206 NOCs, 111 countries;
  * the medal table matches for all 93 NOCs;
  * the minted terms used are exactly the 9 in the ontology;
  * the hand-written sample is reproduced from the source.

## Repository map

```
data/source/     the 5 Kaggle CSVs, unchanged, + SHA256SUMS
data/rdf/        pipeline output: the 5-star dataset, validation report, issues log
ldap/            the application profile as tables
shacl/           the profile as SHACL + examples/ (valid sample, broken/ and allowed/ cases)
ontology/        oly.ttl, the 9 minted terms
pipeline/        the conversion pipeline and its decision tables
tests/           pytest suite
w3id/            the w3id.org registration: redirects to GitHub Pages (see Releasing, step 6)
```

## Releasing (GitHub → Zenodo)

1. Run `make check`. Push to `https://github.com/danedyy/olympic-lod`. Turn on **GitHub Pages** (branch `main`, folder `/`).
2. On <https://zenodo.org>, log in with GitHub. Under *GitHub*, switch on `danedyy/olympic-lod`.
3. On GitHub, create the release **`v1.0.0`**. Zenodo archives it, reads `.zenodo.json` and mints **one DOI**.
   That record holds both snapshots: the project (profile, SHACL, ontology, pipeline) and the 5-star data,
   which is committed in `data/rdf/`.
4. On Zenodo, check the record (title, authors, licence CC BY-NC-SA 4.0, description) and note its DOI.
   Zenodo gives two DOIs:
   - the **version DOI**, for exactly v1.0.0: cite this one;
   - a **concept DOI**, which always points to the latest version.
5. Put the DOI in this README (the line at the top) and in `CITATION.cff` (`doi:`), and commit.
   Don't create a new release just for that: it would mint a new version DOI.
6. Register `w3id.org/olympic-lod`, so the IRIs resolve:
   - Check that `https://danedyy.github.io/olympic-lod/ontology/oly.ttl` opens (GitHub Pages, step 1).
   - Fork <https://github.com/perma-id/w3id.org> and copy the `w3id/olympic-lod/` folder (its `.htaccess` and
     `README.md`) to the root of the fork.
   - Open a pull request titled "Add olympic-lod". The redirects work once the w3id maintainers merge it.
   - Test: `curl -sI https://w3id.org/olympic-lod/ontology` should answer `303`, with a `Location` on GitHub Pages.
     The `ontology/1.0.0` redirect points at the `v1.0.0` tag, so it works only after step 3.

## Licence

Code (`pipeline/`, `tests/`): MIT ([`LICENSE`](LICENSE)).
Data and profile (`data/`, `ldap/`, `shacl/`, `ontology/`): CC BY-NC-SA 4.0, inherited from the source ([`LICENSE-DATA.md`](LICENSE-DATA.md)).
Source: Petro Ivaniuk, *Tokyo 2020 Olympic Summer Games*, Kaggle.
