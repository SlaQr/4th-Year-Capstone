from CLASS.ship import Ship
from CLASS.gamemaster import GameMaster
from random import randrange
from CLASS.weapon import Weapon
from CLASS.organism import Organism
from CLASS.analysis import Analysis

from multiprocessing import Process
from threading import Thread as child

SIMULATION_PATH = "D:\SIM\SIM SMART CREW"

class GameThread:
    def __init__(self, gameMaster, count, startingNum, path, fence, detonation, launch):
        self.gm = gameMaster
        self.count = count
        self.startingNum = startingNum
        self.path = path
        self.fence = fence
        self.detonation = detonation
        self.launch = launch
        
    def go(self):
        for i in range(self.startingNum, self.startingNum + self.count):
            self.gm.newGame(self.fence, self.detonation, self.launch)
            #self.gm.gameOutcomes.append(self.gm.currentGameActions)
            #self.gm.currentGameActions = []
            self.gm.showGame("{}\{}.txt".format(self.path, i))

def bootstrap(fence, detonation, launch, SIMULATION_PATH, debug = False):
    reader = open("DATA\Ship.txt", "r")
    SHIP_TEXT = reader.readlines()
    
    reader = open("DATA\Line of Sight.txt", "r")
    SHIP_LOS_TEXT = reader.readlines()
    
    reader = open("DATA\Hatch.txt", "r")
    SHIP_HATCH_TEXT = reader.readlines()
    
    reader = open("DATA\Crew.txt", "r")
    CREW_TEXT = reader.readlines()
    
    reader = open("DATA\GT.txt", "r")
    GREEN_THING_TEXT = reader.readlines()
    
    reader = open("DATA\Weapon.txt", "r")
    WEAPON_TEXT = reader.readlines()
    
    reader = open("DATA\Weapon Locations.txt", "r")
    WEAPON_PLACEMENT = reader.readlines()
    
    reader = open("DATA\Effect Chits.txt", "r")
    EFFECTS = reader.readlines()
    
    shipFactory = Ship(SHIP_TEXT, SHIP_LOS_TEXT, SHIP_HATCH_TEXT, CREW_TEXT, GREEN_THING_TEXT, WEAPON_TEXT, WEAPON_PLACEMENT, EFFECTS)

    

    SIM_COUNT = 10
    if not debug:
        games = []
        
        ASYNC_SIMS = 10
        for i in range(1, ASYNC_SIMS * SIM_COUNT, SIM_COUNT):
            thr = GameThread(GameMaster(shipFactory), SIM_COUNT, i, SIMULATION_PATH, fence, detonation, launch)
            #thr.gm.debugger = open("D:\SIM\SIM SMART CREW\DEBUG {}.txt".format(i), "a")
            games.append(thr)
        
        threads = []
        for game in games:
            threads.append(child(target=game.go))
            
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
            
        #simulations = []
        #for game in games:
        #    simulations += game.gm.gameOutcomes
        
    else:
        gm = GameMaster(shipFactory)
        for i in range(0, SIM_COUNT):
            print("Running Game: {}".format(i))
            gm.newGame()
            gm.showGame("{}\Sim {}.txt".format(SIMULATION_PATH, i+1))
        print("Done")

#Python threads are unaware of alternate cores.
#giving each designated subset of probabilities a seperate process allows python to make full use of a multi-core processor
class CPUSaver:
    def __init__(self):
        self.processes = []
        self.ranprocesses = 0
    
    def append(self, fence, detonation, launch):
        self.ranprocesses += 1
        self.processes.append(Process(target=bootstrap, args=(fence, detonation, launch, "D:\SIM\{}_{}_{}".format(fence, detonation, launch), False)))
        if len(self.processes) >= 5:
            print("Running processes {} of 80".format(self.ranprocesses))
            for prcs in self.processes:
                prcs.start()
            for prcs in self.processes:
                prcs.join()
            self.processes = []
            

#generates permutations of the percentages (in steps of 25%) to:
        #use a fence
        #initiate ship detonation
        #launch an escaping ship
