import random, re
import unicodedata

baseline_lap = 75.000
RESET = "\033[0m"

def lapSim (driver_perf, team_perf, max_perf, min_perf, session, error_multiplier):
    '''
    Simulates one lap for the given driver
    and returns the variable lap_time.
    '''

    if session == 1:  # Qual
        field_diff = 180
    else:
        field_diff = 150

    perf_diff = max_perf - min_perf
    a_temp = (max_perf - field_diff) - min_perf

    if perf_diff > field_diff:
        w_perf = team_perf + (a_temp * ((max_perf - team_perf) / perf_diff))
    else:
        w_perf = team_perf

    if session == 1: # Qual
        lap_time = baseline_lap - (
            (driver_perf / 25) +
            (w_perf / 40)
        ) + random.gauss(0, 0.12) * error_multiplier
    else: # Race
        lap_time = baseline_lap - (
                (driver_perf / 5) +
                (w_perf / 20)
        ) + random.gauss(0, 0.12) * error_multiplier

    return lap_time

def simulateQual (arr): #Must accept list of team objects
    perf_list = []

    for i in range(len(arr)):
        perf_list.append(arr[i].getPerf())

    perf_list.sort(reverse=True)
    max_perf = perf_list[0]
    min_perf = perf_list[-1]

    for x in arr:
        D1 = x.getDriver1()
        D2 = x.getDriver2()
        if x.getSupStage() > 0 and x.getSupplier() is not None:
            t_perf = (x.getPerf()*2 + x.getSupplier().getPerf()) / 3
        else:
            t_perf = x.getPerf()

        D1_w_perf = D1.getDriverPerf() + (x.getTuning() * 1.0)
        D2_w_perf = D2.getDriverPerf() - (x.getTuning() * 1.0)

        D1.setQualTime(lapSim(D1_w_perf, t_perf, max_perf, min_perf, 1, 2.5))
        D2.setQualTime(lapSim(D2_w_perf, t_perf, max_perf, min_perf, 1, 2.5))

def displayQualResults(arr):

    RESET = "\033[0m"

    drivers = []

    for team in arr:
        drivers.append(team.getDriver1())
        drivers.append(team.getDriver2())

    results = sorted(drivers, key=lambda d: d.getQualTime())

    leader_time = results[0].getQualTime()

    rows = []

    for pos, d in enumerate(results, start=1):

        colour = d.getTeamAt().getColour()

        # ▇

        driver = format_driver_wBar(
            d.getDriverName(),
            colour,
            d.getDriverCha()
        )

        team = format_team(d.getTeamAt(), True)

        if pos == 1:
            gap = "LEADER"
        else:
            gap = f"+{d.getQualTime() - leader_time:.3f}s"

        rows.append([
            pos,
            driver,
            team,
            gap
        ])

        d.setQualPos(pos)

    headers = ["POS","DRIVER","CAR","GAP"]
    widths  = [4,28,34,12]
    aligns  = ["center","left","left","right"]

    print()
    print_table(headers, rows, widths, aligns)
    print()

    return results

def simulateRace (arr): #Must accept list of team objects
    perf_list = []

    for i in range(len(arr)):
        perf_list.append(arr[i].getPerf())

    perf_list.sort(reverse=True)
    max_perf = perf_list[0]
    min_perf = perf_list[-1]

    for x in arr:


        D1 = x.getDriver1()
        D2 = x.getDriver2()
        if x.getSupStage() > 0 and x.getSupplier() is not None:
            t_perf = (x.getPerf()*2 + x.getSupplier().getPerf()) / 3
        else:
            t_perf = x.getPerf()

        D1.setRaceTime(0.000)
        D2.setRaceTime(0.000)

        D1_w_perf = D1.getDriverPerf() + (x.getTuning() * 4.0)
        D2_w_perf = D2.getDriverPerf() - (x.getTuning() * 4.0)

        for _ in range(80):
            D1.setRaceTime(lapSim(D1_w_perf, t_perf, max_perf, min_perf, 2, 25.0))
            D2.setRaceTime(lapSim(D2_w_perf, t_perf, max_perf, min_perf, 2, 25.0))

        D1.setRaceTime((D1.getRaceTime() + (1.0 * D1.getQualPos())) * 3.0) # Grid Penalty & Split Booster
        D2.setRaceTime((D2.getRaceTime() + (1.0 * D2.getQualPos())) * 3.0) # Grid Penalty & Split Booster

