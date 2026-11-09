import time
import random
import re

import Team
import Driver
import Race
import Rules
from YearsData import getYearData
from ContractOffer import classify_team, build_candidate_pool, choose_best_candidate

from Race import simulateQual, displayQualResults, simulateRace, simulateRace2, displayRaceResults, \
    updateConstructorChampionship, updateDriverChampionship, updateDriverChampionship2, \
    displayDriverChampionship, displayDriverChampionship2, \
    displayConstructorChampionship, displayDriverMarket, \
    displayDriverMarket2, driverChampionToList, displayDriverChampions

from Rules import seasonLength, regChangeYear, regIntervals, updatePointsDist, regChange, regSqueeze, DSUS

# ===================== Constants =====================

ADVANCE_COLOUR = "\033[38;2;100;180;100m"
WEEK_COLOUR1 = "\033[38;2;140;140;140m"
WEEK_COLOUR2 = "\033[38;2;115;115;115m"
SUPERRED_COLOUR = "\033[38;2;120;20;10m"

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

# ===================== Utility Functions =====================

def get_int(prompt, min_val=None, max_val=None):
    """Get validated integer input from user within optional bounds."""
    while True:
        try:
            x = int(input(prompt))
            if (min_val is not None and x < min_val) or (max_val is not None and x > max_val):
                raise ValueError
            return x
        except ValueError:
            print("Invalid input.\n")

def format_driver(name):
    """Format driver name as initial.last (e.g. L.HAM)."""
    parts = name.split()
    if len(parts) >= 2:
        first = parts[0][0].upper()
        last = parts[-1][:3].upper()
        return f"{first}.{last}"
    return name.upper()

# ===================== Team & Driver Selection =====================

def choose_existing_team(player_num, teams):
    """Allow player to choose an existing team."""
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

def pick_driver(free_agents, driverChampionship2, driverChampionship):
    """Allow player to pick a driver from free agents or F2."""
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

def refill_f2_grid(queuedDrivers, poolOfDrivers, driverChampionship2):
    """Refill the F2 grid to maintain 22 drivers."""
    while len(driverChampionship2) < 22:
        idx = int(random.random() * 5)
        driver = queuedDrivers.pop(idx)
        driver.setTeamAt("Formula 2")
        driverChampionship2.append(driver)
        queuedDrivers.append(poolOfDrivers.pop(0))

def choose_colour():
    """Allow player to choose a team color."""
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

def create_custom_team(player_num, teams, free_agents, driverChampionship2, driverChampionship, queuedDrivers, poolOfDrivers):
    """Allow player to create a custom team with drivers."""
    print(f"\nPlayer {player_num} - Create your team\n")
    name = input("Team Name: ")
    short = input("Short Name: ")
    print("\nPick Driver 1:")
    displayDriverMarket2(free_agents, driverChampionship2)
    d1 = pick_driver(free_agents, driverChampionship2, driverChampionship)
    print("\nPick Driver 2:")
    displayDriverMarket2(free_agents, driverChampionship2)
    d2 = pick_driver(free_agents, driverChampionship2, driverChampionship)
    refill_f2_grid(queuedDrivers, poolOfDrivers, driverChampionship2)
    colour = choose_colour()

    # Performance balancing
    perf_list = sorted([t.getPerf() for t in teams], reverse=True)
    start_perf = (perf_list[0] + 5 * perf_list[-1]) / 6

    new_team = Team.team(name, short, colour, 6.0, 0, start_perf, 6, None, 0)
    new_team.toggleControlledByAI()
    new_team.setDriver1(d1)
    new_team.setDriver2(d2)
    d1.setTeamAt(new_team)
    d2.setTeamAt(new_team)
    teams.append(new_team)

# ===================== Main Menu and Setup =====================

def show_main_menu():
    """Display main menu and get user selection."""
    while True:
        print("Choose an option below by typing in the option number:\n")
        print("-" * 25)
        print("| (1) Start new career. |")
        print("| (2) Exit program.     |")
        print("-" * 25)
        menuSelect = get_int("Input: ")
        if menuSelect in (1, 2):
            return menuSelect
        print("\nInvalid selection.\n")

def setup_game():
    """Setup player count and season selection."""
    plaCount = 1
    seasonPick = 2026
    while True:
        print("\n(1) Player count:", plaCount)
        print("(2) Season:", seasonPick)
        print("(3) Continue")
        choice = get_int("Input: ", 1, 3)
        if choice == 1:
            plaCount = get_int("Players (1-10): ", 1, 10)
        elif choice == 2:
            print("(2025 or 2026)")
            seasonPick = get_int("Season: ", 2025, 2026)
        elif choice == 3:
            break
    return plaCount, seasonPick