def generateSimulations(basePath = "D:\SIM"):
    import os
    e = CPUSaver()
    for fence in range(0, 125, 25):
        for detonation in range(25, 125, 25):
            print(fence, detonation)
            for launch in range(25, 125, 25):
                folderName = "{}_{}_{}".format(fence, detonation, launch)
                SIMULATION_PATH = "{}\{}\\".format(basePath, folderName)
                directory = os.path.dirname(SIMULATION_PATH)
                
                if not os.path.exists(directory):
                    os.makedirs(directory)
                bootstrap(fence, detonation, launch, "D:\SIM\{}_{}_{}".format(fence, detonation, launch))
                #e.append(fence, detonation, launch)

def getCharacterData(dataTable, crewName):
    #print("a")
    #import pandas as pd
    #dataTable = pd.read_csv(fileName, sep ="~", names=["a", "b", "c"])
    memberData = dataTable.loc[dataTable["a"] == crewName, ["b", "c"]]
    memberData.to_pickle("D:/TEMP/{}.pkl".format(crewName))
    
def get(data, cols):
        ret = None
        if len(cols) == 1:
            ret = data.iloc[0][cols[0]]
        elif len(cols) == 2:
            ret = (data.iloc[0][cols[0]], data.iloc[0][cols[1]])
        elif len(cols) == 3:
            ret = (data.iloc[0][cols[0]], data.iloc[0][cols[1]], data.iloc[0][cols[2]])
        return ret

