import os
import time, re
from posix import wait

import Team
import Driver
import Race
import Rules
from Race import simulateQual, displayQualResults, simulateRace, simulateRace2, format_driver, format_team, displayRaceResults, updateConstructorChampionship, \
    updateDriverChampionship, updateDriverChampionship2, displayDriverChampionship, displayDriverChampionship2, displayConstructorChampionship, displayDriverMarket, \
    displayTeamMarket, displayDriverMarket2, driverChampionToList, displayDriverChampions
from Rules import seasonLength, regChangeYear, regIntervals, updatePointsDist, regChange, regSqueeze, DSUS
import random
from YearsData import getYearData
from ContractOffer import classify_team, build_candidate_pool, choose_best_candidate

import matplotlib.pyplot as plt
import numpy as np

def clear_system():
    os.system('cls' if os.name == 'nt' else 'clear')

def format_driver(name):
    parts = name.split()
    if len(parts) >= 2:
        first = parts[0][0].upper()
        last = parts[-1][:3].upper()
        return f"{first}.{last}"
    return name.upper()

def format_money(mon):
    value = mon * 1_000_000
    return f"{value:,.2f}"

def isRetiring(d, isRumour=False):

    # --- team position ---
    tempTeamPos = 1
    for t in teams:
        if d.getTeamAt() == t:
            break
        tempTeamPos += 1

    # --- base checks ---
    age = d.getDriverAge()
    championships = d.getDriverCha()
    driver_points = d.getDriverPoints()

    team = d.getTeamAt()
    team_points = team.getPoints() if (team and hasattr(team, "getPoints")) else 0

    # --- not old enough → no retirement ---
    if age < retMinAge + (championships / 1.5):
        return 0.0 if isRumour else False

    # --- calculate retire chance ---
    base = 10.0 + (age - retMinAge) * 5

    if team_points > 0:
        performance_factor = driver_points / team_points
        team_factor = (0.5 - performance_factor) * (100 + (tempTeamPos - 0.5) * 5)
        retireChance = base + team_factor
    else:
        retireChance = base + 35.0

    # --- hard cap age ---
    if age >= 49:
        return 100.0 if isRumour else True

    # --- return behaviour ---
    if isRumour:
        return retireChance

    return random.random() * 100 <= retireChance

print("Welcome to Project Manager!")
print()
while True:
    try:
        print("Choose an option below by typing in the option number:\n")
        menuSelect = 0
        print("-" * 25)
        print("| (1) Start new career. |")
        print("| (2) Exit program.     |")
        print("-" * 25)
        menuSelect = int(input("Input: "))

        if menuSelect == 1 or menuSelect == 2 or menuSelect == 3:
            break
        else:
            print("\nInvalid selection.\n")
    except ValueError:
        print("\nInvalid input.\n")

teams = []
free_agents = []
driverChampionship = []
driverChampionship2 = []
queuedDrivers = []
poolOfDrivers = []
retiredDrivers = []
championshipDriverWinners = []
customRet = False

ADVANCE_COLOUR = "\033[38;2;100;180;100m"
WEEK_COLOUR1 = "\033[38;2;140;140;140m"
WEEK_COLOUR2 = "\033[38;2;115;115;115m"
RED_COLOUR = "\033[38;2;255;61;61m"
SUPERRED_COLOUR = "\033[38;2;120;20;10m"

FAColour = "\033[1;38;2;200;200;255;49m"
F2Colour = "\033[1;38;2;255;255;255;49m"

McLarenColour = "\033[1;38;2;239;155;51;49m"
FerrariColour = "\033[1;38;2;213;47;56;49m"
RedBullColour = "\033[1;38;2;20;89;132;49m"
MercedesColour = "\033[1;38;2;117;241;211;49m"
AstonMartinColour = "\033[1;38;2;75;151;116;49m"
AlpineColour = "\033[1;38;2;71;159;226;49m"
HaasColour = "\033[1;38;2;223;225;226;49m"
RacingBullsColour = "\033[1;38;2;112;145;248;49m"
WilliamsColour = "\033[1;38;2;50;103;212;49m"
SauberColour = "\033[1;38;2;105;228;68;49m"
AudiColour = "\033[1;38;2;235;69;38;49m"
RESET = "\033[0m"

def get_int(prompt, min_val=None, max_val=None):
    while True:
        try:
            x = int(input(prompt))
            if (min_val is not None and x < min_val) or (max_val is not None and x > max_val):
                raise ValueError
            return x
        except ValueError:
            print("Invalid input.\n")


def load_season(seasonPick):
    getYearData(seasonPick, teams, driverChampionship, free_agents,
                driverChampionship2, queuedDrivers, poolOfDrivers)


def choose_existing_team(player_num):
    while True:
        print(f"\nPlayer {player_num} - Choose a team:\n")
        for i, team in enumerate(teams, start=1):
            occupied = not team.isControlledByAI()
            status = "(Occupied)" if occupied else ""
            print(f"({i}) {team.getColour()}{team.getName():<25}{RESET} {status}")

        choice = get_int("Select team: ", 1, len(teams))

        if teams[choice - 1].isControlledByAI():
            teams[choice - 1].toggleControlledByAI()
            return
        else:
            print("That team is already taken.\n")


def pick_driver():
    while True:
        name = input("Driver name: ")
        for pool in (free_agents, driverChampionship2):
            for d in pool:
                if d.getDriverName() == name:
                    pool.remove(d)
                    driverChampionship.append(d)
                    d.setContractLeft(1)
                    return d
        print("Driver not found.\n")


def refill_f2_grid():
    while len(driverChampionship2) < 22:
        idx = int(random.random() * 5)
        driver = queuedDrivers.pop(idx)
        driver.setTeamAt("Formula 2")
        driverChampionship2.append(driver)
        queuedDrivers.append(poolOfDrivers.pop(0))


def choose_colour():
    colours = {
        "Light Red": "\033[1;38;2;255;102;102;49m",
        "Light Orange": "\033[1;38;2;255;178;102;49m",
        "Vibrant Orange": "\033[1;38;2;255;128;0;49m",
        "Vibrant Blue": "\033[1;38;2;75;75;255;49m",
        "Dark Orange": "\033[1;38;2;204;102;0;49m",
        "Dark Grey": "\033[1;38;2;96;96;96;49m",
        "Yellow": "\033[1;38;2;193;170;30;49m",
        "Cyan": "\033[1;38;2;0;255;255;49m",
        "Purple": "\033[1;38;2;127;0;255;49m",
        "Pink": "\033[1;38;2;219;81;223;49m"
    }

    print("\nAvailable colours:")
    for c in colours:
        print(c)

    while True:
        choice = input("Pick colour: ")
        if choice in colours:
            return colours[choice]
        print("Invalid colour.\n")


def create_custom_team(player_num):
    print(f"\nPlayer {player_num} - Create your team\n")

    name = input("Team Name: ")
    short = name

    print("\nPick Driver 1:")
    displayDriverMarket2(free_agents, driverChampionship2)
    d1 = pick_driver()

    print("\nPick Driver 2:")
    displayDriverMarket2(free_agents, driverChampionship2)
    d2 = pick_driver()

    refill_f2_grid()

    colour = choose_colour()

    # performance balancing
    perf_list = sorted([t.getPerf() for t in teams], reverse=True)
    start_perf = (perf_list[0] + 5 * perf_list[-1]) / 6

    new_team = Team.team(name, short, colour, 6.0, 0, start_perf, 6, None, 0)
    new_team.toggleControlledByAI()

    new_team.setDriver1(d1)
    new_team.setDriver2(d2)

    d1.setTeamAt(new_team)
    d2.setTeamAt(new_team)

    teams.append(new_team)


# ================= MAIN FLOW =================