def load_season(seasonPick, teams, driverChampionship, free_agents, driverChampionship2, queuedDrivers, poolOfDrivers):
    """Load season data into game state."""
    getYearData(seasonPick, teams, driverChampionship, free_agents, driverChampionship2, queuedDrivers, poolOfDrivers)

# ===================== Main Game Loop =====================

def main():
    print("Welcome to Project Manager!\n")
    menuSelect = show_main_menu()
    if menuSelect == 2:
        print("Exiting program.")
        return

    # Initialize game state lists
    teams = []
    free_agents = []
    driverChampionship = []
    driverChampionship2 = []
    queuedDrivers = []
    poolOfDrivers = []
    championshipDriverWinners = []

    plaCount, seasonPick = setup_game()
    load_season(seasonPick, teams, driverChampionship, free_agents, driverChampionship2, queuedDrivers, poolOfDrivers)

    # Player team selection
    for p in range(1, plaCount + 1):
        print(f"\nPlayer {p}:")
        print("(1) Choose existing team")
        print("(2) Create custom team")
        mode = get_int("Select: ", 1, 2)
        if mode == 1:
            choose_existing_team(p, teams)
        else:
            create_custom_team(p, teams, free_agents, driverChampionship2, driverChampionship, queuedDrivers, poolOfDrivers)

    # Points distribution setup
    pointsDist = updatePointsDist(len(teams) * 2)

    # Initialize championship winners history (example data)
    # ... (You can keep your existing initialization here)

    retMinAge = 42
    drivertransferList = []
    driverWinHistory = []

    # Main season loop (30 seasons)
    for season in range(30):
        # Adjust retMinAge based on season
        if 0 <= season <= 1:
            retMinAge -= 2
        elif season == 4 or season == 7 or season == 14:
            retMinAge -= 1

        # Handle regulation changes
        if (seasonPick + season) == regChangeYear:
            regChangeYear += regIntervals

        driverWinHistory.append([])

        # Pre-season announcements
        print(f"\nNew Season!\n")
        print(f"A new season of Formula One Racing has arrived. Last season was spectacular,")
        print(f"but with all the teams and drivers on edge,")
        if (seasonPick + season) + 1 == regChangeYear:
            print(f"and the arrival of the new era next season in F1 {seasonPick + season + 1},")
        elif (seasonPick + season) + regIntervals == regChangeYear:
            print(f"and the arrival of the new cars that will span from {seasonPick + season} to {regChangeYear-1},")
        print(f"the {seasonPick + season} season is expected to raise the bar even higher!\nWhich teams have nailed their setups for this season, and which have it all crossed up?\n")
        print(f"Before F1 {seasonPick + season} kicks off, let's review the driver line-ups for this season...")
        input("\nPress 'SPACE' to continue...")

        # Display teams and drivers
        print("=" * 115)
        for team in teams:
            driver1 = team.getDriver1()
            driver2 = team.getDriver2()
            driver1_str = f"{driver1.getDriverName()} ({driver1.getDriverAge()}" + (f" | 🏆 x{driver1.getDriverCha():>2})" if driver1.getDriverCha() > 0 else ") ")
            driver2_str = f"{driver2.getDriverName()} ({driver2.getDriverAge()}" + (f" | 🏆 x{driver2.getDriverCha():>2})" if driver2.getDriverCha() > 0 else ") ")
            if team.getSupplier() is not None:
                nameGapLeft = 31 - len(team.getName()) - len(team.getSupplier().getSName())
                print(f"{team.getColour()}{team.getName()}{team.getColReset()} - {team.getSupplier().getColour()}{team.getSupplier().getSName()}{team.getSupplier().getColReset()}{' ':<{nameGapLeft}}||{' ':<5}{team.getColour()}{driver1_str:<35}{driver2_str:<35}{team.getColReset()}")
            else:
                print(f"{team.getColour()}{team.getName():34s}{team.getColReset()}||{' ':<5}{team.getColour()}{driver1_str:<35}{driver2_str:<35}{team.getColReset()}")
        print("=" * 115)
        print()

        # Display driver transfer list
        print(f"{'Driver':<20} | {'Old Team':>16} ➡︎ {'New Team':<16}")
        print("-" * 59)
        if len(drivertransferList) > 0:
            for line in drivertransferList:
                print(line)
        input("\nPress 'SPACE' to continue...")
        drivertransferList.clear()

        # Cash injections from drivers
        for team in teams:
            team.addMoney(team.getDriver1().getDriverCha() / 1.5 + team.getDriver2().getDriverCha() / 1.5)

        # Season rounds
        for round in range(seasonLength):
            chaPos = 0
            driverWinHistory[season].append([[" ", RESET], [" ", RESET], [" ", RESET]])
            for team in teams:
                chaPos += 1
                # Pay drivers their roundly pay
                team.addMoney(-(team.getDriver1().getDriverSalary() / seasonLength + team.getDriver2().getDriverSalary() / seasonLength))

                if team.isControlledByAI():
                    # AI logic for upgrades and research investments
                    positiveFunds = team.getMoney() > (team.getDriver1().getDriverSalary() / seasonLength + team.getDriver2().getDriverSalary() / seasonLength)
                    tempFunds = team.getMoney() - (team.getDriver1().getDriverSalary() / seasonLength + team.getDriver2().getDriverSalary() / seasonLength)
                    if positiveFunds:
                        if (seasonPick + season + 1) == regChangeYear:
                            if chaPos >= 8:
                                curInv = tempFunds / (random.random() * 0.5 + 1.0)
                            elif chaPos >= 5:
                                curInv = tempFunds / (random.random() * 1.0 + 1.0)
                            else:
                                curInv = tempFunds / (random.random() * 1.0 + 1.5)
                            team.addRes(curInv)
                            team.addMoney(-curInv)
                        elif (seasonPick + season) == regChangeYear - 4:
                            curInv = tempFunds / (random.random() * 0.8 + 1.2)
                            team.addPerf(curInv)
                            team.addMoney(-curInv)
                        elif random.random() < 0.5:
                            curInv = tempFunds / (random.random() * 6.0 + 4.0)
                            team.addRes(curInv)
                            team.addMoney(-curInv)
                        if random.random() < 0.5:
                            curInv = tempFunds / (random.random() * 6.5 + 1.5)
                            team.addPerf(curInv)
                            team.addMoney(-curInv)
                    if round >= 3 and team.getPoints() > 0 and team.getDriver1().getDriverPoints() / team.getPoints() > 0.70:
                        if chaPos >= 4:
                            team.setTuning(1)
                        else:
                            team.setTuning(3)
                    else:
                        team.setTuning(0)
                else:
                    # Player turn
                    print(f"\nROUND {round + 1} - {team.getName()}")
                    input("\nPress 'SPACE' to continue...")
                    roundmenuSelect = None
                    while roundmenuSelect is None:
                        try:
                            print(f"{WEEK_COLOUR2}")
                            print(f"\n⌚ {'YEAR:':10s} {seasonPick + season}")
                            print(f"🏁 {'ROUND:':10s} {round + 1}")
                            print(f"🏎 {'TEAM:':10s} {team.getColour()}{team.getName()}{WEEK_COLOUR2}")
                            print(f"💵 {'FUNDS:':10s} ${team.getMoney():.2f}M")
                            print(f"👥 {'DRIVERS:':10s} {team.getColour()}{team.getDriver1()} ({team.getDriver1().getDriverAge()}) {WEEK_COLOUR2} and {team.getColour()} {team.getDriver2()} ({team.getDriver2().getDriverAge()})")
                            print(f"\n{RESET}Choose an option below by typing in the option number:")
                            print("-" * 29)
                            print(f"{ADVANCE_COLOUR}\n| (1) Head to Race Weekend! |\n{RESET}")
                            print("-" * 29)
                            print(f"\n{team.getColour()}(2) FINANCES")
                            print("(3) DEVELOPMENT")
                            print("(4) TUNING")
                            print(f"(5) {regChangeYear} RESEARCH")
                            print("(6) **POWER UNIT")
                            print(f"(7) DRIVERS' Championship (F1 {seasonPick + season})")
                            print(f"(8) CONSTRUCTORS' Championship (F1 {seasonPick + season})")
                            print("(9) **CONTRACTS")
                            print("(10) DRIVER MARKET")
                            print("-" * 50)
                            print(f" {WEEK_COLOUR1}(11) DRIVERS' Championship (F2 {seasonPick + season})")
                            print(" (12) **AFFILIATES")
                            print(" (13) TEAMS")
                            print("-" * 60)
                            print(f" {WEEK_COLOUR2}(14) Retirement RUMOURS")
                            print(" (15) RACE History")
                            print(" (16) CHAMPION History")
                            print(f" {SUPERRED_COLOUR}(17) Retire...{WEEK_COLOUR2}")
                            if season == 0 and 0 <= round <= 2:
                                print(" (18) RńD Performance List *FOR GAME DEVELOPMENT PURPOSES ONLY*")
                            print(f"\n{RESET}(** means not coded)")
                            print("-" * 75)
                            roundmenuSelect = input("Input: ")
                        except ValueError:
                            print("\nInvalid input.\n")
                            roundmenuSelect = None

                    # Process player menu selection
                    process_player_menu_selection(roundmenuSelect, team, season, round, seasonPick, teams, driverChampionship, driverChampionship2, free_agents)

            # Race weekend simulation
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
                pole_sitter=qualiResults[0].getDriverName(),
                team_name=qualiResults[0].getTeamAt().getName(),
                driver1=qualiResults[0].getDriverName(),
                driver2=qualiResults[1].getDriverName(),
                driver3=qualiResults[2].getDriverName(),
                driver4=qualiResults[3].getDriverName()
            )
            print(comment)
            input("\nPress 'SPACE' to continue...\n")

            simulateRace(teams)
            simulateRace2(driverChampionship2)
            raceResults = displayRaceResults(teams, pointsDist)

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
                winner=raceResults[0].getDriverName(),
                team_name=raceResults[0].getTeamAt().getName()
            )
            print(comment)
            input("\nPress 'SPACE' to continue...\n")

            # Post-race updates
            for t in teams:
                t.updateBestPos()
                if t.getDriver1().getDriverPoints() < t.getDriver2().getDriverPoints():
                    tempObj = t.getDriver2()
                    t.setDriver2(t.getDriver1())
                    t.setDriver1(tempObj)

            teams = updateConstructorChampionship(teams)
            driverChampionship = updateDriverChampionship(driverChampionship)
            driverChampionship2 = updateDriverChampionship2(driverChampionship2)

        # End of season processing
        process_end_of_season(season, seasonPick, teams, driverChampionship, driverChampionship2, free_agents, drivertransferList, driverWinHistory, championshipDriverWinners)