def getWinrates(crewNames, simFolders):
    from datetime import datetime
    import glob
    import pandas as pd
    from multiprocessing import Process
    
    
    results = ""
    crewData = ""
    
    def winConditions():
        return {
                "CREW": {"ZNUTAR DESTROYED": 0, "ZNUTAR LOST": 0, "ENEMY DEFEATED": 0},
                "GT": {"ZNUTAR DESTROYED": 0, "ZNUTAR LOST": 0, "ENEMY DEFEATED": 0, "DRAW": 0}}
    
    
    simPermutation = {}
    simPermutation["TOTAL"] = winConditions()
    
    characterAnalysis = {}
    characterAnalysis["TOTAL"] = {"CREW": {}, "GT": {}}
    
    deathRooms = {} #name [0:2] == "GT" => True
    deathRooms["TOTAL"] = {True: {}, False: {}}
    #each folder in base simulation directory
    for folderName in simFolders:

        lastTime = datetime.now()
        print("Gathering data in {}".format(folderName))
        
        
        
        simPermutation[folderName] = winConditions()
        characterAnalysis[folderName] = {"CREW": {}, "GT": {}}
        deathRooms[folderName] = {True: {}, False: {}}
        
        #each simulation text file contained within permutation set
        for fileName in glob.glob("{}\*".format(folderName)):
            #print(fileName)
            #create table
            dataTable = pd.read_csv(fileName, sep ="~", names=["a", "b", "c"])
            #find winning team
            winner = dataTable.loc[dataTable["b"] == "WON", ["a", "c"]]
            team, winType = get(winner, ["a", "c"])
            simPermutation[folderName][team][winType] += 1
            simPermutation["TOTAL"][team][winType] += 1
            
            for crewName in crewNames:
                continue
                if not crewName in characterAnalysis["TOTAL"][team]:
                    characterAnalysis["TOTAL"][team][crewName] = {}
                if not crewName in characterAnalysis[folderName][team]:
                    characterAnalysis[folderName][team][crewName] = {}
                
                memberData = dataTable.loc[dataTable["a"] == crewName, ["b", "c"]]#pd.read_pickle("D:/TEMP/{}.pkl".format(crewName))###returnedCrewData[crewName] #
                for _, action in memberData.iterrows():
                    #local to permutation
                    if action.iloc[0] not in characterAnalysis[folderName][team][crewName]:
                        characterAnalysis[folderName][team][crewName][action.iloc[0]] = {}
                    if action.iloc[1] not in characterAnalysis[folderName][team][crewName][action.iloc[0]]:
                        characterAnalysis[folderName][team][crewName][action.iloc[0]][action.iloc[1]] = 0
                    characterAnalysis[folderName][team][crewName][action.iloc[0]][action.iloc[1]] += 1
                    #total
                    if action.iloc[0] not in characterAnalysis["TOTAL"][team][crewName]:
                        characterAnalysis["TOTAL"][team][crewName][action.iloc[0]] = {}
                    if action.iloc[1] not in characterAnalysis["TOTAL"][team][crewName][action.iloc[0]]:
                        characterAnalysis["TOTAL"][team][crewName][action.iloc[0]][action.iloc[1]] = 0
                    characterAnalysis["TOTAL"][team][crewName][action.iloc[0]][action.iloc[1]] += 1
            
            #get death rooms
            deaths = dataTable.loc[dataTable["b"] == "DIED IN", ["a", "c"]]
            for _, death in deaths.iterrows():
                #print(death.iloc[0])
                organism, room = (death.iloc[0], death.iloc[1])
                team = organism[0:2] == "GT"
                if not room in deathRooms[folderName][team]:
                    deathRooms[folderName][team][room] = 0
                deathRooms[folderName][team][room] += 1
                
                if not room in deathRooms["TOTAL"][team]:
                    deathRooms["TOTAL"][team][room] = 0
                deathRooms["TOTAL"][team][room] += 1
        print(str(datetime.now() - lastTime))
    
    for folderName in ["TOTAL"] + simFolders:
        if folderName not in characterAnalysis:
            continue
        print("Parsing Data... {}\n\t{}".format(folderName, str(datetime.now())))
        
        #headers
        crewData += "\n{}\n".format(folderName)
        results += "\n{}\n".format(folderName)
        
        #member analysis
        #for winningTeam, crew in characterAnalysis[folderName].items():
        #    crewData += "\t{}\n".format(winningTeam)
        #    for crewMember, actions in crew.items():
        #        crewData += "\t\t{}\n".format(crewMember)
        #        for action, things in actions.items():
        #            crewData += "\t\t\t{}\n".format(action)
        #            for thing, count in sorted(list(things.items()), key = lambda kv: (-kv[1], kv[0])):
        #                crewData += "\t\t\t\t{}: {}\n".format(thing, count)
        #            crewData += "\n"
        #        crewData += "\n"

        #winrates
        for team in simPermutation[folderName].keys():
            results += "\n{}\n".format(team)
            for d, e in simPermutation[folderName][team].items():
                results += "\t{}: {}\n".format(d, e)
        #deaths
        for team in deathRooms[folderName].keys():
            results += "\n{}\n".format({True: "GT", False: "CREW"}[team])
            for roomName, deaths in reversed(sorted(deathRooms[folderName][team].items(), key = lambda kv:(kv[1], kv[0]))):
                results += "\t{}: {}\n".format(roomName, deaths)
    return (crewData, results)
    
def analyseSimulations(basePath = "D:\SIM"):
    a = Analysis(basePath, open("DATA\Crew.txt", "r").readlines())
    crew, matches = getWinrates(a.crewNames, a.simFolders)
    open("Game Analysis.txt", "w").write(matches)
    open("Member Analysis.txt", "w").write(crew)
    