if menuSelect in (1, 2):
    plaCount = 1
    seasonPick = 2026
    rndVisualOn = 2

    while True:
        print("\n(1) Player count:", plaCount)
        print("(2) Season:", seasonPick)
        print("(3) RnD Chart:", rndVisualOn)
        print("(4) Continue")

        choice = get_int("Input: ", 1, 4)

        if choice == 1:
            plaCount = get_int("Players (1-10): ", 1, 10)

        elif choice == 2:
            print("(2025 or 2026)")
            seasonPick = get_int("Season: ", 2025, 2026)

        elif choice == 3:
            print("('1' for On, '2' for off)")
            rndVisualOn = get_int("Input: ", 1, 2)

        elif choice == 4:
            clear_system()
            break

    load_season(seasonPick)

    # 🔥 NEW FLEXIBLE SYSTEM
    for p in range(1, plaCount + 1):
        print(f"\nPlayer {p}:")
        print("(1) Choose existing team")
        print("(2) Create custom team")

        mode = get_int("Select: ", 1, 2)

        if mode == 1:
            choose_existing_team(p)
        else:
            create_custom_team(p)

    # points distribution
    pointsDist = updatePointsDist(len(teams) * 2)

    #CAREER
    championshipDriverWinners.append(f"{"Sebastian VETTEL":<20}{"22":<7}{RedBullColour}{"Red Bull":<16}{RESET}{"256":<7}{"🏆x1":<12}{RedBullColour}{"Red Bull":<12}{RESET}")
    championshipDriverWinners.append(f"{"Sebastian VETTEL":<20}{"23":<7}{RedBullColour}{"Red Bull":<16}{RESET}{"392":<7}{"🏆x2":<12}{RedBullColour}{"Red Bull":<12}{RESET}")
    championshipDriverWinners.append(f"{"Sebastian VETTEL":<20}{"24":<7}{RedBullColour}{"Red Bull":<16}{RESET}{"281":<7}{"🏆x3":<12}{RedBullColour}{"Red Bull":<12}{RESET}")
    championshipDriverWinners.append(f"{"Sebastian VETTEL":<20}{"25":<7}{RedBullColour}{"Red Bull":<16}{RESET}{"397":<7}{"🏆x4":<12}{RedBullColour}{"Red Bull":<12}{RESET}")
    championshipDriverWinners.append(f"{"Lewis HAMILTON":<20}{"29":<7}{MercedesColour}{"Mercedes":<16}{RESET}{"384":<7}{"🏆x2":<12}{MercedesColour}{"Mercedes":<12}{RESET}")
    championshipDriverWinners.append(f"{"Lewis HAMILTON":<20}{"30":<7}{MercedesColour}{"Mercedes":<16}{RESET}{"381":<7}{"🏆x3":<12}{MercedesColour}{"Mercedes":<12}{RESET}")
    championshipDriverWinners.append(f"{"Nico ROSBERG":<20}{"30":<7}{MercedesColour}{"Mercedes":<16}{RESET}{"385":<7}{"🏆x1":<12}{MercedesColour}{"Mercedes":<12}{RESET}")
    championshipDriverWinners.append(f"{"Lewis HAMILTON":<20}{"32":<7}{MercedesColour}{"Mercedes":<16}{RESET}{"363":<7}{"🏆x4":<12}{MercedesColour}{"Mercedes":<12}{RESET}")
    championshipDriverWinners.append(f"{"Lewis HAMILTON":<20}{"33":<7}{MercedesColour}{"Mercedes":<16}{RESET}{"408":<7}{"🏆x5":<12}{MercedesColour}{"Mercedes":<12}{RESET}")
    championshipDriverWinners.append(f"{"Lewis HAMILTON":<20}{"34":<7}{MercedesColour}{"Mercedes":<16}{RESET}{"413":<7}{"🏆x6":<12}{MercedesColour}{"Mercedes":<12}{RESET}")
    championshipDriverWinners.append(f"{"Lewis HAMILTON":<20}{"35":<7}{MercedesColour}{"Mercedes":<16}{RESET}{"347":<7}{"🏆x7":<12}{MercedesColour}{"Mercedes":<12}{RESET}")
    championshipDriverWinners.append(f"{"Max VERSTAPPEN":<20}{"23":<7}{RedBullColour}{"Red Bull":<16}{RESET}{"395.5":<7}{"🏆x1":<12}{MercedesColour}{"Mercedes":<12}{RESET}")
    championshipDriverWinners.append(f"{"Max VERSTAPPEN":<20}{"24":<7}{RedBullColour}{"Red Bull":<16}{RESET}{"454":<7}{"🏆x2":<12}{RedBullColour}{"Red Bull":<12}{RESET}")
    championshipDriverWinners.append(f"{"Max VERSTAPPEN":<20}{"25":<7}{RedBullColour}{"Red Bull":<16}{RESET}{"575":<7}{"🏆x3":<12}{RedBullColour}{"Red Bull":<12}{RESET}")
    if seasonPick >= 2025:
        championshipDriverWinners.append(f"{"Max VERSTAPPEN":<20}{"26":<7}{RedBullColour}{"Red Bull":<16}{RESET}{"437":<7}{"🏆x4":<12}{McLarenColour}{"McLaren":<12}{RESET}")
    if seasonPick >= 2026:
        championshipDriverWinners.append(f"{"Lando NORRIS":<20}{"25":<7}{McLarenColour}{"McLaren":<16}{RESET}{"423":<7}{"🏆x1":<12}{McLarenColour}{"McLaren":<12}{RESET}")

    retMinAge = 42
    drivertransferList = []
    driverWinHistory = []
    customRetList = []
    customRetList2 = []

    for season in range (30):
        clear_system()

        #if customTeams == True: pointsDist = updatePointsDist((plaCount + AICount) * 2)
        gridSize = teams.__len__() * 2
        pointsDist = updatePointsDist(gridSize)
        if season == 1: retMinAge == 40
        elif season == 2: retMinAge == 38
        elif season == 4: retMinAge == 37
        elif season == 7: retMinAge == 36
        elif season == 14: retMinAge == 35

        if ((seasonPick + season) == regChangeYear):
            regChangeYear += regIntervals

        driverWinHistory.append([])

        print("\nNew Season!\n")
        print("A new season of Formula One Racing has arrived. Last season was spectacular,")
        print(f"but with all the teams and drivers on edge,")
        if ((seasonPick + season) + 1 == regChangeYear): #If next year is the first year in the new reg era,
            print(f"and the arrival of the new era next season in F1 {seasonPick + season + 1},")
        elif ((seasonPick + season) + regIntervals == regChangeYear): #If this year is the first year in the new reg era,
            print(f"and the arrival of the new cars that will span from {seasonPick + season} to {regChangeYear-1},")
        print(f"the {seasonPick + season} season is expected to raise the bar even higher!"
              f"\nWhich teams have nailed their setups for this season, and which have it all crossed up?\n")
        print(f"Before F1 {seasonPick + season} kicks off, let's review the driver line-ups for this season...")
        input("\nPress 'SPACE' to continue...")

        if season > 0:
            print(f"{"\nDRIVER TRANSFERS REVEAL":<28}")
            print("-" * 66)
            time.sleep(2)
            if len(drivertransferList) > 0:
                for line in drivertransferList:
                    print(line)
                    if len(drivertransferList) > 10:
                        time.sleep(2.5)
                    else:
                        time.sleep(3.5)
            else:
                print("No driver transfers!")
            input("\nPress 'SPACE' to continue...")
        drivertransferList.clear()
        customRetList.clear()
        customRetList2.clear()

        print("=" * 115)
        for team in teams:
            driver1 = team.getDriver1()
            driver2 = team.getDriver2()

            if driver1.getDriverCha() > 0:
                driver1_str = f"{Race.format_driver_basic(driver1.getDriverName(),team.getColour())} ({driver1.getDriverAge()}) 🏆x{driver1.getDriverCha():}"
            else:
                driver1_str = f"{Race.format_driver_basic(driver1.getDriverName(),team.getColour())} ({driver1.getDriverAge()})"
            if driver2.getDriverCha() > 0:
                driver2_str = f"{Race.format_driver_basic(driver2.getDriverName(),team.getColour())} ({driver2.getDriverAge()}) 🏆x{driver2.getDriverCha():}"
            else:
                driver2_str = f"{Race.format_driver_basic(driver2.getDriverName(),team.getColour())} ({driver2.getDriverAge()})"

            if team.getSupplier() != None:
                nameGapLeft = 31 - len(team.getName()) - len(team.getSupplier().getName())
                print(f"{team.getColour()}{team.getName()}{team.getColReset()} - {team.getSupplier().getColour()}{team.getSupplier().getName()}{team.getSupplier().getColReset()}{" ":<{nameGapLeft}}||{" ":<5}{driver1_str:<35}, {driver2_str:<35}")
            else:
                print(f"{team.getColour()}{team.getName():34s}{team.getColReset()}||{" ":<5}{driver1_str:<35}, {driver2_str:<35}")
        print("=" * 115)
        input("\nPress 'SPACE' to continue...")

        for team in teams: #Cash injections from drivers
            team.addMoney(team.getDriver1().getDriverCha()/1.5 + team.getDriver2().getDriverCha()/1.5)

        for round in range (seasonLength):
            chaPos = 0
            driverWinHistory[season].append([[" ",RESET],[" ",RESET],[" ",RESET]])
            fixed_race_winner = None
            for team in teams:
                clear_system()
                chaPos += 1

                customRet = False
                if team.isControlledByAI(): #AI
                    '''
                    Compare how much team needs to save to pay driver salaries.
                    Use the remainder funds to do upgrades or research.

                    ******
                    Should be:
                        INVEST 10:3.5 or 8:3
                    '''
                    # TODO: REMAKE AI BEHAVIOUR
                    tempFunds = team.getMoney() - (team.getDriver1().getDriverSalary()/seasonLength + team.getDriver2().getDriverSalary()/seasonLength)
                    if tempFunds >= 10:
                        roundFunds = (tempFunds - 1) * (random.random() * 0.35 + 0.2)
                    else:
                        roundFunds = (tempFunds - 1) * (random.random() * 0.35)
                    '''print("Team: ", team.getName())
                    print("Temp Funds: ", tempFunds)
                    print("Round Funds: ", roundFunds)
                    input("\nPress 'SPACE' to continue...")'''

                    if roundFunds > 0.5:
                        '''print("IF #1 - team does research")'''
                        tempInv = roundFunds * random.random() * 0.50
                        team.addPerfRes(tempInv)
                        roundFunds -= tempInv
                        team.addMoney(-tempInv)

                        team.addReliRes(roundFunds)
                        team.addMoney(-roundFunds)
                        '''input("\n**Press 'SPACE' to continue...")'''

                        if (team.getPerfRes() + team.getReliRes()) > (random.random() + 2.0) and random.random() > 0.5:
                            '''print("IF #2 - team develops parts (upgrading perf rating)")'''
                            # Apply research effects
                            team.addPerf(team.getPerfRes())
                            team.addPerfRes(-team.getPerfRes())

                            team.addRel(team.getReliRes())
                            team.addReliRes(-team.getReliRes())
                            team.addMoney(-1)
                            '''input("\n***Press 'SPACE' to continue...")'''

                else: #Player
                    print(f"\nROUND {round+1} - {team.getName()}")
                    input("\nPress 'SPACE' to continue...")
                    while True:
                        try:
                            clear_system()
                            if not customRet:
                                customRetList.clear()

                            print()
                            print(f"{team.getColour()}={WEEK_COLOUR2}" * 100)
                            print(f"⏳ {"YEAR:":10s}{seasonPick + season}")
                            print(f"🏁 {"ROUND:":10s}{round+1} of {seasonLength}")
                            print(f"🚩 {"TEAM:":10s}{team.getColour()}{team.getName()}{WEEK_COLOUR2}")
                            print(f"📈 {"FUNDS:":10s}{format_money(team.getMoney())}")
                            print(f"🏎️ {"DRIVER 1:":10s}{team.getColour()}{team.getDriver1()} | 🏆x{team.getDriver1().getDriverCha()} | Aged {team.getDriver1().getDriverAge()} | {team.getDriver1().getDriverPoints()} point(s) | {team.getDriver1().getSeasonRWins()} seasonal race win(s) |{WEEK_COLOUR2}")
                            print(f"🏎️ {"DRIVER 2:":10s}{team.getColour()}{team.getDriver2()} | 🏆x{team.getDriver2().getDriverCha()} | Aged {team.getDriver2().getDriverAge()} | {team.getDriver2().getDriverPoints()} point(s) | {team.getDriver2().getSeasonRWins()} seasonal race win(s) |")
                            roundmenuSelect = 0
                            print(f"{RESET}")
                            print("=" * 32)
                            print(f"{ADVANCE_COLOUR}| (a) ADVANCE to Race Weekend |{RESET}")
                            print("=" * 32)
                            print("-" * 45)
                            print("CHAMPIONSHIP STANDINGS")
                            print(f"{team.getColour()}(dc){WEEK_COLOUR1} DRIVERS' Championship (F1 {seasonPick + season})")
                            print(f"{team.getColour()}(cc){WEEK_COLOUR1} CONSTRUCTORS' Championship (F1 {seasonPick + season})")
                            print(f"{team.getColour()}(dc2){WEEK_COLOUR1} DRIVERS' Championship (F2 {seasonPick + season})")
                            print(f"{RESET}", end="")
                            print("-" * 65)
                            print(f"{team.getName().upper()} RŃD SECTOR")
                            print(f"{team.getColour()}", end="")
                            RPR = classify_team(team, teams)
                            if RPR == "front":
                                RPR = "HIGH"
                            elif RPR == "mid":
                                RPR = "MID"
                            else:
                                RPR = "LOW"
                            print(f"{RESET}Relative Perf: {team.getColour()}{RPR}{RESET}\tCar Reliability: {team.getColour()}{team.getRelDisplay()}{RESET}")
                            print(f"{team.getColour()}(res){WEEK_COLOUR1} RESEARCH PARTS     {team.getColour()}(tun){WEEK_COLOUR1} TUNING")
                            print(f"{team.getColour()}(dev){WEEK_COLOUR1} DEVELOP PARTS      {team.getColour()}(rr){WEEK_COLOUR1} ❌{regChangeYear} REG RESEARCH")
                            print(f"{RESET}", end="")
                            print("-" * 85)
                            print(f"{team.getName().upper()} CONTRACT MANAGEMENT")
                            print(f"{team.getColour()}(fin){WEEK_COLOUR1} FINANCES     {team.getColour()}(dm){WEEK_COLOUR1} DRIVER MARKET     {team.getColour()}(dl){WEEK_COLOUR1} DRIVER LINEUP")
                            print(f"{RESET}", end="")
                            print("-" * 85)
                            print("AFFILIATIONS & LOWER CATEGORIES")
                            print(f"{WEEK_COLOUR1}", end="")
                            print(f"{team.getColour()}(daff){WEEK_COLOUR1} ❌DRIVER AFFILIATES     {team.getColour()}(taff){WEEK_COLOUR1} ❌TEAM AFFILIATES")
                            print(f"{RESET}", end="")
                            print("-" * 85)
                            print("RUMOURS & HISTORY")
                            print(f"{WEEK_COLOUR1}", end="")
                            print(f"{team.getColour()}(rum){WEEK_COLOUR1} Retirement RUMOURS     {team.getColour()}(rh){WEEK_COLOUR1} RACE History     {team.getColour()}(ch){WEEK_COLOUR1} CHAMPION History")
                            print(f"{RESET}", end="")
                            print("-" * 85)
                            print("OTHER")
                            if rndVisualOn == 1:
                                print(f"{team.getColour()}(pbar){WEEK_COLOUR2} RńD Performance Bar Chart")
                            print(f"{team.getColour()}(ret){WEEK_COLOUR2} Retire...")
                            print(f"{RESET}", end="")

                            print(f"\n{RESET}(❌ - not coded)")
                            print(f"{team.getColour()}={RESET}" * 100)
                            roundmenuSelect = input("Input: ")
                        except ValueError:
                            print("\nInvalid input.\n")
                        else:
                            try:
                                m = re.match(r"t(\d+)([+p])(\d+)", roundmenuSelect)
                                clear_system()
                                if roundmenuSelect == "a":
                                    break
                                elif roundmenuSelect == "fin":
                                    print()
                                    print("=" * 50)
                                    print(f"{"Pre-season cash injection:":40s}+${(team.getDriver1().getDriverCha()/1.5 + team.getDriver2().getDriverCha()/1.5):.2f}M")
                                    EPSCI = (9.0 - (0.50 * chaPos))
                                    if chaPos == 1: EPSCI += 1.50
                                    print(f"{"Estimated post-season cash injection:":40s}+${EPSCI:.2f}M")
                                    print("=" * 50)
                                    EPRG = (1.75-(0.025*(chaPos*2)))+(1.75-(0.025*((chaPos*2)-1)))
                                    print(f"{"Estimated per race gains:":40s}+${EPRG:.2f}M") #(1.75 - (0.025 * pos))
                                    print("-" * 38)
                                    print(f"{"Per race cost for "+team.getDriver1().getDriverName()+":":40s}-${team.getDriver1().getDriverSalary() / seasonLength:.2f}M")
                                    print(f"{"Per race cost for "+team.getDriver2().getDriverName()+":":40s}-${team.getDriver2().getDriverSalary() / seasonLength:.2f}M")
                                    PRTC = (team.getDriver1().getDriverSalary() + team.getDriver2().getDriverSalary()) / seasonLength
                                    print(f"{"Per race total cost:":40s}-${PRTC:.2f}M")
                                    print("-" * 38)
                                    if (EPRG-PRTC) >= 0: print(f"{"Estimated per race net profit:":40s}+${(EPRG-PRTC):.2f}M")
                                    elif (EPRG-PRTC) < 0: print(f"{"Estimated per race net profit:":40s}-${(PRTC-EPRG):.2f}M")
                                    print("=" * 50)
                                    input("\nPress 'SPACE' to continue...")
                                elif roundmenuSelect == "dev":
                                    # TODO: UPDATE DEVELOPMENT SECTOR TO IMPROVED GAME STRUCTURE
                                    if team.getMoney() >= 0.0:
                                        while True:
                                            try:
                                                print(f"\nFUNDS: {format_money(team.getMoney())}\n")
                                                print(f"INVESTMENT AMOUNT: {format_money(team.getPerfRes() + team.getReliRes())}\n")
                                                print(f"*PROJECTED RELI: {team.getColour()}{team.getRelDisplay()}{RESET} ---> {team.getColour()}{(team.getRel()*100)+(team.getReliRes()/1):.2f}%{RESET}")
                                                roundsubmenuSelect = 0
                                                print(f"(1) Back")
                                                print(f"(2) ❌Development Quality = NORMAL")
                                                print(f"(3) Confirm Development Plan (Costs $1M)")
                                                roundsubmenuSelect = int(input("Input: "))
                                            except ValueError:
                                                print("\nInvalid input.\n")
                                            else:
                                                if roundsubmenuSelect == 1: break
                                                elif roundsubmenuSelect == 2:
                                                    continue
                                                elif roundsubmenuSelect == 3:
                                                    print(f"Invested ${1:.2f}M for development of newly researched parts!")

                                                    team.addPerf(team.getPerfRes())
                                                    team.addPerfRes(-team.getPerfRes())

                                                    team.addRel(team.getReliRes())
                                                    team.addReliRes(-team.getReliRes())

                                                    team.addMoney(-1)
                                                    break
                                                else:
                                                    print("\nInvalid selection.\n")
                                    else:
                                        print("\nInvalid input - insufficient funds.\n")
                                    input("\nPress 'SPACE' to continue...")
                                elif roundmenuSelect == "tun":
                                    while True:
                                        try:
                                            roundsubmenuSelect = team.getTuning()
                                            print(f"Current Tuning: [{team.getTuning()}]")
                                            print(f"Enter a value between -3 and 3 to set tuning.")
                                            choice = get_int("Input: ", -3, 3)
                                        except:
                                            print("\nERROR PRODUCED.\n")
                                        else:
                                            team.setTuning(choice)
                                            print("\nTuning applied.\n")
                                            break
                                    input("\nPress 'SPACE' to continue...")
                                elif roundmenuSelect == "res":
                                    if 0.0 <= team.getMoney() < 1.0:
                                        investAMT = team.getMoney()
                                    elif team.getMoney() >= 1.0:
                                        investAMT = 1.0
                                    else:
                                        investAMT = 0.0
                                    investG = "Performance"

                                    if team.getMoney() > 0.0:
                                        while True:
                                            clear_system()
                                            try:
                                                print(f"\nFUNDS: {format_money(team.getMoney())}\n")
                                                print(f"(1) Back")
                                                print(f"(2) Research Amount = {team.getColour()}${investAMT:.2f}M{RESET} set")
                                                print(f"(3) Research Priority = {team.getColour()}{investG}{RESET}")
                                                print(f"(4) Confirm Research Plan")
                                                choice = get_int("Input: ", 1, 4)
                                            except ValueError:
                                                print("\nInvalid input.\n")
                                            else:
                                                if choice == 1: break
                                                elif choice == 2:
                                                    try:
                                                        checkInvestAMT = float(input("Type in research amount ($M) or '-1' for back: "))
                                                    except ValueError:
                                                        print("\nInvalid input.\n")
                                                    else:
                                                        if checkInvestAMT > 0.0 and checkInvestAMT <= team.getMoney():
                                                            investAMT = checkInvestAMT
                                                        elif checkInvestAMT == -1:
                                                            break
                                                        else:
                                                            if checkInvestAMT > team.getMoney():
                                                                investAMT = team.getMoney()
                                                            else:
                                                                print("\nInvalid input.\n")
                                                elif choice == 3:
                                                    prompt = (f"\nChoose the priority of your research."
                                                              f"\n(1)  '{team.getColour()}Performance{RESET}' = Focus will be on making the cars FASTER,"
                                                              f"\n\tleaving room for reliability levels to dip."
                                                              f"\n\tPERF 🔼🔼🔼  RELI 🔻"
                                                              f"\n(2)  '{team.getColour()}Reliability{RESET}' = Focus will be on making the cars STURDIER,"
                                                              f"\n\tallowing them to be trustworthy on track (reducing DNF chance)."
                                                              f"\n\tPERF 🔻  RELI 🔼🔼🔼🔼🔼"
                                                              f"\n\nInput ('1' or '2'): ")
                                                    choice = get_int(prompt, 1, 2)
                                                    if choice in [1,2]:
                                                        print(f"Priority successfully chosen.")
                                                        if choice == 1: investG = "Performance"
                                                        else: investG = "Reliability"
                                                    else:
                                                        print("\nInvalid input.\n")
                                                    input("\nPress 'SPACE' to continue...")
                                                    continue
                                                elif choice == 4:
                                                    print(f"Invested ${investAMT:.2f}M")
                                                    if investG == "Performance":
                                                        team.addPerfRes(investAMT)
                                                        team.addReliRes(-(investAMT/3))
                                                    elif investG == "Reliability":
                                                        team.addPerfRes(-(investAMT/5))
                                                        team.addReliRes(investAMT)
                                                    team.addMoney(-investAMT)
                                                    break
                                                else:
                                                    print("\nInvalid selection.\n")
                                    else: print("\nInvalid input - insufficient funds.\n")
                                    input("\nPress 'SPACE' to continue...")
                                elif roundmenuSelect == "dc":
                                    print()
                                    displayDriverChampionship(driverChampionship)
                                    input("\nPress 'SPACE' to continue...")
                                elif roundmenuSelect == "cc":
                                    print()
                                    displayConstructorChampionship(teams)
                                    input("\nPress 'SPACE' to continue...")
                                elif roundmenuSelect == "con" and season == 100:
                                    while True:
                                        try:
                                            print(f"\n{team.getDriver1()}'s contract: {team.getDriver1().getContractLeft()} season(s) left")
                                            print(f"{team.getDriver2()}'s contract: {team.getDriver2().getContractLeft()} season(s) left\n")
                                            print("\nChoose an option below by typing in the option number:")
                                            roundsubmenuSelect = 0
                                            print(f"(1) Back")
                                            print(f"(2) Offer contract extension to {team.getDriver1()}")
                                            print(f"(3) Offer contract extension to {team.getDriver2()}")
                                            roundsubmenuSelect = int(input("Input: "))
                                        except ValueError:
                                            print("\nInvalid input.\n")
                                        else:
                                            if roundsubmenuSelect == 1: break
                                            elif roundsubmenuSelect == 2 and team.getDriver1().getContractLeft() < 2:
                                                team.getDriver1().addContractExtension(1)
                                            elif roundsubmenuSelect == 3 and team.getDriver2().getContractLeft() < 2:
                                                team.getDriver2().addContractExtension(1)
                                            else:
                                                print("\nInvalid selection.\n")
                                    input("\nPress 'SPACE' to continue...")
                                elif roundmenuSelect == "dm":
                                    try:
                                        print()
                                        displayDriverMarket(driverChampionship, free_agents, driverChampionship2, True)
                                        retName = input("\nPress 'SPACE' to continue...")

                                        if customRet:
                                            try:
                                                retName = retName.split(",")
                                                for i in retName:
                                                    p = int(i)

                                                    lowerBound = 1
                                                    upperBound = len(driverChampionship)
                                                    if lowerBound <= p <= upperBound:  # 1 <= p <= 22
                                                        customRetList.append(driverChampionship[p-1])
                                                    else:
                                                        lowerBound = upperBound
                                                        upperBound = lowerBound + len(free_agents)
                                                        if lowerBound < p <= upperBound:  # 22 < p <= 55
                                                            customRetList.append(free_agents[p-1-lowerBound])
                                                        else:
                                                            lowerBound = upperBound
                                                            upperBound = lowerBound + len(driverChampionship2)
                                                            if lowerBound < p <= upperBound:  # 55 < p <= 77
                                                                customRetList.append(driverChampionship2[p-1-lowerBound])
                                            except Exception:
                                                print("\nInvalid input - RET Error.\n")
                                    except:
                                        print("\nERROR PRODUCED - 'dm' command has produced an error.\n")
                                elif roundmenuSelect == "dmR":
                                    try:
                                        print()
                                        displayDriverMarket(driverChampionship, free_agents, driverChampionship2, False)
                                        retName = input("\nPress 'SPACE' to continue...")

                                        try:
                                            for d in driverChampionship[:]:
                                                if retName.lower() == d.getDriverName().lower():
                                                    repVal = float(input("\nRepVal:"))
                                                    d.addDriverRep(repVal)
                                            for d in free_agents[:]:
                                                if retName.lower() == d.getDriverName().lower():
                                                    repVal = float(input("\nRepVal:"))
                                                    d.addDriverRep(repVal)
                                            for d in driverChampionship2[:]:
                                                if retName.lower() == d.getDriverName().lower():
                                                    repVal = float(input("\nRepVal:"))
                                                    d.addDriverRep(repVal)
                                            if 1 <= int(retName) <= gridSize:
                                                retName = int(retName)
                                                repVal = float(input("\nRepVal:"))
                                                retIndex = 0
                                                for d in driverChampionship[:]:
                                                    d.addDriverRep(repVal)
                                                    retIndex += 1
                                                    if retIndex == retName:
                                                        break
                                        except Exception:
                                            print("\nInvalid input - REP Error.\n")
                                    except:
                                        print("\nERROR PRODUCED - 'dmR' command has produced an error.\n")
                                elif roundmenuSelect == "dl":
                                    try:
                                        print()
                                    except:
                                        print("\nERROR PRODUCED - 'dl' command has produced an error.\n")
                                elif roundmenuSelect == "dc2":
                                    print()
                                    displayDriverChampionship2(driverChampionship2)
                                    input("\nPress 'SPACE' to continue...")
                                elif roundmenuSelect == "aff" and season == 100:
                                    print()
                                    input("\nPress 'SPACE' to continue...")
                                elif roundmenuSelect == "tms" and season == 100:
                                    print()
                                    print("=" * 55)
                                    print(f"\n{"Team":<24s} | {"Power Units":<14s} | {"Aff. Level"}")
                                    print("-" * 55)
                                    for t in teams:
                                        if t.getSupplier() != None:
                                            if t.getSupStage() == 1:
                                                print(f"{t.getName():<24} | {t.getSupplier().getName():<14} | {"Partnership"}")
                                            elif t.getSupStage() == 2:
                                                print(f"{t.getName():<24} | {t.getSupplier().getName():<14} | {"Junior Team"}")
                                        else:
                                            print(f"{t.getName():<24} | {t.getName():<14} |")
                                    print("=" * 55)
                                    input("\nPress 'SPACE' to continue...")
                                elif roundmenuSelect == "rum":
                                    DARK_YELLOW = "\033[38;2;180;140;0m"
                                    DARK_ORANGE = "\033[38;2;200;90;0m"
                                    DARK_RED = "\033[38;2;160;0;0m"
                                    RESET = "\033[0m"

                                    print("\nRumour has it that the following drivers are considering retirement:\n")

                                    range_1_pred = []  # light
                                    range_2_pred = []  # moderate
                                    range_3_pred = []  # heavy

                                    for d in driverChampionship[:]:
                                        val = isRetiring(d, True)

                                        if 1 <= val < 20:
                                            range_1_pred.append(d)
                                        elif 20 <= val < 50:
                                            range_2_pred.append(d)
                                        elif val >= 50:
                                            range_3_pred.append(d)


                                    # convert to display strings (name + age)
                                    def format_entry(d):
                                        return f"{d.getDriverName()} ({d.getDriverAge()})"


                                    light_list = [format_entry(d) for d in range_1_pred]
                                    moderate_list = [format_entry(d) for d in range_2_pred]
                                    heavy_list = [format_entry(d) for d in range_3_pred]

                                    max_len = max([len(light_list), len(moderate_list), len(heavy_list)], default=0)

                                    # build rows (side-by-side columns)
                                    rows = []
                                    for i in range(max_len):
                                        rows.append([
                                            light_list[i] if i < len(light_list) else "",
                                            moderate_list[i] if i < len(moderate_list) else "",
                                            heavy_list[i] if i < len(heavy_list) else ""
                                        ])

                                    # coloured headers ONLY
                                    headers = [
                                        f"{DARK_YELLOW}LIGHT{RESET}",
                                        f"{DARK_ORANGE}MODERATE{RESET}",
                                        f"{DARK_RED}HEAVY{RESET}"
                                    ]

                                    widths = [30, 30, 30]
                                    aligns = ["left", "left", "left"]

                                    print()
                                    if max_len == 0:
                                        print("NONE.")
                                    else:
                                        Race.print_table(headers, rows, widths, aligns)
                                    print()

                                    input("Press 'SPACE' to continue...")
                                elif roundmenuSelect == "rh":
                                    print(f"{"Season":<7s} | {"R1":^{6}} | {"R2":^{6}} | {"R3":^{6}} | {"R4":^{6}} | {"R5":^{6}} | {"R6":^{6}} | {"R7":^{6}} | {"R8":^{6}} | {"R9":^{6}} | {"R10":^{6}} | {"R11":^{6}} | {"R12":^{6}} |")
                                    print("=" * 117)
                                    for i in range(season+1):
                                        if i == season:
                                            l1 = f"{ADVANCE_COLOUR}{seasonPick + i:<7}{RESET} |"
                                        else:
                                            l1 = f"{seasonPick + i:<7} |"
                                        l2 = f"{" ":<7} |"
                                        l3 = f"{" ":<7} |"

                                        if season > i:
                                            for r in range(seasonLength):
                                                l1 += f" {driverWinHistory[i][r][0][1]}{format_driver(driverWinHistory[i][r][0][0]):^{6}}{RESET} |"
                                                l2 += f" {driverWinHistory[i][r][1][1]}{format_driver(driverWinHistory[i][r][1][0]):^{6}}{RESET} |"
                                                l3 += f" {driverWinHistory[i][r][2][1]}{format_driver(driverWinHistory[i][r][2][0]):^{6}}{RESET} |"
                                        else:
                                            for r in range(round):
                                                l1 += f" {driverWinHistory[i][r][0][1]}{format_driver(driverWinHistory[i][r][0][0]):^{6}}{RESET} |"
                                                l2 += f" {driverWinHistory[i][r][1][1]}{format_driver(driverWinHistory[i][r][1][0]):^{6}}{RESET} |"
                                                l3 += f" {driverWinHistory[i][r][2][1]}{format_driver(driverWinHistory[i][r][2][0]):^{6}}{RESET} |"
                                        print(l1)
                                        print(l2)
                                        print(l3)
                                        if regChangeYear % 4 == (seasonPick + i + 1) % 4:
                                            print("=" * 117)
                                            print("=" * 117)
                                        else:
                                            print("-" * 117)
                                    input("\nPress 'SPACE' to continue...")
                                elif roundmenuSelect == "ch":
                                    print()
                                    print(displayDriverChampions(championshipDriverWinners))
                                    input("\nPress 'SPACE' to continue...")
                                elif roundmenuSelect == "ret":
                                    try:
                                        print("\nChoose an option below by typing in the option number:")
                                        roundsubmenuSelect = 0
                                        print(f"(1) Confirm your retirement from the series")
                                        print(f"(2) Back")
                                        roundsubmenuSelect = int(input("Input: "))
                                    except ValueError:
                                        print("\nInvalid input.\n")
                                    else:
                                        if roundsubmenuSelect == 1:
                                            team.toggleControlledByAI()
                                            break
                                        elif roundsubmenuSelect == 2:
                                            continue
                                        else:
                                            print("\nInvalid selection.\n")
                                elif roundmenuSelect == "pbar" and rndVisualOn == 1:
                                    while True:
                                        try:
                                            categories = []
                                            values = []
                                            custom_colors = []

                                            for t in teams:
                                                categories.append(t.getName())
                                                values.append(t.getPerf())
                                                tempCol = t.getColour().split(";")
                                                custom_colors.append((int(tempCol[3])/255,int(tempCol[4])/255,int(tempCol[5])/255))

                                            # Pass the list into the color parameter
                                            plt.bar(categories, values, color=custom_colors, edgecolor='black')

                                            plt.title('Performance Chart')
                                            plt.xlabel('Team')
                                            plt.xticks(rotation=40)
                                            plt.ylabel('Performance')
                                            minRange = max(0,min(values) - 50)
                                            maxRange = max(values) + 20
                                            plt.ylim(minRange, maxRange)
                                            plt.yticks(np.arange(minRange, maxRange + 1, 100))
                                            plt.interactive(False)
                                            plt.show()

                                            plt.show()
                                        except ValueError:
                                            print("\nAn error occurred with the RńD Chart.\n")
                                        else:
                                            break
                                elif roundmenuSelect == "pad":
                                    print(f"\n{"Team":32s} | {"Performance":<14} | {"Reliability"} | {"Money"}")
                                    print("-" * 72)
                                    for t in teams:
                                        if t.getSupplier() != None:
                                            nameGapLeft = 29 - len(t.getName()) - len(t.getSupplier().getName())
                                            print(f"{t.getColour()}{t.getName()}{t.getColReset()} - {t.getSupplier().getColour()}{t.getSupplier().getName()}{t.getSupplier().getColReset()}{" ":<{nameGapLeft}} | {t.getPerf():<14.2f} | {t.getRelDisplay()} | ${t.getMoney():.2f}M")
                                        else:
                                            print(f"{t.getColour()}{t.getName():32s}{t.getColReset()} | {t.getPerf():<14.2f} | {t.getRelDisplay()} | ${t.getMoney():.2f}M")
                                    print("-" * 72)
                                    input("\nPress 'SPACE' to continue...")
                                elif roundmenuSelect == "bre1":
                                    team.getDriver1().setContractLeft(1)
                                elif roundmenuSelect == "bre2":
                                    team.getDriver2().setContractLeft(1)
                                elif roundmenuSelect == "ret=t":
                                    print("Custom Ret is now TRUE.")
                                    customRet = True
                                elif roundmenuSelect == "ret=f":
                                    print("Custom Ret is now FALSE.")
                                    customRet = False
                                elif roundmenuSelect == "ret=a":
                                    if customRet:
                                        print("Custom Ret list confirmed.")
                                        customRetList2.clear()
                                        for d in customRetList[:]:
                                            customRetList2.append(d)
                                        for d in customRetList2[:]:
                                            print(d.getDriverName())
                                    else:
                                        print("\nCommand is unavailable at this time.")
                                    input("\nPress 'SPACE' to continue...")
                                elif roundmenuSelect[0] == 'r' and roundmenuSelect[1] == 'w':
                                    try:
                                        if len(roundmenuSelect) == 3:
                                            fixed_race_winner = driverChampionship[int(roundmenuSelect[2])-1]
                                        if len(roundmenuSelect) == 4:
                                            val = int(f"{roundmenuSelect[2]}{roundmenuSelect[3]}")
                                            fixed_race_winner = driverChampionship[int(val)-1]
                                    except:
                                        print("Invalid input - 'rw' command error.")
                                        input("\nPress 'SPACE' to continue...")
                                else:
                                    parts = roundmenuSelect.split(".")

                                    if len(parts) == 4 and parts[0] == "t":
                                        team_num = int(parts[1]) - 1
                                        action = parts[2]
                                        amount = float(parts[3])

                                        if action == "+":
                                            teams[team_num].addMoney(amount)
                                        elif action == "p":
                                            teams[team_num].addPerf(amount)

                                    else:
                                        print("\nInvalid selection.\n")

                            except Exception as e:
                                print("\nAN ERROR HAS BEEN PRODUCED!\n")

                # Pay drivers their roundly pay
                team.addMoney(-(team.getDriver1().getDriverSalary() / seasonLength + team.getDriver2().getDriverSalary() / seasonLength))

            #RACE WEEKEND
            clear_system()
            input("\nPress 'SPACE' to continue...\n")
            commentary_lines = [
                "Engines will roar. Tempers may flare. But one thing’s certain — the race weekend has begun.",
                "As the sun rises over the circuit, the battle lines are drawn. It’s time to go racing.",
                "Silence fades. The crowd waits. The stage is set for another chapter in this championship.",
                "Behind every visor is a story, and this weekend, a new one will be written.",
                "The teams have spoken with strategy. Now, the track will answer with truth.",
                "We’re all set here at the track! Preparations are done — the race weekend is officially underway!",
                "Team radios go quiet, pit crews step back, and we shift into race mode!",
                "From garage to grid, everything has led to this — welcome to the race weekend!",
                "It's race time, folks! Strategy meets speed as the weekend gets rolling.",
                "The lights may be off now, but they won’t stay that way for long — the weekend starts now!"
            ]
            print(random.choice(commentary_lines))
            input("\nPress 'SPACE' to continue...\n")

            simulateQual(teams)
            qualiResults = displayQualResults(teams)
            print()
            qualifying_commentary = [
                "Qualifying wraps up under the setting sun — and on pole, it's {pole_sitter}, leading the charge into tomorrow’s battle.",
                "Pole position locked out by {team_name}! {driver1} and {driver2} will lead the pack — now the question is, who will come out on top?",
                "It’s a power-packed front two rows: {driver1}, {driver2}, {driver3}, and {driver4}. Expect fireworks into Turn 1.",
                "One lap. One shot. And {pole_sitter} nailed it. The pole sitter is ready to write their name into the story of this weekend.",
                "From now on, it’s all about the race. The grid is set, tensions are rising, and the championship edge has never been sharper.",
                "Quali is in the books, and {pole_sitter} will lead the field when the lights go out. The rest? Chasing shadows for now.",
                "A stunning lap from {pole_sitter}! But it’s a long race ahead — and the pressure only builds from here.",
                "Four drivers, two rows, one dream — {driver1}, {driver2}, {driver3}, and {driver4} will start up front tomorrow. Let the mind games begin.",
                "They say Saturday sets the scene, but Sunday writes the script. The pole belongs to {pole_sitter} — let’s see who steals the spotlight next.",
                "With the grid locked in, all that remains is the calm before the chaos. Race day is coming."
            ]

            comment = random.choice(qualifying_commentary).format(
                pole_sitter = qualiResults[0].getDriverName(),
                team_name = qualiResults[0].getTeamAt().getName(),
                driver1 = qualiResults[0].getDriverName(),
                driver2 = qualiResults[1].getDriverName(),
                driver3 = qualiResults[2].getDriverName(),
                driver4 = qualiResults[3].getDriverName()
            )

            print(comment)
            input("\nPress 'SPACE' to continue...\n")

            simulateRace(teams)
            simulateRace2(driverChampionship2)
            raceResults = displayRaceResults(teams, pointsDist, fixed_race_winner)
            print()
            post_race_commentary = [
                "What a race! {winner} takes the win and etches their name into the history books.",
                "From lights out to the checkered flag, this one had it all. A stunning drive from {winner} in the {team_name} seals the deal.",
                "Victory belongs to {winner} in the {team_name}, but the stories behind the podium are just as gripping. What a weekend.",
                "A masterclass in control and pace — {winner} stands tall at the end of an unforgettable Grand Prix.",
                "The dust settles on another explosive race weekend. Hearts were broken, legends were made.",
                "When the pressure mounted, {winner} delivered. A brilliant drive, start to finish.",
                "That’s a wrap on this Grand Prix — twists, turns, and tension from lap one to the very end.",
                "As the engines cool and the teams pack up, the paddock buzzes with one name: {winner}.",
                "The checkered flag falls, and it’s {winner} in the {team_name} who claims glory. The season just got even more interesting.",
                "Another chapter closes in this season’s battle. But if today showed anything — it’s far from over."
            ]

            comment = random.choice(post_race_commentary).format(
                winner = raceResults[0].getDriverName(),
                team_name = raceResults[0].getTeamAt().getName()
            )
            print(comment)
            driverWinHistory[season][round][0][0] = raceResults[0].getDriverName()
            driverWinHistory[season][round][0][1] = raceResults[0].getTeamAt().getColour()
            driverWinHistory[season][round][1][0] = raceResults[1].getDriverName()
            driverWinHistory[season][round][1][1] = raceResults[1].getTeamAt().getColour()
            driverWinHistory[season][round][2][0] = raceResults[2].getDriverName()
            driverWinHistory[season][round][2][1] = raceResults[2].getTeamAt().getColour()
            raceResults[0].addSeasonRWins(1)
            input("\nPress 'SPACE' to continue...\n")

            #POST-RACE UPDATES
            for t in teams:
                t.updateBestPos()
                if t.getDriver1().getDriverPoints() < t.getDriver2().getDriverPoints():
                    tempObj = t.getDriver2()
                    t.setDriver2(t.getDriver1())
                    t.setDriver1(tempObj)
            teams = updateConstructorChampionship(teams)
            driverChampionship = updateDriverChampionship(driverChampionship)
            driverChampionship2 = updateDriverChampionship2(driverChampionship2)




        # **** END OF SEASON: Showing the Final Standings ****

        '''

        | Phase                 | Purpose                   |
        | --------------------- | ------------------------- |
        | 1. Contract expiry    | drivers become free       |
        | 2. Market valuation   | driver worth recalculated |
        | 3. Team needs         | who is weak/strong        |
        | 4. AI targeting       | who teams want            |
        | 5. Offer generation   | salary + years            |
        | 6. Negotiation        | best offer wins           |
        | 7. Promotions         | fill empty seats          |
        | 8. Free agent cleanup | leftovers                 |

        '''

        clear_system()
        print(f"The end of F1 {seasonPick + season} is here....")
        time.sleep(2)
        print(f"and {Race.format_driver_basic(driverChampionship[0].getDriverName(), driverChampionship[0].getTeamAt().getColour())} in the {driverChampionship[0].getTeamAt().getName()} has won the Driver Championship,\nand {teams[0].getName()} has won the Constructor Championship!")
        print("\nHere are the final standings:\n")
        driverChampionship[0].addDriverCha()
        displayDriverChampionship(driverChampionship)
        print() #Space between standings
        displayConstructorChampionship(teams)
        print(f"\nIn the lower racing category, {driverChampionship2[0].getDriverName()} wins F2 {seasonPick + season}! They cannot race in F2 anymore, which means"
              f"\n{driverChampionship2[0].getDriverName()} will have to find a Formula One race seat as soon as possible. Which team will take a leap of faith?")
        input("\nPress 'SPACE' to continue...\n")

        # POST-SEASON DATA UPDATES AND RESETS
        free_agents.insert(0, driverChampionship2.pop(0))
        free_agents[0].setTeamAt("F2 Champion")
        championshipDriverWinners.append(driverChampionToList(driverChampionship[0], teams[0])) #History making line of code
        print()

        print(displayDriverChampions(championshipDriverWinners))
        input("\nPress 'SPACE' to continue...")

        # ** RETIREMENTS **
        newRetiredDrivers = []

        if len(customRetList2) == 0:
            tempPos = 0
            to_remove = []


            # Iterate Over Formula 1 Championship
            for d in driverChampionship[:]:
                isRetiringBool = isRetiring(d)

                if isRetiringBool:
                    newRetiredDrivers.append(d)
                    to_remove.append(d)
                    d.setContractLeft(1)

            for d in to_remove:
                driverChampionship.remove(d)

            # Iterate Over Free Agents
            tempPos = 0
            to_remove = []
            for d in free_agents[:]:
                tempPos += 1
                isRetiringBool = False

                if d.getDriverAge() >= retMinAge - 2:
                    retireChance = 20.0 + ((d.getDriverAge()-retMinAge) * 5)
                    if random.random() * 100 <= retireChance or d.getDriverAge() >= retMinAge + 15:
                        isRetiringBool = True

                if d.getDriverAge() == 49:
                    isRetiringBool = True

                if isRetiringBool:
                    newRetiredDrivers.append(d)
                    to_remove.append(d)
                    d.setContractLeft(1)

            for d in to_remove:
                free_agents.remove(d)

            # Iterate Over Formula 2 Championship
            tempPos = 0
            to_remove = []
            for d in driverChampionship2[:]:
                tempPos += 1
                isRetiringBool = False

                if d.getDriverAge() >= retMinAge - 2:
                    retireChance = 20.0 + ((d.getDriverAge() - retMinAge) * 5)
                    if random.random() * 100 <= retireChance or d.getDriverAge() >= retMinAge + 15:
                        isRetiringBool = True

                if d.getDriverAge() == 49:
                    isRetiringBool = True

                if isRetiringBool:
                    newRetiredDrivers.append(d)
                    to_remove.append(d)
                    d.setContractLeft(1)

            for d in to_remove:
                driverChampionship2.remove(d)

        else: #CUSTOM RET
            to_remove = []

            # Iterate Over Formula 1 Championship
            for d in driverChampionship[:]:
                if d in customRetList2:
                    newRetiredDrivers.append(d)
                    to_remove.append(d)
                    d.setContractLeft(1)

            for d in to_remove:
                driverChampionship.remove(d)

            # Iterate Over Free Agents
            to_remove = []
            for d in free_agents[:]:
                if d in customRetList2:
                    newRetiredDrivers.append(d)
                    to_remove.append(d)
                    d.setContractLeft(1)

            for d in to_remove:
                free_agents.remove(d)

            # Iterate Over Formula 2 Championship
            to_remove = []
            for d in driverChampionship2[:]:
                if d in customRetList2:
                    newRetiredDrivers.append(d)
                    to_remove.append(d)
                    d.setContractLeft(1)

            for d in to_remove:
                driverChampionship2.remove(d)

        # Retirement Announcements
        if len(newRetiredDrivers) > 0:
            print("\nBREAKING:\nThe following drivers are retiring.\n")
            for d in newRetiredDrivers:
                try:
                    col = d.getTeamAt().getColour()
                except:
                    col = "\033[1;38;2;200;200;255;49m"
                print(f"{Race.format_driver(d.getDriverName(), col, d.getDriverCha())} at the age of {d.getDriverAge()}")
        input("\nPress 'SPACE' to continue...")

        # F1 Driver Stats and Info Updates
        tempPos = 0
        for d in driverChampionship:
            tempPos += 1
            d.addDriverAge(1)
            d.addContractExtension(-1)

            # Market Value Updates
            tempTeamPos = 1
            for t in teams:
                if d.getTeamAt() == t:
                    break
                tempTeamPos += 1

            if d.getTeamAt().getDriver1() == d:
                teammatePoints = d.getTeamAt().getDriver2().getDriverPoints()
                teammateRep = d.getTeamAt().getDriver2().getDriverRep()
            else:
                teammatePoints = d.getTeamAt().getDriver1().getDriverPoints()
                teammateRep = d.getTeamAt().getDriver1().getDriverRep()

            #

            ageVal = (d.getDriverAge() / 20) * 3.5
            posVal = (len(driverChampionship) - (tempPos - 1)) / len(driverChampionship) * 8

            val = (d.getDriverSalary() * 0.6) + (ageVal * 0.2) + (posVal * 0.2)

            '''if teammatePoints > 0:
                val = (((d.getDriverPoints() - teammatePoints) / teammatePoints) * (teammateRep / d.getDriverRep())) + (-(tempTeamPos - (gridSize / 2)) / (gridSize / 2))
            elif d.getDriverPoints() > 0:
                val = ((((tempTeamPos * 2) / tempPos) - 1) + ((gridSize - (tempTeamPos * 2)) / (gridSize * 2)))

            val = (d.getDriverSalary() + (d.getDriverSalary() + val)) / 2'''


            d.setDriverSalary(val)

            if d.getDriverSalary() > 10:
                d.setDriverSalary(10)
            elif d.getDriverSalary() < 0.5:
                d.setDriverSalary(0.5)

            # Driver Rating Updates
            d.addDriverPerf(DSUS(d))

        for d in newRetiredDrivers:
            if d.getTeamAt() in teams:
                if d.getTeamAt().getDriver1() == d:
                    d.getTeamAt().setDriver1(None)
                else:
                    d.getTeamAt().setDriver2(None)
            d.setTeamAt(None)

        # FA Driver Stats and Info Updates
        for d in free_agents:
            d.addDriverAge(1)
            d.addDriverPerf(DSUS(d))

        # F2 Driver Stats and Info Updates
        for d in driverChampionship2:
            d.addDriverAge(1)
            d.addDriverPerf(DSUS(d))

        # QD Driver Stats and Info Updates
        for d in queuedDrivers:
            d.addDriverAge(1)
            d.addDriverPerf(DSUS(d))

        # Sorting drivers within teams
        for t in teams:
            if t.getDriver1() is None and t.getDriver2() is not None:
                t.setDriver1(t.getDriver2())
                t.setDriver2(None)

        # F1 Team Prize Money Distribution
        pos = 0
        for t in teams:
            pos += 1

            if pos == 1:
                t.addMoney(12.0)  # Originally 12.0
            elif pos != 1:
                t.addMoney(11.0 - (0.65 * pos))  # Originally 11.0 - (0.65 * pos)

        ''' **** WINTER BREAK **** '''

        drivertransferList = []
        for team in teams:
            clear_system()
            availableSeat = (team.getDriver1() is None or team.getDriver1().getContractLeft() == 0) or (
                    team.getDriver2() is None or team.getDriver2().getContractLeft() == 0)

            if team.isControlledByAI() == False:  # Player
                if team.getSupplier() != None:
                    print(f"\nTeam: {team.getColour()}{team.getName()}{team.getColReset()} - {team.getSupplier().getColour()}{team.getSupplier().getName()}{team.getSupplier().getColReset()}")
                else:
                    print(f"\nTeam: {team.getColour()}{team.getName()}{team.getColReset()}")
                input("\nPress 'SPACE' to continue...")

                while True:
                    clear_system()
                    availableSeat = (team.getDriver1() is None or team.getDriver1().getContractLeft() == 0) or (
                                team.getDriver2() is None or team.getDriver2().getContractLeft() == 0)
                    menuSelect = 0
                    print(f"\nEnd of {seasonPick + season} | Winter Break")
                    if team.getSupplier() != None:
                        print(f"🏎️ {"TEAM:":10s}{team.getColour()}{team.getName()}{team.getColReset()} - {team.getSupplier().getColour()}{team.getSupplier().getName()}{team.getSupplier().getColReset()}")
                    else:
                        print(f"🏎️ {"TEAM:":10s}{team.getColour()}{team.getName()}{team.getColReset()}")
                    print(f"💵 {"FUNDS:":10s}{format_money(team.getMoney())}")

                    condition1 = not availableSeat
                    if condition1:
                        print(f"(1)  Driver Lineup  -  {ADVANCE_COLOUR}Satisfied{RESET}")
                    else:
                        print(f"(1)  Driver Lineup  -  {RED_COLOUR}Not Satisfied{RESET}")
                    print("(2)  Driver Market")
                    print("(3)  Team Market")
                    print(f"(4)  Rebrand {team.getColour()}{team.getName()}{team.getColReset()}")

                    advance_avail = condition1
                    if advance_avail:
                        print("(a)  ADVANCE")
                    else:
                        print(f"(a)  ADVANCE - {RED_COLOUR}locked{RESET}")

                    menuSelect = input("Input: ")

                    if menuSelect == "1":
                        while True:
                            try:
                                clear_system()
                                menuSelect = 0
                                print("\n(b)  Back")
                                if team.getDriver1() != None:
                                    print(f"(1)  Driver 1: {team.getColour()}{team.getDriver1().getDriverName()}{RESET} - under contract for the next {team.getDriver1().getContractLeft()} year(s).")
                                else:
                                    print(f"     Driver 1: [Open Seat]")
                                if team.getDriver2() != None:
                                    print(f"(2)  Driver 2: {team.getColour()}{team.getDriver2().getDriverName()}{RESET} - under contract for the next {team.getDriver2().getContractLeft()} year(s).")
                                else:
                                    print(f"     Driver 2: [Open Seat]")

                                menuSelect = input("Input: ")
                                if menuSelect == "b":
                                    break
                                if (team.getDriver1() != None and menuSelect == "1") or (team.getDriver2() != None and menuSelect == "2"):
                                    if menuSelect == "1":
                                        driverPicked = team.getDriver1()
                                    if menuSelect == "2":
                                        driverPicked = team.getDriver2()
                                    while True:
                                        menuSelect = 0
                                        print(f"\n{team.getColour()}{driverPicked.getDriverName()} | Aged {driverPicked.getDriverAge()} | {driverPicked.getContractLeft()} year(s) |{RESET}")
                                        print("(b)  Back")
                                        print("(1)  Break Contract")

                                        menuSelect = input("Input: ")
                                        if menuSelect == "b":
                                            break
                                        if menuSelect == "1":
                                            menuSelect = 0
                                            conbremoney = 1+driverPicked.getDriverSalary()*driverPicked.getContractLeft()
                                            print(f"Action info:\n\tThe driver's contract will immediately end with the team.")
                                            print(f"\tYou must pay them a total of ${conbremoney:.2f}M for them to leave.")
                                            print(f"\tCURRENT FUNDS:  ${format_money(team.getMoney())}")
                                            print(f"\tFUTURE FUNDS:  ${format_money(team.getMoney() - conbremoney)}")
                                            print("Confirm Contract Break?")
                                            print("(b)  Back")
                                            print("(1)  Confirm")
                                            menuSelect = input("Input: ")
                                            if menuSelect == "b":
                                                break
                                            if menuSelect == "1":
                                                team.addMoney(-(1+driverPicked.getDriverSalary()*driverPicked.getContractLeft()))
                                                driverPicked.setContractLeft(0)
                                                print(f"You have successfully ended the contract for {driverPicked.getDriverName()}.")
                                                availableSeat = (team.getDriver1() is None or team.getDriver1().getContractLeft() == 0) or (team.getDriver2() is None or team.getDriver2().getContractLeft() == 0)
                                                input("\nPress 'SPACE' to continue...")
                                                break
                                if menuSelect == "2":
                                    break
                            except ValueError:
                                print("Invalid input.")

                    if menuSelect == "2":
                        while True:
                            try:
                                clear_system()
                                displayDriverMarket(driverChampionship, free_agents, driverChampionship2, True)
                                print(f"Enter 'i' num to select a driver (or '0' to go back).")
                                driverIndex = int(input("Input: "))
                                if driverIndex == 0:
                                    break
                                elif 1 <= driverIndex <= len(driverChampionship):
                                    while True:
                                        driverPicked = driverChampionship[driverIndex - 1]
                                        menuSelect = 0
                                        # DISPLAY DRIVER STATS
                                        print(f"\n{driverPicked.getTeamAt().getColour()}| {driverPicked.getDriverName()} | Aged {driverPicked.getDriverAge()} | {driverPicked.getContractLeft()} year(s) |{RESET}")
                                        print("(b)  Back")
                                        print("(1)  Approach - driver must have 0 contract left.")
                                        menuSelect = input("Input: ")
                                        if menuSelect == "b":
                                            break
                                        if menuSelect == "1" and availableSeat:
                                            if (driverPicked.getContractLeft() in [0,None]):
                                                while True:
                                                    try:
                                                        conLenTemp = int(input("\nContract Length (type '0' to go back): "))
                                                        if conLenTemp == 0:
                                                            break
                                                        if not 1 <= conLenTemp <= 4:
                                                            print("Invalid input - must be 1, 2, 3, or 4.")
                                                            continue
                                                    except ValueError:
                                                        print("Invalid input - must be an integer.")
                                                    else:
                                                        driverPicked.setContractLeft(conLenTemp)
                                                        if driverPicked in driverChampionship:

                                                            if driverPicked.getTeamAt() != team:

                                                                if driverPicked.getTeamAt().getDriver1() == driverPicked:
                                                                    driverPicked.getTeamAt().setDriver1(None)
                                                                elif driverPicked.getTeamAt().getDriver2() == driverPicked:
                                                                    driverPicked.getTeamAt().setDriver2(None)

                                                                dctl = (f"{Race.format_driver(driverPicked.getDriverName(), team.getColour(), driverPicked.getDriverCha())}"
                                                                        f" from {format_team(driverPicked.getTeamAt(), True)}"
                                                                        f" to {format_team(team, True)}")

                                                                drivertransferList.append(dctl)
                                                                driverPicked.setTeamAt(team)

                                                                # Assign the new driver to the first available slot
                                                                if team.getDriver2() != driverPicked and (team.getDriver1() is None or team.getDriver1().getContractLeft() == 0):
                                                                    team.setDriver1(driverPicked)
                                                                elif team.getDriver2() is None or team.getDriver2().getContractLeft() == 0:
                                                                    team.setDriver2(driverPicked)
                                                                else:
                                                                    # Both slots are occupied with valid contracts, this should not happen here
                                                                    print("Warning: Attempted to assign a F1 driver when both slots are filled.")
                                                                    break
                                                            else:
                                                                dctl = (f"{Race.format_driver(driverPicked.getDriverName(), team.getColour(), driverPicked.getDriverCha())}"
                                                                        f" extends contract with {format_team(team, True)}")
                                                                drivertransferList.append(dctl)
                                                                driverPicked.setTeamAt(team)
                                                                if team.getDriver1() != driverPicked:
                                                                    team.setDriver2(driverPicked)
                                                        print(f"You have signed {Race.format_driver_basic(driverPicked.getDriverName(), team.getColour())} for {conLenTemp} seasons(s)!")
                                                        availableSeat = (team.getDriver1() is None or team.getDriver1().getContractLeft() == 0) or (team.getDriver2() is None or team.getDriver2().getContractLeft() == 0)
                                                        break
                                                        # TODO: Ensure newly signed driver is added properly to new team.
                                            else:
                                                print("Invalid input - driver is already under contract.")
                                                input("\nPress 'SPACE' to continue...")
                                        else:
                                            print("Invalid input - your team has a full driver lineup.")
                                            input("\nPress 'SPACE' to continue...")
                            except ValueError:
                                print("Invalid input.")
                                input("\nPress 'SPACE' to continue...")

                    if menuSelect == "3":
                        while True:
                            try:
                                clear_system()
                                displayTeamMarket(teams)
                                print(f"Enter 'i' num to select a team (or '0' to go back).")
                                teamIndex = int(input("Input: "))
                                if teamIndex == 0:
                                    break
                                elif 1 <= teamIndex <= len(driverChampionship):
                                    while True:
                                        teamPicked = teams[teamIndex - 1]
                                        if teamPicked.getSupplier() is not None:
                                            supName = f"{format_team(teamPicked.getSupplier(), False)}{teamPicked.getColour()}"
                                        else:
                                            supName = "N/A"
                                        tier = classify_team(team, teams)
                                        if teamPicked.getSupplier() is team:
                                            breakCost = 15
                                        elif team.getSupplier() is teamPicked:
                                            breakCost = 15
                                        menuSelect = 0
                                        # DISPLAY TEAM STATS
                                        print(f"\n{teamPicked.getColour()}| {teamPicked.getName()} | Supplier: {supName} |{RESET}")
                                        print("(b)  Back")
                                        if tier == "back":
                                            print(f"(1)  Begin Supplying  --> {ADVANCE_COLOUR}Available{RESET}.")
                                        else:
                                            print(f"(1)  Begin Supplying  --> {RED_COLOUR}Not Available{RESET}.")
                                        print(f"(1)  ")
                                        print(f"(2)  Break Partnership - Costs ${breakCost:.2f}M.")
                                        menuSelect = input("Input: ")
                                        if menuSelect == "b":
                                            break
                                        if menuSelect == "1":
                                            print(f"\n{teamPicked.getColour()}| {teamPicked.getName()} | Supplier: {supName} |{RESET}")
                                            print("")
                                            print("(1)  CONFIRM Team Signing")
                                            print("(2)  CANCEL")

                                            if tier == "back":
                                                if teamPicked.getSupplier() is None:
                                                    print(f"You have signed {teamPicked.getColour()}{teamPicked.getName()}{RESET} as a customer team!")
                                                else:
                                                    print(f"Because ")
                                            else:
                                                print("Invalid input - the team you're trying to supply isn't available.")
                                                input("\nPress 'SPACE' to continue...")
                                        if menuSelect == "2":
                                            if teamPicked.getSupplier() is team:

                                                break
                            except ValueError:
                                print("Invalid input.")
                                input("\nPress 'SPACE' to continue...")
                    if menuSelect == "4":
                        break
                    if menuSelect == "a":
                        if advance_avail:
                            break
                        else:
                            print("You can't proceed until all end-of-season requirements are met.")
                            input("\nPress 'SPACE' to continue...")

            elif team.isControlledByAI() == True and availableSeat:  # AI
                while availableSeat:

                    tier = classify_team(team, teams)

                    # CHECK if driver 1 finished in the top 4 (automatically sign if so)
                    if team.getDriver1() is not None and team.getDriver1().getContractLeft() == 0 and team.getDriver1() in [driverChampionship[0], driverChampionship[1], driverChampionship[2], driverChampionship[3]]:
                        new_driver = team.getDriver1()

                    # CHECK if driver 2 finished in the top 4 (automatically sign if so)
                    elif team.getDriver2() is not None and team.getDriver2().getContractLeft() == 0 and team.getDriver2() in [driverChampionship[0], driverChampionship[1], driverChampionship[2], driverChampionship[3]]:
                        new_driver = team.getDriver2()

                    # BUILD candidate pool (could include current driver(s))
                    else:
                        candidate_pool = build_candidate_pool(team, driverChampionship, free_agents, driverChampionship2)
                        new_driver = choose_best_candidate(team, tier, candidate_pool)

                    if tier == "front":
                        if new_driver.getDriverRep() < 3.0:
                            potentialInt = [1, 1, 2, 2, 2]
                            new_driver.setContractLeft(random.choice(potentialInt))
                        elif 3.5 <= new_driver.getDriverRep() < 4.0:
                            potentialInt = [2, 2, 2, 3, 3]
                            new_driver.setContractLeft(random.choice(potentialInt))
                        else:
                            potentialInt = [2, 3, 3, 4, 4]
                            new_driver.setContractLeft(random.choice(potentialInt))
                    elif tier == "mid":
                        if new_driver.getDriverRep() < 2.5:
                            potentialInt = [1, 1, 2, 2, 2]
                            new_driver.setContractLeft(random.choice(potentialInt))
                        elif 2.5 <= new_driver.getDriverRep() < 3.5:
                            potentialInt = [2, 2, 2, 3, 3]
                            new_driver.setContractLeft(random.choice(potentialInt))
                        else:
                            potentialInt = [2, 2, 3, 3, 4]
                            new_driver.setContractLeft(random.choice(potentialInt))
                    else:
                        if new_driver.getDriverRep() < 2.0:
                            new_driver.setContractLeft(1)
                        elif 2.0 <= new_driver.getDriverRep() < 3.0:
                            potentialInt = [2, 2, 3, 3, 3]
                            new_driver.setContractLeft(random.choice(potentialInt))
                        else:
                            potentialInt = [2, 3, 3, 4, 4]
                            new_driver.setContractLeft(random.choice(potentialInt))

                    if new_driver in driverChampionship:

                        if new_driver.getTeamAt() != team:

                            if new_driver.getTeamAt().getDriver1() == new_driver:
                                new_driver.getTeamAt().setDriver1(None)
                            elif new_driver.getTeamAt().getDriver2() == new_driver:
                                new_driver.getTeamAt().setDriver2(None)

                            drivertransferList.append(f"{Race.format_driver(new_driver.getDriverName(), team.getColour(), new_driver.getDriverCha())} from {format_team(new_driver.getTeamAt(), True)} to {format_team(team, True)}")
                            new_driver.setTeamAt(team)

                            # Assign the new driver to the first available slot
                            if team.getDriver2() != new_driver and (team.getDriver1() is None or team.getDriver1().getContractLeft() == 0):
                                team.setDriver1(new_driver)
                            elif team.getDriver2() is None or team.getDriver2().getContractLeft() == 0:
                                team.setDriver2(new_driver)
                            else:
                                # Both slots are occupied with valid contracts, this should not happen here
                                print("Warning: Attempted to assign a F1 driver when both slots are filled.")
                                break
                        else:
                            # drivertransferList.append(f"{team.getColour()}{new_driver.getDriverName():<20}{RESET} | {new_driver.getTeamAt().getColour()}{new_driver.getTeamAt().getName():>16}{RESET} ➡︎ {team.getColour()}{team.getName():<16}{RESET} (extended)")
                            drivertransferList.append(f"{Race.format_driver(new_driver.getDriverName(), team.getColour(), new_driver.getDriverCha())} extends contract with {format_team(team, True)}")
                            new_driver.setTeamAt(team)
                            if new_driver.getTeamAt().getDriver1() != new_driver:
                                team.setDriver2(new_driver)


                    elif new_driver in free_agents:

                        free_agents.remove(new_driver)
                        driverChampionship.append(new_driver)
                        if new_driver.getTeamAt() in ["Free Agent", "F2 Champion"]:
                            drivertransferList.append(f"{Race.format_driver(new_driver.getDriverName(), team.getColour(), new_driver.getDriverCha())} from {FAColour}{new_driver.getTeamAt()}{RESET} to {format_team(team, True)}")
                        else:
                            drivertransferList.append(f"{Race.format_driver(new_driver.getDriverName(), team.getColour(), new_driver.getDriverCha())} from {format_team(new_driver.getTeamAt(), True)} {FAColour}T&R{RESET} to {format_team(team, True)}")
                        new_driver.setTeamAt(team)

                        # Assign the new driver to the first available slot
                        if team.getDriver1() is None or team.getDriver1().getContractLeft() == 0:
                            team.setDriver1(new_driver)
                        elif team.getDriver2() is None or team.getDriver2().getContractLeft() == 0:
                            team.setDriver2(new_driver)
                        else:
                            # Both slots are occupied with valid contracts, this should not happen here
                            print("Warning: Attempted to assign a FA driver when both slots are filled.")
                            break


                    elif new_driver in driverChampionship2:

                        driverChampionship2.remove(new_driver)
                        driverChampionship.append(new_driver)
                        if new_driver.getTeamAt() in ["Formula 2"]:
                            drivertransferList.append(f"{Race.format_driver(new_driver.getDriverName(), team.getColour(), new_driver.getDriverCha())} from {F2Colour}{new_driver.getTeamAt()}{RESET} to {format_team(team, True)}")
                        else:
                            drivertransferList.append(f"{Race.format_driver(new_driver.getDriverName(), team.getColour(), new_driver.getDriverCha())} from F2 {format_team(new_driver.getTeamAt(), True)} Junior to {format_team(team, True)}")
                        new_driver.setTeamAt(team)

                        # Assign the new driver to the first available slot
                        if team.getDriver1() is None or team.getDriver1().getContractLeft() == 0:
                            team.setDriver1(new_driver)
                        elif team.getDriver2() is None or team.getDriver2().getContractLeft() == 0:
                            team.setDriver2(new_driver)
                        else:
                            # Both slots are occupied with valid contracts, this should not happen here
                            print("Warning: Attempted to assign a F2 driver when both slots are filled.")
                            break

                    availableSeat = (team.getDriver1() is None or team.getDriver1().getContractLeft() == 0) or (team.getDriver2() is None or team.getDriver2().getContractLeft() == 0)

        new_driverChampionship = []
        for d in driverChampionship:
            if d.getContractLeft() == 0:
                free_agents.insert(0,d)
                drivertransferList.append(f"{Race.format_driver(d.getDriverName(), d.getTeamAt().getColour(), d.getDriverCha())} from {format_team(d.getTeamAt(), True)} to {FAColour}Free Agent{RESET}")
                d.setTeamAt("Free Agent")
            else:
                new_driverChampionship.append(d)

        # F1 Resets & Updates
        driverChampionship = new_driverChampionship

        for t in teams:

            if t.getDriver1() is not None:
                t.getDriver1().resetDriverPoints()
                t.getDriver1().setBestPos(None)
                t.getDriver1().resetSeasonRWins()
            if t.getDriver2() is not None:
                t.getDriver2().resetDriverPoints()
                t.getDriver2().setBestPos(None)
                t.getDriver2().resetSeasonRWins()

            t.resetPoints()
            t.setBestPos(None)

            '''if (seasonPick + season) + 1 == 2026 and t.getName() == "Sauber":
                t.setName("Audi"); t.setSName("Audi"); t.setColour(AudiColour)
                t.addMoney(10.0)'''

        # F2 Resets
        for d in driverChampionship2:
            d.resetDriverPoints()
            d.setBestPos(None)

        # F3 (Queued) Drivers to Join the F2 Grid
        F2_grid_size = 22
        if len(poolOfDrivers) < 65:
            F2_grid_size = 18
        if len(poolOfDrivers) < 40:
            F2_grid_size = 14
        if len(poolOfDrivers) < 20:
            F2_grid_size = 12
        if len(poolOfDrivers) == 0 and len(driverChampionship2) >= 8:
            F2_grid_size = len(driverChampionship2)
        if len(poolOfDrivers) == 0 and len(driverChampionship2) < 8:
            print("F2 category has run out of F3 drivers to promote. Series has ended. Thanks for playing.")
            exit(0)

        while len(driverChampionship2) < F2_grid_size:
            randomNum = random.random()
            if 0.7 <= randomNum <= 1.0: # 30%
                driverChampionship2.append(queuedDrivers.pop(0))
            elif 0.4 <= randomNum < 0.7: # 30%
                driverChampionship2.append(queuedDrivers.pop(1))
            elif 0.2 <= randomNum < 0.4: # 20%
                driverChampionship2.append(queuedDrivers.pop(2))
            elif 0.1 <= randomNum < 0.2: # 10%
                driverChampionship2.append(queuedDrivers.pop(3))
            elif 0.0 <= randomNum < 0.1: # 10%
                driverChampionship2.append(queuedDrivers.pop(4))

            driverChampionship2[-1].setTeamAt("Formula 2")
            queuedDrivers.append(poolOfDrivers.pop(0))

        # If the following year = reg year...
        # TODO: FIX REG CHANGES
        '''if ((seasonPick + season + 1) == regChangeYear):
            regChangeYear += regIntervals

            gridPerfAvgList = []
            for t in teams:
                gridPerfAvgList.append(t.getPerf())

            gridPerfTotal = 0

            for i in gridPerfAvgList:
                gridPerfTotal += i

            gridPerfAvg = gridPerfTotal / len(gridPerfAvgList)

            tempTeamPos = 0
            for t in teams:
                t.setPerf(regChange(gridPerfAvg, 50 + teams[tempTeamPos].getPerf() - teams[-1].getPerf(), t.getPerf(), t.getRes()))
                t.resetRes()
                tempTeamPos += 1

            while teams[0].getPerf() - teams[-1].getPerf() >= 225:
                tempTeamPos = 0
                for t in teams:
                    t.setPerf(t.getPerf() + ((teams[0].getPerf() - t.getPerf()) / 2.0))
                    tempTeamPos += 1

            while teams[0].getPerf() >= 400:
                for t in teams:
                    t.setPerf(t.getPerf() - 100)'''

        #regSqueeze(teams)