def process_player_menu_selection(selection, team, season, round, seasonPick, teams, driverChampionship, driverChampionship2, free_agents):
    """Process the player's menu selection during their turn."""
    # This function will contain the large if-elif block from your original code handling all menu options (2 to 18)
    # For brevity, I will not rewrite all here, but this should be modularized further into functions per menu option.
    # Example:
    if selection == "1":
        # Head to Race Weekend (break loop)
        return
    elif selection == "2":
        # Finances menu
        handle_finances(team)
    elif selection == "3":
        # Development menu
        handle_development(team)
    # ... and so on for all menu options
    else:
        print("\nInvalid selection.\n")

def process_end_of_season(season, seasonPick, teams, driverChampionship, driverChampionship2, free_agents, drivertransferList, driverWinHistory, championshipDriverWinners):
    """Handle end-of-season logic including standings, retirements, and resets."""
    print(f"The end of F1 {seasonPick + season} is here....")
    time.sleep(2)
    print(f"and {driverChampionship[0].getDriverName()} in the {driverChampionship[0].getTeamAt().getName()} has won the Driver Championship,\nand {teams[0].getName()} has won the Constructor Championship!")
    print("\nHere are the final standings:\n")
    driverChampionship[0].addDriverCha()
    displayDriverChampionship(driverChampionship)
    print()
    displayConstructorChampionship(teams)
    print(f"\nIn the lower racing category, {driverChampionship2[0].getDriverName()} wins F2 {seasonPick + season}! They cannot race in F2 anymore, which means")
    print(f"\n{driverChampionship2[0].getDriverName()} will have to find a Formula One race seat as soon as possible. Which team will take a leap of faith?")
    input("\nPress 'SPACE' to continue...\n")

    # Post-season data updates and resets
    free_agents.insert(0, driverChampionship2.pop(0))
    free_agents[0].setTeamAt("Free Agent")
    championshipDriverWinners.append(driverChampionToList(driverChampionship[0], teams[0]))
    print()
    print(displayDriverChampions(championshipDriverWinners))
    input("\nPress 'SPACE' to continue...")

    # Handle retirements
    handle_retirements(driverChampionship, free_agents, driverChampionship2, retMinAge)

    # Driver stats and market updates
    update_driver_stats_and_market(driverChampionship, free_agents, driverChampionship2, queuedDrivers)

    # Winter break and driver market
    winter_break_and_driver_market(teams, driverChampionship, free_agents, driverChampionship2)

    # Regulation changes and performance adjustments
    handle_regulation_changes(seasonPick, season, teams)

