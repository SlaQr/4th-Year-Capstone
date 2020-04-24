#inherits Organism from Ship class
from copy import copy
from random import randrange

class P:
    def __init__(self, s = ""):
        self.name = str(s)

class Weapon:
    def __init__(self, name, targetType, attacks, collateral, maximum, weaponEffect, effectBag):
        self.dumbMode = True
        self.name = name
        self.targetType = targetType
        self.attacks = attacks
            #[(range, reusable), *]
        self.collateral = collateral
        self.weaponEffect = weaponEffect
        self.heldBy = None
        self.fenceCurrentRoom = None
        self.fenceActive = False
        self.spawnLocations = []
        self.maximum = int(maximum)
        self.effectBag = effectBag
    
    def pickup(self, crew, gamemaster):
        if len(crew.weaponOptions) < 2 and crew.isAlive and crew.stun <= 0:
            #remove from room
            for weapon in crew.currentRoom.pickups:
                if weapon.name == self.name:
                    crew.currentRoom.pickups.remove(weapon)
                    break
            #add to person
            crew.weaponOptions.append(self)
            self.heldBy = crew
            gamemaster.note(crew, "GRABBED", self)
            if crew.firstWeapon:
                gamemaster.note(crew, "FIRST PICKUP", self)
        else:
            gamemaster.note(crew, "HANDS WERE FULL", self)
    
    def getTemporary(self):
        return self.effectBag.generateTemporary()
    
    def getPermanent(self):
        if self.weaponEffect.effect == None:
            self.weaponEffect.effect = self.effectBag.generatePermanent()
    
    def drop(self):
        if self.heldBy != None and self.name != "Bare Hand":
            self.heldBy.currentRoom.pickups.append(self)
    
    def __str__(self):
        a = "Name:\t{}\n".format(self.name)
        a += "Target:\t{}\n".format(self.targetType)
        a += "Attacks:\n"
        for ra, re in self.attacks:
            a += "\tRange:\t{}\n\tReuse:\t({})\n".format(ra,re)
        a += "Coll:\t{}\n".format(self.collateral)
        
        return a
    
    def BH(self, attacker, gm, targets, collateral, reusable):
        if len(targets) > 0:
            target = targets[randrange(0, len(targets))]
            #GT must attack robot if it's in the same room
            if self.heldBy.name[0:2] == "GT":
                for t in targets:
                    if t.name == "Robot":
                        target = t
                        break
            target.addDamage(attacker, self, self.weaponEffect)
            gm.note(attacker, "USING", self)
            gm.note(attacker, "ATTACKING", target)
            gm.note(attacker, "ATTACKING STAGE", P(target.stage[:]))

    def BoA(self, attacker, gm, targets, collateral, reusable):
        if len(targets) > 0:
            target = targets[randrange(0, len(targets))]
            target.addDamage(attacker, self, self.weaponEffect)
            gm.note(attacker, "USING", self)
            gm.note(attacker, "ATTACKING", target)
            gm.note(attacker, "ATTACKING STAGE", P(target.stage[:]))
            #remove weapon from inventory
            #_ = self.heldBy.weaponOptions.pop(1)
            del attacker.weaponOptions[1]
            #return to spawn
            self.heldBy = None
            self.spawnLocations[randrange(0, len(self.spawnLocations))].pickups.append(self)
    
    def CoZ(self, attacker, gm, targets, collateral, reusable):
        if len(targets) > 0:
            target = targets[randrange(0, len(targets))]
            target.addDamage(attacker, self, self.weaponEffect)
            gm.note(attacker, "USING", self)
            gm.note(attacker, "ATTACKING", target)
            gm.note(attacker, "ATTACKING STAGE", P(target.stage[:]))
            #remove weapon from inventory
            del attacker.weaponOptions[1]
            #return to spawn
            self.heldBy = None
            self.spawnLocations[randrange(0, len(self.spawnLocations))].pickups.append(self)
    
    def CB(self, attacker, gm, targets, collateral, reusable):
        if len(targets) > 0:
            gm.note(attacker, "USING", self)
            for target in targets:
                target.addDamage(attacker, self, self.weaponEffect)
                gm.note(attacker, "ATTACKING", target)
                gm.note(attacker, "ATTACKING STAGE", P(target.stage[:]))
    
    def EF(self, attacker, gm, targets, collateral, reusable):
        gm.note(attacker, "PLACED FENCE", attacker.currentRoom)
        
        #place and activate
        attacker.currentRoom.pickups.append(self)
        self.fenceActive = True
        
        #fence placing conditions
        attacker.canMove = False
        attacker.canAttack = False
        #remove links
        del attacker.weaponOptions[1]
        self.heldBy = None
    
    def FE(self, attacker, gm, targets, collateral, reusable):
        if len(targets) > 0:
            gm.note(attacker, "USING", self)
            for target in targets:
                target.addDamage(attacker, self, self.weaponEffect)
                gm.note(attacker, "ATTACKING", target)
                gm.note(attacker, "ATTACKING STAGE", P(target.stage[:]))
    
    def GG(self, attacker, gm, targets, collateral, reusable):
        from .weaponEffect import Effect
        gm.note(attacker, "USING", self)
        for organism in collateral:
            gm.note(attacker, "COLLATERAL", organism)
            if organism.name.find("GT") >= 0:
                organism.addDamage(attacker, self, self.weaponEffect)
                gm.note(attacker, "ATTACKING STAGE", P(organism.stage[:]))
            else:
                organism.addDamage(attacker, self, Effect("STUN"))
        #respawn weapon
        del attacker.weaponOptions[1]
        self.heldBy = None
        self.spawnLocations[randrange(0, len(self.spawnLocations))].pickups.append(self)
    
    def HN(self, attacker, gm, targets, collateral, reusable):
        if len(targets) > 0:
            target = targets[randrange(0, len(targets))]
            target.addDamage(attacker, self, self.weaponEffect)
            gm.note(attacker, "USING", self)
            gm.note(attacker, "ATTACKING", target)
            gm.note(attacker, "ATTACKING STAGE", P(target.stage[:]))
    
    def K(self, attacker, gm, targets, collateral, reusable):
        if len(targets) > 0:
            target = targets[randrange(0, len(targets))]
            target.addDamage(attacker, self, self.weaponEffect)
            gm.note(attacker, "USING", self)
            gm.note(attacker, "ATTACKING", target)
            gm.note(attacker, "ATTACKING STAGE", P(target.stage[:]))
            if reusable == "No":
                #move knife to target room
                del attacker.weaponOptions[1]
                #return to spawn
                self.heldBy = None
                target.currentRoom.pickups.append(self)
                gm.note(self, "THROWN", target.currentRoom)
    
    def PS(self, attacker, gm, targets, collateral, reusable):
        if len(targets) > 0:
            target = targets[randrange(0, len(targets))]
            target.addDamage(attacker, self, self.weaponEffect)
            gm.note(attacker, "USING", self)
            gm.note(attacker, "ATTACKING", target)
            gm.note(attacker, "ATTACKING STAGE", P(target.stage[:]))
    
    def RF(self, attacker, gm, targets, collateral, reusable):
        from .weaponEffect import Effect
        gm.note(attacker, "USING", self)
        for organism in collateral:
            gm.note(attacker, "COLLATERAL", organism)
            if organism.name.find("GT") >= 0:
                organism.addDamage(attacker, self, self.weaponEffect)
                gm.note(attacker, "ATTACKING STAGE", P(organism.stage[:]))
            else:
                organism.addDamage(attacker, self, Effect("KILL 5"))
        #respawn weapon
        del attacker.weaponOptions[1]
        self.heldBy = None
        self.spawnLocations[randrange(0, len(self.spawnLocations))].pickups.append(self)
    
    def SP(self, attacker, gm, targets, collateral, reusable):
        if len(targets) > 0:
            target = targets[randrange(0, len(targets))]
            target.addDamage(attacker, self, self.weaponEffect)
            gm.note(attacker, "USING", self)
            gm.note(attacker, "ATTACKING", target)
            gm.note(attacker, "ATTACKING STAGE", P(target.stage[:]))
    
    def WT(self, attacker, gm, targets, collateral, reusable):
        if len(targets) > 0:
            target = targets[randrange(0, len(targets))]
            target.addDamage(attacker, self, self.weaponEffect)
            gm.note(attacker, "USING", self)
            gm.note(attacker, "ATTACKING", target)
            gm.note(attacker, "ATTACKING STAGE", P(target.stage[:]))
    
    def fencePlaceholder(self, attacker, gm, targets, collateral, reusable):
        pass
    
    def dealDamage(self, gm, attacker, targets, collateral, reusable):
        if attacker.stage != "Egg":
            damage = lambda a : a(attacker, gm, targets, collateral, reusable)
            damage(
                {
                    "Bare Hand": lambda: self.BH,
                    "Bottle of Acid": lambda : self.BoA,
                    "Canister of Zgwortz": lambda : self.CoZ,
                    "Comm Beamer": lambda : self.CB,
                    "Electric Fence": lambda : self.fencePlaceholder,
                    "Fire Extinguisher": lambda : self.FE,
                    "Gas Grenade": lambda : self.GG,
                    "Hypodermic Needle": lambda : self.HN,
                    "Knife": lambda : self.K,
                    "Pool Stick": lambda : self.PS,
                    "Rocket Fuel": lambda : self.RF,
                    "Stun Pistol": lambda : self.SP,
                    "Welding Torch": lambda : self.WT
                }[self.name]()
            )
            
    def give(self, organism):
        if len(organism.weaponOptions) < 2:
            newWeapon = copy(self)
            newWeapon.heldBy = organism
            organism.weaponOptions.append(newWeapon)

    def effect(self):
        return self.weaponEffect.effect
    
    def removeDupeOrganisms(organisms):
        for i, org1 in enumerate(organisms):
            for org2 in organisms[i+1:len(organisms)]:
                if org1.name == org2.name:
                    organisms.remove(org2)
        return organisms
    
    def getDamageTree(self, heldBy):
        attackTypes = []
        
        for rng, reusable in self.attacks:
            targetRooms = []
            #range 0
            t, c = Weapon.organismsInRoom(heldBy, heldBy.currentRoom, self.targetType, self.collateral)
            targetRooms.append((heldBy.currentRoom, t, c))
            #range 1
            if rng == "1":
                for room in heldBy.currentRoom.connectedRooms[1:len(heldBy.currentRoom.connectedRooms)]:
                    t, c = Weapon.organismsInRoom(heldBy, room, self.targetType, self.collateral)
                    targetRooms.append((room, t, c))
            #line of site
            if rng == "LoS":
                for room in heldBy.currentRoom.los:
                    t, c = Weapon.organismsInRoom(heldBy, room, self.targetType, self.collateral)
                    targetRooms.append((room, t, c))
            attackTypes.append((targetRooms, reusable, rng))
            
        return attackTypes
    
    def printTree(tree):
        currentString = ""
        firstTime = True
        for rooms, reusable, rng in tree:
            if firstTime == False:
                currentString += "|\n"
            firstTime = False
            currentString += "|=Range:    {}\n".format(rng)
            currentString += "|=Reusable: {}\n".format(reusable)
            #currentString += "|\n"
            for room, organisms, collateral in rooms:
                currentString += "|\n"
                currentString += "|-- {}\n".format(room.name)
                currentString += "| |-- Targets: ({})\n".format(len(organisms))
                for organism in organisms:
                    currentString += "| | |-- {} in {}\n".format(organism.name, organism.currentRoom.name)
                currentString += "| |\n"
                currentString += "| |-- Collateral: ({})\n".format(len(collateral))
                for organism in collateral:
                    currentString += "| | |-- {} in {}\n".format(organism.name, organism.currentRoom.name)
                
        return currentString
        
    def getHatchCollateral(weaponHolder, room):
        coll = []
        for organism in room.organisms:
            coll.append(organism)
        return coll
    
    def organismsInRoom(weaponHolder, room, target, collateral):
        targets = []
        coll = []
        for organism in room.organisms:
            #specific target type
            isCrew = (weaponHolder.name[0:2] != "GT")
            isTargetCrew = (organism.name[0:2] != "GT")
            if isCrew != isTargetCrew:
                targets.append(organism)
                    
        #check if hatch damage and get hatch rooms
        coll += Weapon.getHatchCollateral(weaponHolder, room)
        if target == "Hatch" and collateral != "No":
            for connectedByHatch in room.hatch:
                coll += Weapon.getHatchCollateral(weaponHolder, connectedByHatch)
        return (targets, coll)      
