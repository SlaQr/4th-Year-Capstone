import glob
#from multiprocessing import Process, Pipe

def getCharacterData(pipeBack, data, crewName):
    memberData = data.loc[data["a"] == crewName, ["b", "c"]]
    pipeBack.send(memberData)

def get(data, cols):
        ret = None
        if len(cols) == 1:
            ret = data.iloc[0][cols[0]]
        elif len(cols) == 2:
            ret = (data.iloc[0][cols[0]], data.iloc[0][cols[1]])
        elif len(cols) == 3:
            ret = (data.iloc[0][cols[0]], data.iloc[0][cols[1]], data.iloc[0][cols[2]])
        return ret

class Analysis:
    
    def __init__(self, basePath, crewData):
        #get all simulations in directory
        self.simFolders = glob.glob("{}\*".format(basePath))
        
        #import crew data and parse names
        self.crewNames = []
        for line in crewData:
            self.crewNames.append(line[0:line.find(",")])
    
    def getWinrates(self):
        from datetime import datetime
        
        results = ""
        crewData = ""
        
        def winConditions():
            return {
                    "CREW": {"ZNUTAR DESTROYED": 0, "ZNUTAR LOST": 0, "ENEMY DEFEATED": 0},
                    "GT": {"ZNUTAR DESTROYED": 0, "ZNUTAR LOST": 0, "ENEMY DEFEATED": 0}}
        import pandas as pd
        
        simPermutation = {}
        simPermutation["TOTAL"] = winConditions()
        
        characterAnalysis = {}
        characterAnalysis["TOTAL"] = {"CREW": {}, "GT": {}}
        
        deathRooms = {} #name [0:2] == "GT" => True
        deathRooms["TOTAL"] = {True: {}, False: {}}

        #each folder in base simulation directory
        for folderName in self.simFolders:
            print("Gathering data in {}\n\t{}".format(folderName, str(datetime.now())))
            
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
                
                
                
                #otherTable = dataTable.loc[dataTable["a"] == self.crewNames[0], ["a", "b", "c"]]
                #for cName in self.crewNames[1:]:
                #    otherTable += dataTable.loc[dataTable["a"] == cName, ["a", "b", "c"]]
                #multiprocess experiment
                crewData = []
                returnedCrewData = {}
                for cName in self.crewNames:
                    pipe_parent, pipe_child = Pipe()
                    subProcess = Process(target=getCharacterData, args=(pipe_child, dataTable, cName))
                    crewData.append ((cName, pipe_parent, subProcess))
                print("1")
                for _, _, subProcess in crewData:
                    subProcess.start()
                    print("2")
                    
                for cName, pipe, subProcess in crewData:
                    print("Waiting for data {}".format(cName))
                    while subProcess.is_alive():
                        continue
                    returnedCrewData[cName] = pipe.get()
                
                for crewName in self.crewNames:
                    
                    if not crewName in characterAnalysis["TOTAL"][team]:
                        characterAnalysis["TOTAL"][team][crewName] = {}
                    if not crewName in characterAnalysis[folderName][team]:
                        characterAnalysis[folderName][team][crewName] = {}
                    
                    memberData = returnedCrewData[crewName] #dataTable.loc[dataTable["a"] == crewName, ["b", "c"]]
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
        
        for folderName in ["TOTAL"] + self.simFolders:
            if folderName not in characterAnalysis:
                continue
            print("Parsing Data... {}\n\t{}".format(folderName, str(datetime.now())))
            
            #headers
            crewData += "\n{}\n".format(folderName)
            results += "\n{}\n".format(folderName)
            
            #member analysis
            for winningTeam, crew in characterAnalysis[folderName].items():
                crewData += "\t{}\n".format(winningTeam)
                for crewMember, actions in crew.items():
                    crewData += "\t\t{}\n".format(crewMember)
                    for action, things in actions.items():
                        crewData += "\t\t\t{}\n".format(action)
                        for thing, count in sorted(list(things.items()), key = lambda kv: (-kv[1], kv[0])):
                            crewData += "\t\t\t\t{}: {}\n".format(thing, count)
                        crewData += "\n"
                    crewData += "\n"

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
        #print(wins["GT"]["ZNUTAR DESTROYED"], wins["GT"]["ZNUTAR LOST"], wins["GT"]["ENEMY DEFEATED"])