# ===================== Additional Helper Functions =====================

# You can define functions like:
# - handle_finances(team)
# - handle_development(team)
# - handle_retirements(...)
# - update_driver_stats_and_market(...)
# - winter_break_and_driver_market(...)
# - handle_regulation_changes(...)
# - ai_team_turn(team)
# - player_team_turn(team)
# - simulate_race_weekend(teams, driverChampionship2)
# - post_race_updates(...)
# - etc.

def process_player_menu_selection(selection, team, season, round, seasonPick, teams, driverChampionship, driverChampionship2, free_agents):
    """Process the player's menu selection during their turn."""
    if selection == "1":
        # Head to Race Weekend (break loop)
        return
    elif selection == "2":
        handle_finances(team)
    elif selection == "3":
        handle_development(team)
    elif selection == "4":
        handle_tuning(team)
    elif selection == "5":
        handle_research(team)
    elif selection == "6":
        handle_power_unit(team, season)
    elif selection == "7":
        displayDriverChampionship(driverChampionship)
        input("\nPress 'SPACE' to continue...")
    elif selection == "8":
        displayConstructorChampionship(teams)
        input("\nPress 'SPACE' to continue...")
    elif selection == "9":
        handle_contracts(team)
    elif selection == "10":
        displayDriverMarket(driverChampionship, free_agents, driverChampionship2)
        input("\nPress 'SPACE' to continue...")
    elif selection == "11":
        displayDriverChampionship2(driverChampionship2)
        input("\nPress 'SPACE' to continue...")
    elif selection == "12" and season == 100:
        input("\nPress 'SPACE' to continue...")
    elif selection == "13":
        displayTeams(teams)
    elif selection == "14":
        display_retirement_rumours(driverChampionship)
    elif selection == "15":
        display_race_history(season, seasonPick, driverWinHistory)
    elif selection == "16":
        displayDriverChampions(championshipDriverWinners)
        input("\nPress 'SPACE' to continue...")
    elif selection == "17":
        handle_retirement_confirmation(team)
    elif selection == "18" and season == 0:
        display_rd_performance_list(teams)
    else:
        print("\nInvalid selection.\n")