def simulateRace2 (arr): #Must accept list of driver objects
    for x in arr:
        x.setRaceTime(0.000)
        for lap in range (30):
            x.setRaceTime(x.getRaceTime() + (baseline_lap - ((x.getDriverPerf() / 100) + (random.random() * 1.2))))

    auxiliary = []
    for x in arr:
        auxiliary.append(x)
    results = sorted(auxiliary, key=lambda free_agent: free_agent.getRaceTime())

    ptsDist = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
    pos = 1
    for d in results:
        d.setRacePos(pos)
        if d.getBestPos() == None: d.setBestPos(d.getRacePos())
        elif d.getRacePos() < d.getBestPos(): d.setBestPos(d.getRacePos())
        if pos <= 10:
            d.addDriverPoints(ptsDist[pos-1])
        newRep = ((2 - (pos / (len(arr) * 2)) * 1) * 1 + d.getDriverRep() * 11) / 12
        d.setDriverRep(newRep)
        pos += 1

ANSI_PATTERN = re.compile(r'\x1b\[[0-9;]*m')

def visible_len(text):
    text = ANSI_PATTERN.sub('', str(text))

    width = 0
    for ch in text:
        if unicodedata.east_asian_width(ch) in ('F', 'W'):
            width += 2
        else:
            width += 1

    return width

def pad(text, width, align="left"):
    text = str(text)
    length = visible_len(text)

    if length >= width:
        return text

    padding = width - length

    if align == "left":
        return text + " " * padding
    elif align == "right":
        return " " * padding + text
    elif align == "center":
        left = padding // 2
        right = padding - left
        return " " * left + text + " " * right

def print_table(headers, rows, widths, aligns):

    # header
    header_line = " | ".join(
        pad(h, w, "center") for h, w in zip(headers, widths)
    )
    print(header_line)

    # separator
    total_width = sum(widths) + 3 * (len(widths)-1)
    print("-" * total_width)

    # rows
    for row in rows:
        line = " | ".join(
            pad(col, w, a) for col, w, a in zip(row, widths, aligns)
        )
        print(line)

def format_driver(name, colour, championships):

    parts = name.split()
    first = parts[0]
    try:
        last = f"{parts[1].upper()} {parts[2].upper()}"
    except:
        last = parts[1].upper()

    text = f"{last}"

    if championships > 0:
        text += f" 🏆x{championships}"

    return f"{first} {colour}{text}{RESET}"

def format_driver_wBar(name, colour, championships):

    parts = name.split()
    first = parts[0]
    try:
        last = f"{parts[1].upper()} {parts[2].upper()}"
    except:
        last = parts[1].upper()

    text = f"{last}"

    if championships > 0:
        text += f" 🏆x{championships}"
    # ▇
    return f"{colour} |{RESET} {first} {colour}{text}{RESET}"

def format_driver_basic(name, colour):

    parts = name.split()
    first = parts[0]
    try:
        last = f"{parts[1].upper()} {parts[2].upper()}"
    except:
        last = parts[1].upper()

    text = f"{last}"

    return f"{first} {colour}{text}{RESET}"

def format_champion(name):

    parts = name.split()
    first = parts[0]
    last = parts[-1].upper()

    text = f"{last}"

    return f"{first} {text}"

def format_team(team, aff):
    try:
        if aff:
            try:
                return (
                    f"{team.getColour()}{team.getName()}{team.getColReset()}-"
                    f"{team.getSupplier().getColour()}{team.getSupplier().getName()}{team.getSupplier().getColReset()}"
                )
            except:
                return f"{team.getColour()}{team.getName()}{team.getColReset()}"
        else:
            return f"{team.getColour()}{team.getName()}{team.getColReset()}"
    except:
        if team in ["Free Agent","F2 Champion"]:
            colour = "\033[1;38;2;200;200;255;49m"  # Default colour = White + tinted blue
        else:
            colour = "\033[1;38;2;255;255;255;49m"  # Default colour = White
        return f"{colour}{team}{RESET}"

def driver_abbr(name):
    return name.split()[-1][:3].upper()

def team_string(team):
    try:
        return f"{team.getName()}-{team.getSupplier().getName()}"
    except:
        return team.getName()

def pos_symbol(pos):
    if pos == 1: return "🥇"
    if pos == 2: return "🥈"
    if pos == 3: return "🥉"
    return pos

