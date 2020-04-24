from random import randrange, sample
from sys import stderr

from .room import Room
from .organism import Organism
from .weapon import Weapon
from .weaponEffect import Effect, EffectBag
from copy import copy

class Ship:
    
    def __init__(self, roomSetup, roomLoS, roomHatch, crew, gt, weapon, weaponPlacement, weaponChits):
        self.roomSetup = roomSetup
        self.roomLoS = roomLoS
        self.roomHatch = roomHatch
        self.crew = crew
        self.gt = gt
        self.weapon = weapon
        self.weaponPlacement = weaponPlacement
        self.weaponChits = weaponChits
        
    def newBoard(self):
        ship = self.addHatch(self.addLoS(self.createShip()))
        crew = self.createCrew(ship)
        weapons = self.createWeapon()
        self.placeWeapons(weapons, ship)
        gt, atts, starting = self.createGT(ship)
        return (ship, crew, gt, weapons, atts, starting)
    
    #just in case pass by value is an issue
    def createEffects(self):
        a = []
        for line in self.weaponChits:
            a.append(line)
        return a

#||||||||||||||||||||||||||||||||||||ship||||||||||||||||||||||||||||||||||||||
    def createShip(self):
        rooms = []
        
        #create room for each left-side name
        for roomEntry in self.roomSetup:
            rooms.append(Room(roomEntry[0:roomEntry.find("->") - 1])) #get room name on left side of "->"
        
        #attach right-side names
        for room in rooms:
            #connect self
            room.connectedRooms.append(room)
            
            #connect others
            for roomName in Ship.getConnectedRoomNames(Ship.findLine(room.name, self.roomSetup)):
                room.connectedRooms.append(Ship.roomFromName(roomName, rooms))
        
        return rooms
    
    def addLoS(self, ship):
        for room in ship:
            roomLine = Ship.findLine(room.name, self.roomLoS)
            if roomLine != None:
                #room has Los entries
                for losRoomName in Ship.getConnectedRoomNames(roomLine):
                    room.los.append(Ship.roomFromName(losRoomName, ship))
        return ship
                    
    def addHatch(self, ship):
        for room in ship:
            roomLine = Ship.findLine(room.name, self.roomHatch)
            if roomLine != None:
                #room has hatch entries
                for losRoomName in Ship.getConnectedRoomNames(roomLine):
                    room.hatch.append(Ship.roomFromName(losRoomName, ship))
        return ship
    
    def roomFromName(name, rooms):
        for room in rooms:
            if name.strip() == room.name:
                return room
        print("Could Not Find {}".format(name))
        return None
    
    def findLine(findMe, text):
        for line in text:
            if line.find(findMe) == 0:
                return line
        return None
        
    def getConnectedRoomNames(string):
        roomNames = []
        string = string[string.find(">")+2: len(string)] #remove left-side name and "->"
        
        if string.find(",") < 0:
            roomNames.append(string.strip())
        else:
            string = string.split(",")
            for name in string:
                roomNames.append(name.strip())
        return roomNames
    
#||||||||||||||||||||||||||||||||||||crew||||||||||||||||||||||||||||||||||||||
    def createCrew(self, ship):
        crewMembers = []
        
        for line in self.crew:
            memberDetails = line.split(", ")
            #create member
            crewMember = Organism(memberDetails[0].strip(), memberDetails[1].strip(), memberDetails[2].strip(), memberDetails[3].strip())
            crewMembers.append(crewMember)
            
            #place member
            desiredRoom = Ship.roomFromName(memberDetails[randrange(4, len(memberDetails))], ship)
            desiredRoom.enterRoom(crewMember)
            
        return crewMembers
    
