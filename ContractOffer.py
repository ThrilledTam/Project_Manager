import random


def classify_team(team, all_teams):
    # simple perf-based classification
    perfs = [t.getPerf() for t in all_teams]
    sorted_perfs = sorted(perfs, reverse=True)
    tier1_cut = sorted_perfs[len(sorted_perfs)//3]
    tier2_cut = sorted_perfs[(2*len(sorted_perfs))//3]
    if team.getPerf() >= tier1_cut:
        return "front"
    elif team.getPerf() >= tier2_cut:
        return "mid"
    else:
        return "back"

def build_candidate_pool(team, all_drivers, free_agents, f2_drivers):
    # drivers currently without contract next year but on grid
    current_grid_free = [d for d in all_drivers if d.getContractLeft()==0 and d.getTeamAt()!= "Free Agent" and d.getTeamAt()!="Formula 2"]
    return current_grid_free + free_agents + f2_drivers

def choose_best_candidate(team, tier, candidates, season_results=None):
    """
    tier: "front", "mid", or "back"
    candidates: list of driver objects
    season_results: optional dict {driver: points/standing}
                    if you have standings already calculated
    """
    if not candidates:
        return None

    # Default: derive "visible performance" from points or bestPos
    def visible_score(d): # TODO: Fix transfer system.
        # You can plug in your own season stats here
        # Prefer points if you track them, else bestPos
        pts = d.getDriverPoints()
        bestpos = d.getBestPos() if d.getBestPos() is not None else 99
        ovrAll = 1.00
        if (d.getTeamAt() == "Formula 1"):
            if d.getTeamAt().getPoints() > 0:
                if d.getTeamAt().getDriver1() == d:
                    dPts = d.getTeamAt().getDriver1().getDriverPoints()
                    tPts = d.getTeamAt().getPoints()
                    rep = (d.getDriverRep() + (d.getDriverCha() / 4))
                    ovrAll = ((dPts / tPts) * 2.0) + (rep * 0.5) + (dPts / 20)
                elif d.getTeamAt().getDriver2() == d:
                    dPts = d.getTeamAt().getDriver2().getDriverPoints()
                    tPts = d.getTeamAt().getPoints()
                    rep = (d.getDriverRep() + (d.getDriverCha() / 4))
                    ovrAll = ((dPts / tPts) * 2.0) + (rep * 0.5) + (dPts / 20)
            else:
                if d.getTeamAt().getDriver1() == d:
                    rep = (d.getDriverRep() + (d.getDriverCha() / 4))
                    ovrAll = (0.5) + (rep * 1.0)
                elif d.getTeamAt().getDriver2() == d:
                    rep = (d.getDriverRep() + (d.getDriverCha() / 4))
                    ovrAll = (0.5) + (rep * 1.0)
        return (ovrAll, pts, -bestpos)  # higher ptsPerc, higher pts, lower bestpos is better

    if tier in ("front", "mid"):

        # rank by reputation
        def exp_score(d):
            team_at = d.getTeamAt()
            if team_at == "Formula 2":
                score = (d.getDriverRep() * 1.00) + (d.getDriverCha() / 7)
            elif team_at == "Free Agent":
                score = (d.getDriverRep() * 1.00) + (d.getDriverCha() / 7)
            else:
                score = (d.getDriverRep() * 1.10) + (d.getDriverCha() / 7)
                if team_at == team:
                    score *= 1.25
            return score

        # free agents/F2 get slight boost:
        def source_bonus(d):
            team_at = d.getTeamAt()
            if team_at == "Free Agent":
                return 4  # adjust
            elif team_at == "Formula 2":
                return 2  # adjust
            return 0

        candidates.sort(
            key=lambda d: (exp_score(d), source_bonus(d)),
            reverse=True
        )

    else:
        def exp_score(d):
            team_at = d.getTeamAt()
            if team_at == "Formula 2":
                score = (d.getDriverRep() * 1.25) + (d.getDriverCha() / 7)
            elif team_at == "Free Agent":
                score = (d.getDriverRep() * 1.00) + (d.getDriverCha() / 7)
            else:
                score = (d.getDriverRep() * 1.00) + (d.getDriverCha() / 7)
                if team_at == team:
                    score *= 1.25
            return score

        # free agents/F2 get slight boost:
        def source_bonus(d):
            team_at = d.getTeamAt()
            if team_at == "Free Agent":
                return 4  # adjust
            elif team_at == "Formula 2":
                return 2  # adjust
            return 0

        candidates.sort(
            key=lambda d: (exp_score(d), source_bonus(d)),
            reverse=True
        )

        # TODO: Fix transfer system.
        '''
        # rank by who actually performed better this season
        # (points first, then best finish)
        candidates.sort(key=lambda d: visible_score(d), reverse=True)
        '''

    if tier in ("front"):
        retCans = [candidates[0]]
    elif tier in ("mid"):
        retCans = [candidates[0], candidates[0], candidates[1], candidates[2]]
    else:
        retCans = [candidates[0], candidates[1], candidates[2]]
    return random.choice(retCans)