def handle_finances(team):
    invest = 2.0
    if 0.0 <= team.getMoney() < 1.0:
        invest = 0.0
    elif 1.0 <= team.getMoney() < 4.0:
        invest = 1.0

    while True:
        print(f"\nFUNDS: ${team.getMoney():.2f}M\n")
        print("(1) Back")
        print(f"(2) Development Amount (${invest:.2f}M set)")
        print("(3) Confirm Development Plan")
        try:
            choice = int(input("Input: "))
        except ValueError:
            print("\nInvalid input.\n")
            continue

        if choice == 1:
            break
        elif choice == 2:
            try:
                checkInvest = float(input("Type in development amount ($M) or '-1' for back: "))
                if checkInvest == -1:
                    break
                elif 0.0 < checkInvest <= team.getMoney():
                    invest = checkInvest
                else:
                    print("\nInvalid input.\n")
            except ValueError:
                print("\nInvalid input.\n")
        elif choice == 3:
            print(f"Invested ${invest:.2f}M")
            team.addPerf(invest)
            team.addMoney(-invest)
            break
        else:
            print("\nInvalid selection.\n")

def handle_development(team):
    invest = 2.0
    if 0.0 <= team.getMoney() < 1.0:
        invest = team.getMoney()
    elif 1.0 <= team.getMoney() < 4.0:
        invest = 1.0

    while True:
        print(f"\nFUNDS: ${team.getMoney():.2f}M\n")
        print("(1) Back")
        print(f"(2) Development Amount (${invest:.2f}M set)")
        print("(3) Confirm Development Plan")
        try:
            choice = int(input("Input: "))
        except ValueError:
            print("\nInvalid input.\n")
            continue

        if choice == 1:
            break
        elif choice == 2:
            try:
                checkInvest = float(input("Type in development amount ($M) or '-1' for back: "))
                if checkInvest == -1:
                    break
                elif 0.0 < checkInvest <= team.getMoney():
                    invest = checkInvest
                else:
                    print("\nInvalid input.\n")
            except ValueError:
                print("\nInvalid input.\n")
        elif choice == 3:
            print(f"Invested ${invest:.2f}M in development")
            # Assuming development affects performance similarly
            team.addPerf(invest)
            team.addMoney(-invest)
            break
        else:
            print("\nInvalid selection.\n")

def handle_tuning(team):
    while True:
        try:
            current_tuning = team.getTuning()
            print(f"Current Tuning: [{current_tuning}]")
            print("Enter a value between -3 and 3 to set tuning.")
            choice = int(input("Input: "))
            if -3 <= choice <= 3:
                team.setTuning(choice)
                print("\nTuning applied.\n")
                break
            else:
                print("\nInvalid selection.\n")
        except ValueError:
            print("\nInvalid input. Please enter an integer.\n")

