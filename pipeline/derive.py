"""Stage 4b — Derive oly:coachesAthlete (matrix row 9).

Never read from the source: coaches.csv names no athletes. A coach of a Team coaches every
member of the Team (directly or through its squads); a coach of a Squad only that squad.
"""
from config import PREFIXES

COACHES_ATHLETE = """
CONSTRUCT { ?coach oly:coachesAthlete ?athlete }
WHERE {
  ?role a org:Membership ; org:member ?coach ; org:organization ?unit .
  { ?athlete org:memberOf ?unit }
  UNION
  { ?athlete org:memberOf ?squad . ?squad org:subOrganizationOf ?unit . ?unit a dbo:SportsTeam }
}"""


def derive(g):
    derived = g.query(COACHES_ATHLETE, initNs=PREFIXES).graph
    g += derived
    return len(derived)
