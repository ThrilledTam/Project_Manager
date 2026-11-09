import math

class team():
    #Constructors
    def __init__ (self, name, colour, money, cWins, perf, rel, sup, sta):
        self.controlledByAI = True
        self.name = name
        self.colour = colour
        self.colReset = "\033[0m"
        self.money = money
        self.points = 0
        self.championshipWins = cWins
        self.performance = perf
        self.adaptedPerf = perf
        self.reliability = rel
        self.tuning = 0
        self.perfRes = 0
        self.reliRes = 0
        self.supplier = sup
        self.supStage = sta
        self.driver1 = None
        self.driver2 = None
        self.bestPos = None
        self.nextDrivers = []
        self.affDrivers = []

    #Getters
    def isControlledByAI (self): return self.controlledByAI
    def getName (self): return self.name
    def getColour (self): return self.colour
    def getColReset (self): return self.colReset
    def getMoney (self): return self.money
    def getPoints (self): return self.points
    def getChampionshipWins (self): return self.championshipWins
    def getPerf (self): return self.performance
    def getAPerf(self): return self.adaptedPerf
    def getRel (self): return self.reliability
    def getRelDisplay(self): return f"{self.reliability*100:.2f}%"
    def getTuning (self): return self.tuning
    def getPerfRes (self): return self.perfRes
    def getReliRes (self): return self.reliRes
    def getSupplier (self): return self.supplier
    def getSupStage(self): return self.supStage
    def getDriver1 (self): return self.driver1
    def getDriver2 (self): return self.driver2
    def getBestPos (self): return self.bestPos
    def getNextDrivers(self):return self.nextDrivers
    def getAffDrivers (self): return self.affDrivers

    #Setters
    def toggleControlledByAI(self):
        if self.isControlledByAI() == True:
            self.controlledByAI = False
        else: self.controlledByAI = True
    def setName(self, newName): self.name = newName
    def setColour(self, col): self.colour = col
    def addMoney(self, addMoney): self.money += addMoney
    def updatePoints(self): self.points = self.driver1.getDriverPoints() + self.driver2.getDriverPoints()
    def resetPoints(self): self.points = 0
    def addChampionshipWin(self): self.championshipWins = 1

    def addPerf(self, investment):
        self.performance += ((400 / self.performance) ** 2.5) * (investment / 3)
        '''
        If PERF == 100  &  INV == 1.0:
            (15.588) * (0.5) = +7.794
            
        If PERF == 100  &  INV == 4.0:
            (15.588) * (2.0) = +31.177
        
        If PERF == 200  &  INV == 1.0:
            (2.756) * (0.5) = +1.378
        
        If PERF == 200  &  INV == 4.0:
            (2.756) * (2.0) = +5.511
            
        If PERF == 250  &  INV == 1.0:
            (1.577) * (0.5) = +0.789
        
        If PERF == 250  &  INV == 4.0:
            (1.577) * (0.5) = +3.155
        '''

        # self.performance += investment * 2.0 * (1 / (1 + self.performance / 300))   // OLD SYSTEM
    def setPerf(self, new): self.performance = new
    def setAPerf(self, new): self.adaptedPerf = new

    def addRel(self, investment):
        self.reliability += investment / 100

    def setTuning (self, new): self.tuning = new

    def addPerfRes(self, addRes): self.perfRes += addRes
    def addReliRes(self, addRes): self.reliRes += addRes
    def resetRes(self):
        self.perfRes = 0
        self.reliRes = 0

    def setSupplier(self, newSup): self.supplier = newSup
    def setSupStage(self, newSupStage): self.supStage = newSupStage

    def setDriver1(self, newDriver): self.driver1 = newDriver
    def setDriver2(self, newDriver): self.driver2 = newDriver

    def setBestPos(self, pos):  self.bestPos = pos
    def updateBestPos(self):
        if self.getDriver1().getBestPos() <= self.getDriver2().getBestPos():
            self.bestPos = self.getDriver1().getBestPos()
        else: self.bestPos = self.getDriver2().getBestPos()
    def addNextDrivers(self, driver): self.nextDrivers.append(driver)
    def addAffDrivers(self, driver): self.affDrivers.append(driver)