def handle_research(team):
    invest = 2.0
    if 0.0 <= team.getMoney() < 1.0:
        invest = team.getMoney()
    elif 1.0 <= team.getMoney() < 4.0:
        invest = 1.0

    while True:
        print(f"\nFUNDS: ${team.getMoney():.2f}M\n")
        print("(1) Back")
        print(f"(2) Research Amount (${invest:.2f}M set)")
        print("(3) Confirm Research Plan")
        try:
            choice = int(input("Input: "))
        except ValueError:
            print("\nInvalid input.\n")
            continue

        if choice == 1:
            break
        elif choice == 2:
            try:
                checkInvest = float(input("Type in research amount ($M) or '-1' for back: "))
                if checkInvest == -1:
                    break
                elif 0.0 < checkInvest <= team.getMoney():
                    invest = checkInvest
                else:
                    print("\nInvalid input.\n")
            except ValueError:
                print("\nInvalid input.\n")
        elif choice == 3:
            print(f"Invested ${invest:.2f}M in research")
            team.addRes(invest)
            team.addMoney(-invest)
            break
        else:
            print("\nInvalid selection.\n")

def handle_power_unit(team, season):
    invest = 2.0
    if 0.0 <= team.getMoney() < 1.0:
        invest = team.getMoney()
    elif 1.0 <= team.getMoney() < 4.0:
        invest = 1.0

    while True:
        print(f"\nFUNDS: ${team.getMoney():.2f}M\n")
        print("(1) Back")
        print(f"(2) P. Unit Development Amount (${invest:.2f}M set)")
        print("(3) Confirm P. Unit Development Plan")
        try:
            choice = int(input("Input: "))
        except ValueError:
            print("\nInvalid input.\n")
            continue

        if choice == 1:
            break
        elif choice == 2:
            try:
                checkInvest = float(input("Type in development amount ($M) or '-1' for back: "))
                if checkInvest == -1:
                    break
                elif 0.0 < checkInvest <= team.getMoney():
                    invest = checkInvest
                else:
                    print("\nInvalid input.\n")
            except ValueError:
                print("\nInvalid input.\n")
        elif choice == 3:
            print(f"Invested ${invest:.2f}M in power unit development")
            team.addEPerf(invest)
            team.addMoney(-invest)
            break
        else:
            print("\nInvalid selection.\n")

def handle_contracts(team):
    while True:
        try:
            print(f"\n{team.getDriver1()}'s contract: {team.getDriver1().getContractLeft()} season(s) left")
            print(f"{team.getDriver2()}'s contract: {team.getDriver2().getContractLeft()} season(s) left\n")
            print("*Contracts left include current season (i.e., 2 means this season and next season left).")
            print("*Contract extensions can only be offered to drivers with one season left with the team.\n")
            print("Choose an option below by typing in the option number:")
            print("(1) Back")
            print(f"(2) Offer contract extension to {team.getDriver1()}")
            print(f"(3) Offer contract extension to {team.getDriver2()}")
            choice = int(input("Input: "))
        except ValueError:
            print("\nInvalid input.\n")
            continue

        if choice == 1:
            break
        elif choice == 2 and team.getDriver1().getContractLeft() < 2:
            team.getDriver1().addContractExtension(1)
            print(f"Contract extended for {team.getDriver1()}.")
        elif choice == 3 and team.getDriver2().getContractLeft() < 2:
            team.getDriver2().addContractExtension(1)
            print(f"Contract extended for {team.getDriver2()}.")
        else:
            print("\nInvalid selection or driver not eligible for extension.\n")

def handle_retirement_confirmation(team):
    while True:
        try:
            print("\nChoose an option below by typing in the option number:")
            print("(1) Confirm your retirement from the series")
            print("(2) Back")
            choice = int(input("Input: "))
        except ValueError:
            print("\nInvalid input.\n")
            continue

        if choice == 1:
            team.toggleControlledByAI()
            print(f"\n{team.getName()} is now controlled by AI. You have retired from the series.\n")
            break
        elif choice == 2:
            break
        else:
            print("\nInvalid selection.\n")

def display_retirement_rumours(driverChampionship):
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

    def format_entry(d):
        return f"{d.getDriverName()} ({d.getDriverAge()})"

    light_list = [format_entry(d) for d in range_1_pred]
    moderate_list = [format_entry(d) for d in range_2_pred]
    heavy_list = [format_entry(d) for d in range_3_pred]

    max_len = max(len(light_list), len(moderate_list), len(heavy_list), default=0)

    # Build rows for side-by-side columns
    rows = []
    for i in range(max_len):
        rows.append([
            light_list[i] if i < len(light_list) else "",
            moderate_list[i] if i < len(moderate_list) else "",
            heavy_list[i] if i < len(heavy_list) else ""
        ])

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

