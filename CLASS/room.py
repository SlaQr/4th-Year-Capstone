#Takes: room name
class Room:
    
    def __init__(self, name):
        self.name: str = name
        self.alreadyLaunched = False
            #used for rooms that can launch ships
        
        #CREW AND GT
        self.organisms = []
        
        #ROOMS CONNECTIONS
        self.connectedRooms = []
            #can move to these rooms
            #can be targeted with range 1 weapons
        self.los = []
            #used for weapons with range LoS
            #rooms not listed but should be are already part of connectedRooms which is checked furing LoS anyways
        self.hatch = []
            #used for weapons containing collateral damage
        
        #WEAPONS IN ROOM
        self.pickups = []
    
    def hasHostileGT(self):
        for o in self.organisms:
            if o.isGT():
                if o.stage in ["Baby", "Adult"]:
                    return True
        return False
        
    def pileOn(self):
        crew = []
        gt = []
        
        for room in self.connectedRooms:
            for o in room.organisms:
                if o.isGT():
                    gt.append(o)
                else:
                    crew.append(o)
        return (crew, gt)
     
    def countCrewConstitution(self):
        totalCon = 0
        for organism in self.organisms:
            if not organism.isGT() and organism.isAlive:
                totalCon += organism.constitution
        return totalCon
        
    def removeUselessWeapons(self, gm):
        for weapon in self.pickups:
            if weapon.effect() in ["NO EFFECT", "GROW", "FRAGMENT"]:
                gm.note(weapon, "DISAPPEARED", self)
                self.pickups.remove(weapon)
    
    def containsActiveFence(self):
        for w in self.pickups:
            if w.name == "Fence" and w.fenceActive:
                return True
        return False
    
    def getFence(self):
        for w in self.pickups:
            if w.name == "Fence" and w.fenceActive:
                w
        return None
    
    def countSurroundingGT(self):
        gts = 0
        for room in self.connectedRooms:
            gts += room.countGT()
        return gts
        
    def countSurroundingCrew(self):
        crew = 0
        for room in self.connectedRooms:
            crew += room.countCrew()
        return crew
            
    def getGT(self):
        gts = []
        for o in self.organisms:
            if o.name[0:2] == "GT":
                gts.append(o)
        return gts
    
    def getCrew(self):
        crew = []
        for o in self.organisms:
            if not o.isGT():
                crew.append(o)
        return crew
    
    def getSurroundingGT(self):
        gts = []
        for room in self.connectedRooms:
            gts += room.getGT()
        return gts
    
    def enterRoom(self, organism):
        self.organisms.append(organism)
        if organism.currentRoom != None: #first time placement check
            organism.currentRoom.exitRoom(organism)
        organism.currentRoom = self
        
    def exitRoom(self, organismLeavingRoom):
        #by names because ids are finicky and I'm not having any of it
        for existingOrganism in self.organisms:
            if existingOrganism.name == organismLeavingRoom.name:
                self.organisms.remove(existingOrganism)
    
    def countGT(self):
        GTCount = 0
        for o in self.organisms:
            if o.name[0:2] == "GT":
                GTCount += 1
        return GTCount
    
    def countCrew(self):
        return len(self.organisms) - self.countGT()
    
    def __str__(self):
        #name header
        status = "/===========================================\n|=Room: {}\n|\n".format(self.name)

        #connected rooms
        status += "|-- Movement Options ({}):\n| |\n".format(len(self.connectedRooms))
        for room in self.connectedRooms:
            status += "| |-- {}\n".format(room.name)
        
        status += "|\n|-- Line of Sight ({}):\n| |\n".format(len(self.los))
        
        for room in self.los:
            status += "| |-- {}\n".format(room.name)
        
        status += "|\n|-- Hatchless Connections ({}):\n| |\n".format(len(self.hatch))
        
        for room in self.hatch:
            status += "| |-- {}\n".format(room.name)
            
        status += "|\n|-- Weapon Pickups:\n| |\n"
        
        for weapon in self.pickups:
            status += "| |-- {}\n".format(weapon.name)
        
        #all organisms + corresponding attributes
        status += "|\n|-- Organisms ({}):\n".format(len(self.organisms))
        for organism in self.organisms:
            first = True
            status += "| |\n"
            for attribute in organism.attributes():
                if first:
                    status += "| |--   {}\n".format(attribute)
                    first = False
                else:
                    status += "| | |-- {}\n".format(attribute)
            
        
        return status