def displayRaceResults(arr, ptsDist, fixed_rw=None):

    GREEN = "\033[38;2;0;230;0m"
    RED = "\033[38;2;255;0;0m"
    GREY = "\033[38;2;50;50;50m"
    RESET = "\033[0m"

    drivers = []
    rw = None

    for team in arr:
        if team.getDriver1() == fixed_rw:
            rw = team.getDriver1()
        else:
            drivers.append(team.getDriver1())
        if team.getDriver2() == fixed_rw:
            rw = team.getDriver2()
        else:
            drivers.append(team.getDriver2())

    results = sorted(drivers, key=lambda d: d.getRaceTime())
    if rw is not None:
        results.insert(0, fixed_rw)
        if results[1].getRaceTime() < results[0].getRaceTime():
            results[0].setRaceTime(results[1].getRaceTime() - (random.random() * 7 + 1))

    leader_time = results[0].getRaceTime()

    rows = []

    for pos, d in enumerate(results, start=1):

        gl_val = d.getQualPos() - pos

        if gl_val > 0:
            gl = f"{GREEN}⬆{RESET}{gl_val}"
        elif gl_val < 0:
            gl = f"{RED}⬇{RESET}{-gl_val}"
        else:
            gl = f"{GREY}⬆{RESET}0"

        colour = d.getTeamAt().getColour()

        driver = format_driver_wBar(
            d.getDriverName(),
            colour,
            d.getDriverCha()
        )

        team = format_team(d.getTeamAt(), True)

        if pos == 1:
            gap = "LEADER"
        else:
            gap = f"+{d.getRaceTime() - leader_time:.3f}s"

        rows.append([
            pos_symbol(pos),
            driver,
            gl,
            team,
            gap
        ])

        # updates
        d.setRacePos(pos)

        if d.getBestPos() is None or pos < d.getBestPos():
            d.setBestPos(pos)

        if pos <= len(ptsDist):
            d.addDriverPoints(ptsDist[pos-1])

        d.getTeamAt().addMoney(1.95 - (0.025 * pos))
        # newRep = ((5.2 - (pos/(len(arr)))*3)*1 + d.getDriverRep()*17) / 18
        raceRep = 5 - (pos/(len(arr)*2))*3.2
        newRep = (raceRep + d.getDriverRep()*11) / 12
        d.setDriverRep(newRep)

    for team in arr:
        team.updatePoints()

    headers = ["POS","DRIVER","G/L","CAR","GAP"]
    widths  = [4,28,6,34,12]
    aligns  = ["center","left","center","left","right"]

    print()
    print_table(headers, rows, widths, aligns)
    print()

    return results

def updateDriverChampionship (arr): #Must accept list of DRIVER objects
    auxiliary = []
    for x in arr:
        auxiliary.append(x)

    results = sorted(auxiliary, key=lambda driver: (-driver.getDriverPoints(), driver.getBestPos()))
    return results

def updateDriverChampionship2 (arr): #Must accept list of DRIVER objects
    auxiliary = []
    for x in arr:
        auxiliary.append(x)

    results = sorted(auxiliary, key=lambda free_agent: (-free_agent.getDriverPoints(), free_agent.getBestPos()))
    return results

def displayDriverChampionship(arr):
    '''
    F1 standings
    '''

    rows = []

    for pos, d in enumerate(arr, start=1):

        try:
            colour = d.getTeamAt().getColour()
        except:
            colour = "\033[1;38;2;255;255;255;49m" # Default colour = White

        driver = format_driver_wBar(
            d.getDriverName(),
            colour,
            d.getDriverCha()
        )

        team = format_team(d.getTeamAt(), True)

        pts = f"{d.getDriverPoints():.0f}"

        rows.append([
            pos_symbol(pos),
            driver,
            team,
            pts
        ])

    headers = ["POS","DRIVER","CAR","PTS"]
    widths  = [4,28,34,4]
    aligns  = ["center","left","left","right"]

    print()
    print_table(headers, rows, widths, aligns)
    print()