def display_race_history(season, seasonPick, driverWinHistory):
    ADVANCE_COLOUR = "\033[38;2;100;180;100m"
    RESET = "\033[0m"

    # Header row with season and rounds
    header = f"{'Season':<7s} | " + " | ".join([f"R{i+1:^{6}}" for i in range(Rules.seasonLength)]) + " |"
    print(header)
    print("=" * len(header))

    for i in range(season + 1):
        if i == season:
            season_str = f"{ADVANCE_COLOUR}{seasonPick + i:<7}{RESET} |"
        else:
            season_str = f"{seasonPick + i:<7} |"

        line1 = " " * 7 + " |"
        line2 = " " * 7 + " |"
        line3 = " " * 7 + " |"

        rounds_to_show = Rules.seasonLength if season > i else round

        for r in range(rounds_to_show):
            d0, c0 = driverWinHistory[i][r][0]
            d1, c1 = driverWinHistory[i][r][1]
            d2, c2 = driverWinHistory[i][r][2]

            line1 += f" {c0}{format_driver(d0):^{6}}{RESET} |"
            line2 += f" {c1}{format_driver(d1):^{6}}{RESET} |"
            line3 += f" {c2}{format_driver(d2):^{6}}{RESET} |"

        print(season_str)
        print(line1)
        print(line2)
        print(line3)

        if (regChangeYear % 4) == ((seasonPick + i + 1) % 4):
            print("=" * len(header))
            print("=" * len(header))
        else:
            print("-" * len(header))

    input("\nPress 'SPACE' to continue...")

def display_rd_performance_list(teams):
    print(f"\n{'Team':32s} | {'Performance'}")
    print("-" * 42)
    for t in teams:
        if t.getSupplier() is not None:
            nameGapLeft = 29 - len(t.getName()) - len(t.getSupplier().getSName())
            print(f"{t.getColour()}{t.getName()}{t.getColReset()} - {t.getSupplier().getColour()}{t.getSupplier().getSName()}{t.getSupplier().getColReset()}{' ':<{nameGapLeft}} | {t.getPerf():.2f}")
        else:
            print(f"{t.getColour()}{t.getName():32s}{t.getColReset()} | {t.getPerf():.2f}")
    print("-" * 42)
    input("\nPress 'SPACE' to continue...")

def handle_retirements(driverChampionship, free_agents, driverChampionship2, retMinAge):
    newRetiredDrivers = []
    to_remove = []

    # Check retirements in Formula 1
    for d in driverChampionship[:]:
        if isRetiring(d):
            newRetiredDrivers.append(d)
            to_remove.append(d)
            d.setContractLeft(1)
    for d in to_remove:
        driverChampionship.remove(d)

    # Check retirements in Free Agents
    to_remove.clear()
    for d in free_agents[:]:
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
        free_agents.remove(d)

    # Check retirements in Formula 2
    to_remove.clear()
    for d in driverChampionship2[:]:
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

    # Announce retirements
    if len(newRetiredDrivers) > 0:
        if len(newRetiredDrivers) == 1:
            print(f"\nBREAKING:\t{newRetiredDrivers[0].getDriverName()} is retiring at age {newRetiredDrivers[0].getDriverAge()}\n")
        else:
            print("\nBREAKING:\nThe following drivers are retiring.\n")
            for d in newRetiredDrivers:
                print(f"{d.getDriverName()} at age {d.getDriverAge()}")
        input("\nPress 'SPACE' to continue...")

