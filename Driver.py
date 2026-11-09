class driver():
    #Constructor
    def __init__(self, name, age, perf, rep, dChamp, teamAt, contractLeft, MV, salary):
        self.driverName = name
        #self.driverAbr = abr
        self.driverAge = age
        self.driverPerf = perf
        self.driverRep = rep
        self.driverPoints = 0
        self.seasonRWins = 0
        self.driverChampionships = dChamp
        self.teamAt = teamAt
        self.contractLeft = contractLeft
        self.driverMV = MV
        self.driverSalary = salary
        self.qualTime = None
        self.qualPos = None
        self.raceTime = None
        self.racePos = None
        self.bestPos = None
        self.contractOffers = []

    #Getters
    def getDriverName (self):
        return self.driverName
    #def getDriverAbr (self):
        #return self.driverAbr
    def getDriverAge (self):
        return self.driverAge
    def getDriverPerf (self):
        return self.driverPerf
    def getDriverRep (self):
        return self.driverRep
    def getDriverPoints (self):
        return self.driverPoints
    def getSeasonRWins (self):
        if self.seasonRWins is None:
            return 0
        return self.seasonRWins
    def getDriverCha (self):
        return self.driverChampionships
    def getTeamAt (self):
        return self.teamAt
    def getContractLeft (self):
        return self.contractLeft
    def getDriverMV (self):
        return self.driverMV
    def getDriverSalary (self):
        return self.driverSalary
    def getQualTime (self):
        return self.qualTime
    def getQualPos (self):
        return self.qualPos
    def getRaceTime (self):
        return self.raceTime
    def getRacePos (self):
        return self.racePos
    def getBestPos (self):
        return self.bestPos

    #Setters
    def setDriverName(self, newName):
        self.driverName = newName
    def setDriverAge(self, newAge):
        self.driverAge = newAge
    def addDriverAge(self, add):
        self.driverAge += add
    def setDriverPerf(self, newPerf):
        self.driverPerf = newPerf
    def addDriverPerf(self, addPerf):
        self.driverPerf += addPerf
    def setDriverRep(self, newRep):
        self.driverRep = newRep
    def addDriverRep(self, addRep):
        self.driverRep += addRep
    def addDriverPoints (self, addPts):
        self.driverPoints += addPts
    def resetDriverPoints (self):
        self.driverPoints = 0
    def addSeasonRWins(self, addS):
        self.seasonRWins += addS
    def resetSeasonRWins(self):
        self.seasonRWins = 0
    def addDriverCha (self):
        self.driverChampionships += 1
    def setTeamAt (self, newTeam):
        self.teamAt = newTeam
    def setContractLeft(self, newLeft):
        self.contractLeft = newLeft
    def addContractExtension(self, add):
        self.contractLeft += add
    def setDriverMV(self, newMV):
        self.driverMV = newMV
    def addDriverMV(self, newMV):
        self.driverMV += newMV
    def setDriverSalary(self, newSalary):
        self.driverSalary = newSalary
    def setQualTime (self, newTime):
        self.qualTime = newTime
    def setQualPos (self, newPos):
        self.qualPos = newPos
    def setRaceTime (self, newTime):
        self.raceTime = newTime
    def setRacePos (self, newPos):
        self.racePos = newPos
    def setBestPos (self, newPos):
        self.bestPos = newPos

    def __str__ (self):
        return (f"{self.driverName}")