def displayDriverChampionship2(arr):
    '''
    F2 standings
    '''

    rows = []

    for pos, d in enumerate(arr, start=1):

        try:
            colour = d.getTeamAt().getColour()
        except:
            colour = "\033[1;38;2;255;255;255;49m" # Default colour = White

        driver = format_driver_wBar(
            d.getDriverName(),
            colour,
            d.getDriverCha()
        )

        if d.getTeamAt() in ["Formula 2"]:
            team = "N/A"
        else:
            team = format_team(d.getTeamAt(), False)

        pts = f"{d.getDriverPoints():.0f}"

        rows.append([
            pos_symbol(pos),
            driver,
            team,
            pts
        ])

    headers = ["POS","DRIVER","AFFILIATION","PTS"]
    widths  = [4,28,15,6]
    aligns  = ["center","left","center","right"]

    print()
    print_table(headers, rows, widths, aligns)
    print()

def updateConstructorChampionship (arr): #Must accept list of TEAM objects
    auxiliary = []
    for x in arr:
        auxiliary.append(x)

    results = sorted(auxiliary, key=lambda team: (-team.getPoints(), team.getBestPos()))
    return results

def displayConstructorChampionship(arr):

    rows = []

    for pos, t in enumerate(arr, start=1):

        team = format_team(t, True)
        pts = f"{t.getPoints():.0f}"

        rows.append([
            pos_symbol(pos),
            team,
            pts
        ])

    headers = ["POS", "TEAM", "PTS"]
    widths  = [4,28,6]
    aligns  = ["center","left","right"]

    print()
    print_table(headers, rows, widths, aligns)
    print()

def displayDriverMarket(arr, arr2, arr3, boolRep):

    rows = []

    # contracted drivers
    i = 1
    for d in arr:

        try:
            colour = d.getTeamAt().getColour()
        except:
            colour = "\033[1;38;2;255;255;255;49m"  # Default colour = White

        driver = format_driver_wBar(
            d.getDriverName(),
            colour,
            d.getDriverCha()
        )

        team = format_team(d.getTeamAt(), True)

        if boolRep:
            rows.append([
                i,
                driver,
                d.getDriverAge(),
                team,
                d.getContractLeft(),
                f"${d.getDriverSalary():.2f}M"
            ])
        else:
            rows.append([
                i,
                driver,
                d.getDriverAge(),
                team,
                d.getContractLeft(),
                f"${d.getDriverSalary():.2f}M",
                f"{d.getDriverRep():.2f}",
                f"{d.getDriverPerf()}"
            ])
        i += 1

    # free agents
    for d in arr2:

        try:
            colour = d.getTeamAt().getColour()
        except:
            colour = "\033[1;38;2;200;200;255;49m"  # Default colour = White (+tinted blue)

        driver = format_driver_wBar(
            d.getDriverName(),
            colour,
            d.getDriverCha()
        )

        if d.getTeamAt() in ["Free Agent","F2 Champion"]:
            team = f"{format_team(d.getTeamAt(), False)}"
        else:
            team = f"T&R for {format_team(d.getTeamAt(), False)}"

        if boolRep:
            rows.append([
                i,
                driver,
                d.getDriverAge(),
                team,
                "",
                f"${d.getDriverSalary():.2f}M"
            ])
        else:
            rows.append([
                i,
                driver,
                d.getDriverAge(),
                team,
                "",
                f"${d.getDriverSalary():.2f}M",
                f"{d.getDriverRep():.2f}",
                f"{d.getDriverPerf()}"
            ])
        i += 1

    # academy / juniors
    for d in arr3:

        try:
            colour = d.getTeamAt().getColour()
        except:
            colour = "\033[1;38;2;255;255;255;49m" # Default colour = White

        driver = format_driver_wBar(
            d.getDriverName(),
            colour,
            d.getDriverCha()
        )

        if d.getTeamAt() in ["Formula 2"]:
            team = "F2"
        else:
            team = f"F2 {format_team(d.getTeamAt(), False)} Junior"

        if boolRep:
            rows.append([
                i,
                driver,
                d.getDriverAge(),
                team,
                "",
                f"${d.getDriverSalary():.2f}M"
            ])
        else:
            rows.append([
                i,
                driver,
                d.getDriverAge(),
                team,
                "",
                f"${d.getDriverSalary():.2f}M",
                f"{d.getDriverRep():.2f}",
                f"{d.getDriverPerf()}"
            ])
        i += 1

    if boolRep:
        headers = ["i","DRIVER","AGE","TEAM / LABEL","CONTRACT","MARKET VALUE"]
        widths  = [4, 28, 5, 36, 10, 12]
        aligns  = ["left","left","center","left","center","right"]
    else:
        headers = ["i", "DRIVER", "AGE", "TEAM / LABEL", "CONTRACT", "MARKET VALUE", "REP", "PERF"]
        widths = [4, 28, 5, 36, 10, 12, 6, 6]
        aligns = ["left", "left", "center", "left", "center", "right", "right", "right"]

    print()
    print_table(headers, rows, widths, aligns)
    print()