def parseAnalysis(analysisName = "Member Analysis.txt"):
    def tabs(line):
        tester = line
        tabs = 0
        if line == "\n":
            return -1
        while tester[0:1] == "\t":
            tester = tester[1:]
            tabs += 1
        return tabs

    reader = open(analysisName, "r")
    
    
    allActions = {} # {Action: ALL subactions}
    memberAnalysis = {"GT": {}, "CREW": {}} # {crewName: {sideVictory: {fileName : {actions: {subactions: count}}}}}
    
    fileName, winningSide, crew, action, subaction = "", "" ,"" ,"", ""
    for line in reader.readlines():

        s = line.strip()
        level = tabs(line)
        if level == -1: #empty line
            continue
        elif level == 0: #contains file header
            fileName = s
        elif level == 1: #contains winning side
            winningSide = s
        elif level == 2: #contains crew member
            crew = s
            print("{},{}".format(fileName, crew))
        elif level == 3: #contains action
            action = s
        elif level == 4: #contains subaction
            #create action
            if not action in memberAnalysis[winningSide]:
                memberAnalysis[winningSide][action] = {}
            #add crew to action
            if not crew in memberAnalysis[winningSide][action]:
                memberAnalysis[winningSide][action][crew] = {}
            #create file if required
            if not fileName in memberAnalysis[winningSide][action][crew]:
                memberAnalysis[winningSide][action][crew][fileName] = {}
            #create subaction
            subaction, count = s[0:s.find(":")].strip(), int(s[s.find(":")+1:].strip()) 
            memberAnalysis[winningSide][action][crew][fileName][subaction] = count
            #append subaction in all actions
            if not action in allActions:
                allActions[action] = []
            if not subaction in allActions[action]:
                allActions[action].append(subaction)
        else:
            print("I broke on line [{}]".format(line))
            exit
    
    actionExclusions = ["ATTACKING", "KILLED BY DAMAGE DICE", "STUNNED", "CANNOT ATTACK", "CANNOT MOVE"]
    for victor, actionList in memberAnalysis.items():
        for actionName, crewList in actionList.items():
            if actionName in actionExclusions:
                continue
            for crewName, fileList in crewList.items():
                sortedSubactions = sorted(allActions[actionName])
                fileHeader = "FILE"
                for subactionName in sortedSubactions:
                    fileHeader += ",{}".format(subactionName)
                writer = open("MEMBER_ANALYSIS\\{}_{}_{}.csv".format(victor, actionName, crewName), "w")
                writer.write("{}\n".format(fileHeader))
                for fileName, subActionList in fileList.items():
                    if fileName == "TOTAL":
                        continue
                    lineEntry = fileName
                    for subactionName in sortedSubactions:
                        subactionCount = 0
                        if subactionName in subActionList:
                            subactionCount = subActionList[subactionName]
                        lineEntry += ",{}".format(subactionCount)
                    writer.write("{}\n".format(lineEntry))
                    
def plotAnalysis(fileName = None):
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    #sns.set()
    
    df = pd.read_csv(fileName)
    fig = df.plot(figsize=(400, 50), x='FILE', kind='bar')
    #df = sns.load_dataset(fileNamsssssssssssssse)
    #sns.lmplot(x="FILE", y="ORRURRENCES", data = df)
    #fig = df.plot()#figsize=(100, 100), linewidth=2, fontsize=20)
    #plt.xlabel('HELP', fontsize=20)
    fig = fig.get_figure()
    fig.savefig("catchmeonyelp.png")

def deleteLater(fileName):
    writer = open(fileName, "r")
    lines = writer.readlines()
    out = ""
    f = ""
    lf = ""
    writer = open("{}_modified.csv".format(fileName), "w")
    writer.write("File, DESTROYED, LOST, ENEMY DEFEATED\n")
    for line in lines:
        if line[0:1] == "D":
            f = line.strip()
            out = f
        if line.strip() in ["CREW", "GT"]:
           lf = line.strip()
           print("[{}]".format(lf))
        if lf == "GT":
            continue
        
        if line.strip().find("ZNUTAR DESTROYED") >= 0:
            out += ", {}".format(line.strip()[line.strip().find(":")+1:])
        if line.strip().find("ZNUTAR LOST") >= 0:
            out += ", {}".format(line.strip()[line.strip().find(":")+1:])
        if line.strip().find("ENEMY DEFEATED") >= 0:
            out += ", {}".format(line.strip()[line.strip().find(":")+1:])
            writer.write("{}\n".format(out))
    

if __name__ == "__main__":
    
    #deleteLater("Game Analysis_final.txt")
    generateSimulations()
    #analyseSimulations()
    #parseAnalysis()
    #plotAnalysis("MEMBER_ANALYSIS\CREW_DIED IN_Captain Yid.csv")
    