#|||||||||||||||||||||||||||||||||||||gt|||||||||||||||||||||||||||||||||||||||
    def createGT(self, ship):
        initials = {}
        attributes = {}
        startingRoomNames = []
        
        #parse file for life states, initial starting amounts, starting rooms
        for line in self.gt:
            if line.find("ATTRIBUTES") == 0:
                #clear out header
                states = line[line.find(">")+2:len(line)]
                #split stages and dump results in a dictionary
                for lifeStage in states.split(";"):
                    stage = lifeStage.split(",")
                    attributes[stage[0].strip()] = (int(stage[1].strip()), #attack
                                                    int(stage[2].strip()), #constitution
                                                    int(stage[3].strip()), #movement
                                                    int(stage[4].strip())) #maximum on ship
            if line.find("INITIAL") == 0:
                inits = line[line.find(">")+2:len(line)]
                for starting in inits.split(";"):
                    sizes = starting.split(",")
                    initials[int(sizes[0].strip())] = (int(sizes[1].strip()), #eggs
                                                       int(sizes[2].strip()), #babies
                                                       int(sizes[3].strip())) #adults
            if line.find("ROOMS") == 0:
                roomNames = line[line.find(">")+2:len(line)]
                for name in roomNames.split(","):
                    startingRoomNames.append(name.strip())
        
        #set starting amounts for life stages
        startingNumbers = {}
        startingNumbers["Egg"], startingNumbers["Baby"], startingNumbers["Adult"] = initials[randrange(1, 7)]
        
       
        GT = []
        GTName = 1
        #create starting GTs
        for stage in ["Egg", "Baby", "Adult"]:
            a, c, m, _ = attributes[stage]
            for i in range(startingNumbers[stage]):
                GT.append(Organism("GT {}".format(GTName), a, c, m, stage))
                GTName += 1 # update global class variable (responsible for giving unique names)
        
        #place initial GT
        nextRoom = startingRoomNames[randrange(0, len(startingRoomNames))]
        if nextRoom == "Choose":
            nextRoom = startingRoomNames[randrange(0, len(startingRoomNames)-1)]
        nextRoom = Ship.roomFromName(nextRoom, ship)
        GTRooms = [] #used to keep track of all rooms a GT has been placed it
        for gt in GT:
            #append first or subsequent rooms
            GTRooms.append(nextRoom)
            
            for room in sample(GTRooms, len(GTRooms)): #scan list of current rooms for empty one
                
                nextRoom = Ship.findEmptyRoom(room)
                
                if nextRoom == None:
                    continue
                nextRoom.enterRoom(gt)
                break
            
            if nextRoom == None:
                stderr.write("Ran out of places to put GTs")
                exit
        
        return (GT, attributes, startingNumbers)
    
    def findEmptyRoom(room):
        if room == None:
            return None
        #remove self-reference from random room sample
        rooms = room.connectedRooms[0:len(room.connectedRooms)]
    
        #randomise room order
        #preserves argument room list order
        for potentialRoom in sample(rooms, len(rooms)):
            if len(potentialRoom.organisms) == 0:
                return potentialRoom #found empty room
    
        return None #passed room has no empty connected rooms

#|||||||||||||||||||||||||||||||||||weapon|||||||||||||||||||||||||||||||||||||
    def createWeapon(self):
        weapons = []
        bag = EffectBag(self.weaponChits.copy())
        for line in self.weapon:
            weaponData = []
            
            for linePortion in line.split(","):
                entry = linePortion.strip()
                if entry.find("(") < 0: #no more parsing required
                    weaponData.append(entry)
                else: #weapon attack types
                    attackTypes = []
                    for attackType in entry.split("("):
                        if attackType == "":
                            continue
                        attackTypes.append((attackType[0:attackType.find(";")].strip(), attackType[attackType.find(";")+1:len(attackType)-1].strip()))
                    weaponData.append(attackTypes)
            weapons.append(Weapon(weaponData[0], weaponData[1], weaponData[2], weaponData[3], weaponData[4].strip(), Effect(), bag))
        return weapons
    
    def placeWeapons(self, weapons, rooms):
        for line in self.weaponPlacement:
            weaponName = line[0:line.find("->") - 1]
            weapon = Ship.roomFromName(weaponName, weapons) #get weapon object
            
            #turn names into rooms
            spawnLocations = []
            for roomName in Ship.getConnectedRoomNames(line):
                spawnLocations.append(Ship.roomFromName(roomName, rooms))
            
            #used for weapons that are returned to spawn rooms after used
            weapon.spawnLocations = spawnLocations
            
            #place weapons in avaiable rooms
            for _ in range(0, weapon.maximum):
                randomRoom = spawnLocations[randrange(0, len(weapon.spawnLocations))]
                randomRoom.pickups.append(copy(weapon))
    
    def printTree(tree):
        s = ""
        for weapon, t in tree:
            s += "/===========================================\n"
            s += "|=Weapon:   {}\n".format(weapon.name)
            s += "{}\n".format(Weapon.printTree(t))
        return s