def displayTeamMarket(arr):

    rows = []

    for pos, t in enumerate(arr, start=1):

        team = format_team(t, False)
        colour = t.getColour()
        pts = f"{t.getPoints():.0f}"
        if t.getSupplier() is not None:
            if t.getSupStage() == 1:
                supName = f"{format_team(t.getSupplier(), False)} Customer Team"
            elif t.getSupStage() == 2:
                supName = f"{format_team(t.getSupplier(), False)} Junior Team"
        else:
            supName = "N/A"
        drivers = ""
        try:
            driver1 = format_driver(
                t.getDriver1().getDriverName(),
                colour,
                t.getDriver1().getDriverCha()
            )
            drivers += driver1
        except:
            driver1 = None
        try:
            driver2 = format_driver(
                t.getDriver2().getDriverName(),
                colour,
                t.getDriver2().getDriverCha()
            )
            if driver1 != None:
                drivers += ", "
            drivers += driver2
        except:
            driver2 = ""

        rows.append([
            pos_symbol(pos),
            team,
            pts,
            supName,
            f" {drivers}"
        ])

    headers = ["i", "TEAM", "PTS", "AFFILIATION STATUS", "DRIVERS"]
    widths  = [4,16,6,25,50]
    aligns  = ["center","left","right","left","left"]

    print()
    print_table(headers, rows, widths, aligns)
    print()

def displayDriverMarket2 (arr2, arr3):
    print(f"{"DRIVER":<25}{"AGE":<5}{"LABEL":<36}{"MARKET VALUE":<10}")
    print()
    for x in arr2:
        if x.getDriverCha() > 0:
            print(f"{x.getDriverName() + " 🏆x" + str(x.getDriverCha()):<24}{x.getDriverAge():<5}{x.getTeamAt():<36}${x.getDriverSalary():.2f}M")
        else:
            print(f"{x.getDriverName():<25}{x.getDriverAge():<5}{x.getTeamAt():<36}${x.getDriverSalary():.2f}M")
    for x in arr3:
        print(f"{x.getDriverName():<25}{x.getDriverAge():<5}{x.getTeamAt():<36}${x.getDriverSalary():.2f}M")

def driverChampionToList (obj, obj2): #Must accept DRIVER object
    return f"{format_champion(obj.getDriverName()):<20}{obj.getDriverAge():<7}{obj.getTeamAt().getColour()}{obj.getTeamAt().getName():<16}{RESET}{obj.getDriverPoints():<7.0f}🏆x{obj.getDriverCha():<10.0f}{obj2.getColour()}{obj2.getName():<12}{RESET}"

def displayDriverChampions (arr): #Must accept list of STRING items
    if len(arr) > 0:
        print(f"{"YEAR":<7}{"DRIVER":<20}{"AGE":<7}{"CAR":<16}{"PTS":<7}{"TROPHIES":<12}{"WINNING TEAM":<12}")
        print("\n...")
        year = 2010
        for l in arr:
            '''if year == 2014: print("-- NEW REG. ERA! --")
            if year == 2018: print("-- NEW REG. ERA! --")
            if year == 2022: print("-- NEW REG. ERA! --")
            #if year == yrPicked: print("-- NEW SEASON FORMAT! --")1
            if year == 2026: print("-- NEW REG. ERA! --")
            if year == 2030: print("-- NEW REG. ERA! --")
            if year == 2034: print("-- NEW REG. ERA! --")
            if year == 2038: print("-- NEW REG. ERA! --")
            if year == 2042: print("-- NEW REG. ERA! --")
            if year == 2046: print("-- NEW REG. ERA! --")
            if year == 2050: print("-- NEW REG. ERA! --")
            if year == 2054: print("-- NEW REG. ERA! --")
            if year == 2058: print("-- NEW REG. ERA! --")
            if year == 2062: print("-- NEW REG. ERA! --")
            if year == 2066: print("-- NEW REG. ERA! --")
            if year == 2070: print("-- NEW REG. ERA! --")'''
            print(f"{year:<7}{l}")
            year += 1