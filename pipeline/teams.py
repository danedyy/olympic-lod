"""Stage 2b — Teams, squads and coaching roles (see README, Design choices).

* Team  = NOC + discipline. Every athlete and every coach belongs to one.
* Squad = Team + men/women, only where the source gives the gender and the sport is split
          by gender (no squads in Equestrian).
* An athlete with no gender is placed in a squad from a medal in a men's (M) or women's (W)
  event if there is one; otherwise the athlete joins the Team directly (never guessed).
* A coach goes to the unit named by the 'event' column (mapping_rules.json); empty → the Team.
"""
import collections

from config import table


def build(clean, log):
    rules = table("mapping_rules")
    open_disc = set(rules["open_disciplines_without_squads"])
    medal_sex = {x["pid"]: x["category"] for x in clean["medals"] if x["category"] in ("men", "women")}

    member = collections.defaultdict(set)        # athlete -> {(noc, disc, sex|None)}
    for x in clean["athletes"]:
        sex = x["sex"]
        if not sex and x["pid"] in medal_sex:
            sex = medal_sex[x["pid"]]
            log.add("teams", "athletes.csv", x["line"], x["pid"],
                    f"no gender; medal in a {sex}'s event", f"member of the {sex}'s squad")
        elif not sex and x["disc"] not in open_disc:
            log.add("teams", "athletes.csv", x["line"], x["pid"], "no gender", "member of the Team directly (no squad)")
        if x["disc"] in open_disc:
            sex = None
        member[x["pid"]].add((x["noc"], x["disc"], sex))
    for p, units in sorted(member.items()):
        if len({(n, d) for n, d, _ in units}) > 1:
            log.add("teams", "athletes.csv", "", p, "athlete listed in two disciplines", "member of both teams")

    coach_of = collections.defaultdict(set)      # coach -> {(noc, disc, sex|None, function)}
    for x in clean["coaches"]:
        coach_of[x["pid"]].add((x["noc"], x["disc"], x["unit_sex"], x["function"]))

    teams = {(n, d) for v in member.values() for n, d, _ in v} | {(n, d) for v in coach_of.values() for n, d, _, _ in v}
    squads = {k for v in member.values() for k in v if k[2]} | {(n, d, s) for v in coach_of.values() for n, d, s, _ in v if s}
    for t in sorted(teams - {(n, d) for v in member.values() for n, d, _ in v}):
        log.add("teams", "coaches.csv", "", "-".join(t), "team has coaches but no athletes in the source",
                "team created from the coach records")
    return {"member": dict(member), "coach_of": dict(coach_of), "teams": teams, "squads": squads}