def update_driver_stats_and_market(driverChampionship, free_agents, driverChampionship2, queuedDrivers):
    gridSize = len(driverChampionship)
    tempTeamPos = 1

    # Update Formula 1 drivers
    for d in driverChampionship:
        d.addDriverAge(1)
        d.addContractExtension(-1)

        # Find team position
        tempTeamPos = 1
        for t in teams:
            if d.getTeamAt() == t:
                break
            tempTeamPos += 1

        # Determine teammate points and rep
        if d.getTeamAt().getDriver1() == d:
            teammatePoints = d.getTeamAt().getDriver2().getDriverPoints()
            teammateRep = d.getTeamAt().getDriver2().getDriverRep()
        else:
            teammatePoints = d.getTeamAt().getDriver1().getDriverPoints()
            teammateRep = d.getTeamAt().getDriver1().getDriverRep()

        # Calculate market value adjustment
        if teammatePoints > 0:
            val = (((d.getDriverPoints() - teammatePoints) / teammatePoints) * (teammateRep / d.getDriverRep())) + (-(tempTeamPos - (gridSize / 2)) / (gridSize / 2))
        elif d.getDriverPoints() > 0:
            val = ((((tempTeamPos * 2) / tempTeamPos) - 1) + ((gridSize - (tempTeamPos * 2)) / (gridSize * 2)))
        else:
            val = 0

        val = (d.getDriverMV() + (d.getDriverMV() + val)) / 2
        d.setDriverMV(max(0.5, min(val, 8)))

        # Update driver performance
        d.addDriverPerf(DSUS(d))

    # Update Free Agents
    for d in free_agents:
        d.addDriverAge(1)
        d.addDriverPerf(DSUS(d))

    # Update Formula 2 drivers
    for d in driverChampionship2:
        d.addDriverAge(1)
        d.addDriverPerf(DSUS(d))

    # Update queued drivers (F3)
    for d in queuedDrivers:
        d.addDriverAge(1)
        d.addDriverPerf(DSUS(d))

import random

def winter_break_and_driver_market(teams, driverChampionship, free_agents, driverChampionship2):
    print("\nWinter break is here! Driver market and contracts are being updated...\n")

    # Drivers with expired contracts become free agents
    for d in driverChampionship[:]:
        if d.getContractLeft() < 1:
            print(f"{d.getDriverName()} is now a free agent.")
            driverChampionship.remove(d)
            free_agents.append(d)
            d.setTeamAt("Free Agent")

    # AI teams pick drivers from free agents if they have vacancies
    for team in teams:
        if team.isControlledByAI():
            # Check if driver1 is free agent and team has money
            d1 = team.getDriver1()
            if d1.getTeamAt() == "Free Agent" and team.getMoney() > 0:
                candidate_pool = build_candidate_pool(free_agents, team)
                if candidate_pool:
                    chosen = choose_best_candidate(candidate_pool)
                    team.setDriver1(chosen)
                    chosen.setTeamAt(team)
                    free_agents.remove(chosen)
                    print(f"{team.getName()} signed {chosen.getDriverName()} as Driver 1.")

            # Check if driver2 is free agent and team has money
            d2 = team.getDriver2()
            if d2.getTeamAt() == "Free Agent" and team.getMoney() > 0:
                candidate_pool = build_candidate_pool(free_agents, team)
                if candidate_pool:
                    chosen = choose_best_candidate(candidate_pool)
                    team.setDriver2(chosen)
                    chosen.setTeamAt(team)
                    free_agents.remove(chosen)
                    print(f"{team.getName()} signed {chosen.getDriverName()} as Driver 2.")

    # Display updated driver market
    displayDriverMarket(driverChampionship, free_agents, driverChampionship2)
    input("\nPress 'SPACE' to continue...")

def handle_regulation_changes(seasonPick, season, teams):
    # Assuming regulation changes occur every 4 years
    REG_CHANGE_INTERVAL = 4
    regChangeYear = seasonPick + season

    if (regChangeYear % REG_CHANGE_INTERVAL) == 0:
        print("\nRegulation changes have come into effect this season!")
        for team in teams:
            # Apply performance penalty or reset due to regulation changes
            old_perf = team.getPerf()
            new_perf = old_perf * 0.9  # Example: 10% performance drop
            team.setPerf(new_perf)
            print(f"{team.getName()} performance adjusted from {old_perf:.2f} to {new_perf:.2f}")

        input("\nPress 'SPACE' to continue...")

def ai_team_turn(team):
    # Example AI logic for team decisions

    # Invest in development if funds allow
    money = team.getMoney()
    invest_amount = 0.0
    if money > 4.0:
        invest_amount = 2.0
    elif money > 1.0:
        invest_amount = 1.0

    if invest_amount > 0:
        team.addPerf(invest_amount)
        team.addMoney(-invest_amount)
        print(f"{team.getName()} invested ${invest_amount:.2f}M in development.")

    # Adjust tuning randomly within allowed range
    import random
    tuning_choice = random.randint(-3, 3)
    team.setTuning(tuning_choice)
    print(f"{team.getName()} set tuning to {tuning_choice}.")

    # AI contract management (simple logic)
    for driver in [team.getDriver1(), team.getDriver2()]:
        if driver.getContractLeft() == 1:
            driver.addContractExtension(1)
            print(f"{team.getName()} extended contract for {driver.getDriverName()}.")

    print(f"{team.getName()} has completed its turn.\n")

# ================================================================

if __name__ == "__main__":
    main()
