#General Sport Rules
import random, Driver, math, Team

seasonLength = 12

regChangeYear = 2026    # Reg cycle starting year
regIntervals = 4        # Every four years

costCap = 32            # 32,000,000

#Regulation Change Method
def regChange (grid_avg, target, perf, research):
    # -------------------------------
    # 1. Base regulation reset
    base_loss = -target

    # -------------------------------
    # 2. Research with STRONG diminishing returns
    # 10M  → ~18 perf
    # 30M  → ~28 perf
    # 60M  → ~35 perf  (big teams can't brute-force)
    research_gain = 12 * math.log1p(research)

    # Hard cap: nobody can fully cancel regulations
    research_gain = min(research_gain, target * 0.70)

    # -------------------------------
    # 3. Catch-up boost (only if below avg)
    perf_gap = grid_avg - perf
    catchup_bonus = max(0, perf_gap * 0.35)

    # -------------------------------
    # 4. Regulation chaos
    chaos = random.uniform(-4, 4)

    # -------------------------------
    final_change = base_loss + research_gain + catchup_bonus + chaos
    new_perf = perf + final_change

    # -------------------------------
    # 5. Anti-collapse safety net
    new_perf = max(new_perf, grid_avg * 0.72)

    return round(new_perf, 2)

def regChange2 (grid_h, grid_l, grid_avg, target, perf, research):
    # TODO: REVAMP REG CHANGES
    grid_split = grid_h - grid_l

    new_perf = (100 + perf) / 2

def regSqueeze (arr): #Must accept list of team objects
    DChaPos = 0
    perf_list = []
    for i in range(len(arr)):
        perf_list.append(arr[i].getPerf())
    perf_list.sort(reverse=True)
    max_perf = perf_list[0]
    min_perf = perf_list[-1]
    perf_diff = max_perf - min_perf
    aTemp = (max_perf - 150) - min_perf

    for x in arr:
        DChaPos += 1
        weighted_perf = x.getPerf()
        if perf_diff > 150:
            weighted_perf = x.getPerf() + (aTemp * ((max_perf - x.getPerf()) / (max_perf - min_perf)))
        x.setPerf(weighted_perf)
        x.addMoney(DChaPos*1)

#Points System
def updatePointsDist (gridSize):
    pointsDist = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1] #Top 10 (default)
    if gridSize <= 22: pointsDist = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1] #Top 10
    elif 22 < gridSize <= 26: pointsDist = [25, 18, 15, 12, 10, 8, 6, 5, 4, 3, 2, 1] #Top 12
    elif 26 < gridSize: pointsDist = [25, 18, 15, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1] #Top 14 (GAME MAXIMUM)
    return pointsDist

#Driver Skill Updating System (DSUS)
def DSUS (d):
    def clampSkill(perf, minRating, maxRating, skillChange):
        newPerf = perf + skillChange
        if newPerf < minRating:
            return minRating - perf
        if newPerf > maxRating:
            return maxRating - perf
        return skillChange

    age = d.getDriverAge()
    perf = d.getDriverPerf()
    skillChange = 0

    if age == 12:
        skillChange += random.randint(2,4)
    elif age == 13:
        skillChange += random.randint(2,4)
    elif age == 14:
        skillChange += random.randint(2, 4)
    elif age == 15:
        skillChange += random.randint(2, 4)
    elif age == 16:
        skillChange += random.randint(2,4)
    elif age == 17:
        skillChange += random.randint(2,5)
    elif age == 18:
        skillChange += random.randint(2,5)
    elif age == 19:
        skillChange += random.randint(2,3)
    elif age == 20:
        skillChange += random.randint(2,3)
    elif age == 21:
        skillChange += random.randint(2,3)
    elif age == 22:
        skillChange += random.randint(1,2)
    elif age == 23:
        skillChange += random.randint(1,2)
    elif age == 24:
        skillChange += random.randint(1,2)
    elif age == 25:
        skillChange += random.randint(0,1)
        skillChange = clampSkill(perf, 71, 100, skillChange)
    elif age == 26:
        skillChange += random.randint(0,1)
        skillChange = clampSkill(perf, 72, 100, skillChange)
    elif age == 27:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 72, 99, skillChange)
    elif age == 28:
        skillChange += random.randint(0, 1) * -1
        skillChange = clampSkill(perf, 72, 98, skillChange)
    elif age == 29:
        skillChange += random.randint(0, 2) * -1
        skillChange = clampSkill(perf, 72, 96, skillChange)
    elif age == 30:
        skillChange += random.randint(1,2) * -1
        skillChange = clampSkill(perf, 71, 94, skillChange)
    elif age == 31:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 71, 93, skillChange)
    elif age == 32:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 71, 92, skillChange)
    elif age == 33:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 70, 91, skillChange)
    elif age == 34:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 70, 90, skillChange)
    elif age == 35:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 70, 89, skillChange)
    elif age == 36:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 69, 88, skillChange)
    elif age == 37:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 69, 88, skillChange)
    elif age == 38:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 68, 88, skillChange)
    elif age == 39:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 67, 87, skillChange)
    elif age == 40:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 66, 87, skillChange)
    elif age == 41:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 65, 87, skillChange)
    elif age == 42:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 64, 86, skillChange)
    elif age == 43:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 63, 86, skillChange)
    elif age == 44:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 62, 86, skillChange)
    elif age == 45:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 61, 86, skillChange)
    elif age == 46:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 60, 86, skillChange)
    elif age == 47:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 59, 86, skillChange)
    elif age == 48:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 58, 86, skillChange)
    elif age == 49:
        skillChange += random.randint(0,1) * -1
        skillChange = clampSkill(perf, 57, 86, skillChange)
    else:
        skillChange = 0

    return skillChange