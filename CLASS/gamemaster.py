#inherits Organism from Ship class
from random import randrange, sample
from .weapon import Weapon
from .weaponEffect import EffectBag

#keep uniform *.name in game printout
class P:
    def __init__(self, s = ""):
        self.name = str(s)

class GameMaster:
    def __init__(self, ship):
        self.ship = ship
        self.escapingShips = []
        self.detonation = False
        self.explosionCountdown = 3
        
        self.GTAttributes = {}
        self.currentGTs = {}
        self.GTNameCounter = 1
        
        self.rooms = []
        self.crew = []
        self.gt = []
        self.weapons = []
        self.gameOutcomes = []
        self.currentGameActions = [] #[(actor, action, target), *]
    
    def showGame(self, gameName):
        spaces = 25
        writer = open(gameName, "w")
        writer.write("")
        writer = open(gameName, "a")
        
        s = ""
        for a, b, c in self.currentGameActions:
            if a == None or c == None:
                print(b)
            s += "{}{}{}{}{}\n".format(a.name, "~", b, "~", c.name)
            #s += "{}{}{}{}{}\n".format(a.name, " "*(spaces-len(a.name)), b, " "*(spaces-len(b)), c.name)
        writer.write(s)
        writer.close()
    
    def note(self, a, b, c, debug = False):
        if not debug:
            self.currentGameActions.append((a, b, c))
        else:
            self.debugger.write("{}{}{}{}{}\n".format(a.name, "~", b, "~", c.name))
            
        
    
    def newGame(self, fence, detonation, launch):
        self.rooms, self.crew, self.gt, self.weapons, self.GTAttributes, self.currentGTs = self.ship.newBoard()
        self.currentGTs["Fragment"] = 0
        self.currentGameActions = []
        self.escapingShips = []
        
        self.GTNameCounter = 1  #reset for GameMaster being reused
        for val in self.currentGTs.values():
            self.GTNameCounter += int(val)
            
        #add initial spawns to game actions
        for member in self.crew:
            self.note(member, "PLACED", member.currentRoom)
        for member in self.gt:
            self.note(member, "PLACED", member.currentRoom)
        for member in self.gt:
            self.note(member, "STAGE", P(member.stage))
            
        #initial weapon placement
        for room in self.rooms:
            for item in room.pickups:
                self.note(item, "PLACED", room)
            
        #find a crew member that can move into a room containing GTs
        roomContainingGT = []
        GTDiscoverer = []
        for _ in range(0, 2):
            for crewMember in sample(self.crew, len(self.crew)):
                alreadyUsed = False
                for o in GTDiscoverer:
                    if o.name == crewMember.name:
                        alreadyUsed = True
                if alreadyUsed:
                    continue
                GTFound = False
                for connected in crewMember.currentRoom.connectedRooms:
                    if connected.countGT() > 0:
                        GTFound = True
                        GTDiscoverer.append(crewMember)
                        roomContainingGT.append(connected)
                        break
                if GTFound:
                    break
        
        #move crew
        for i in range(0, len(GTDiscoverer)):
            roomContainingGT[i].enterRoom(GTDiscoverer[i])
            GTDiscoverer[i].mustAttackCurrentRoom = True
            self.note(GTDiscoverer[i], "MOVED", roomContainingGT[i])
        #initial attack
        for crew in GTDiscoverer:
            self.dumbAttack(crew)
        for g in self.gt:
            self.resolveDamage(g)
        
        counter = 0
        
        while True:
            counter += 1
            if counter > 4000:
                self.note(P("GT"), "WON", P("DRAW"))
                break
            self.note(P("ROUND"), str(counter), P())
            #green thing player turn
            self.GTTurn()
            if GameMaster.countAlive(self.gt) == 0:
                self.note(P("CREW"), "WON", P("ENEMY DEFEATED"))
                break
            #crew player
            self.CrewTurn_Run(fence, detonation, launch)
            if GameMaster.countAlive(self.crew) == 0:
                if len(self.escapingShips) == 0:
                    self.note(P("GT"), "WON", P("ENEMY DEFEATED"))
                    break
                else:
                    GTPoints, endStatement = {True: (55.5, "ZNUTAR DESTROYED"), False: (110, "ZNUTAR LOST")}[self.detonation]
                    CrewPoints = self.epilogue()
                    self.note(P({True: "CREW", False: "GT"}[CrewPoints > GTPoints]), "WON", P(endStatement))
                    break
            if self.detonation:
                self.explosionCountdown -= 1
            
                if self.explosionCountdown == 0:
                    GTPoints = 55.5
                    CrewPoints = self.epilogue()
                    self.note(P({True: "CREW", False: "GT"}[CrewPoints > GTPoints]), "WON", P("ZNUTAR DESTROYED"))
                    break
        
    def getAlive(organisms):
        alive = []
        for o in organisms:
            if o.isAlive:
                alive.append(o)
        return alive
    
    def countAlive(organisms):
        return len(GameMaster.getAlive(organisms))
        
    def GTTurn(self, debug=False):
        
        
        #GROW
        if debug:
            for g in self.gt:
                if g.isAlive:
                    self.note(g, "STAGE", P(g.stage))
        self.growGTStage()
        
        for g in GameMaster.getAlive(self.gt):
            self.moveOrganism(g)        #MOVE
            self.dumbAttack(g)              #ATTACK
            g.roundEnd()                    #WAKE UP
            
        #RESOLVE CREW DAMAGE
        for c in self.crew:
            self.resolveDamage(c)
    
    def shipsLeft(self):
        t = True
        for r in self.rooms:
            if r.name in ["Scout Bay", "Saucer Bay", "Cockboat Bay"]:
                t = t and not r.alreadyLaunched
        return t
    
    def CrewTurn_Run(self, fence, detonation, launch, debug=False):
        aliveCrew = GameMaster.getAlive(self.crew)
        FENCE_USE_CHANCE = fence
        SHIP_DETONATION_CHANCE = detonation
        SHIP_LAUNCH_CHANCE = launch
        
        self.discardUselessWeapons(aliveCrew)
        self.crewPickup(aliveCrew)      #GRAB
        self.fence(aliveCrew, FENCE_USE_CHANCE)
        
        for c in aliveCrew:
            self.shipDetonation(c, SHIP_DETONATION_CHANCE)
            #move to escape
            if self.shipsLeft():
                if c.isAlive and c.stun == 0 and c.canMove:
                    #safeWay
                    depth, movement = c.lookForEscape(c.currentRoom)

                    if depth == 100:
                        #risky way
                        depth, movement = c.lookForEscape(c.currentRoom, True)
                    for counter, r in enumerate(movement):
                        if counter >= c.movement:
                            break
                        
                        r.enterRoom(c)
                        self.note(c, "MOVING", r)
                        
                        if c.currentRoom.containsActiveFence():
                            break
                        
                        mustStop = False
                        if c.currentRoom.countGT() > 0:
                            for o in c.currentRoom.organisms:
                                if o.stage in ["Baby", "Adult"]:
                                    c.mustAttackCurrentRoom = True
                                    self.note(c, "ENCOUNTERED ENEMY", c.currentRoom)
                                    #print("{} encountered {} Green Things!".format(organism.name, organism.currentRoom.countGT()))
                                    mustStop = True
                        if mustStop:
                            break
                        
            else:
                self.moveOrganism(c)
            #launch ships
            self.launchShip_smart(c)
            self.dumbAttack(c)
            c.roundEnd()
    
        self.giveWeaponPermanent()

        for g in self.gt:
            self.resolveDamage(g)
    
    def CrewTurn(self, fence, detonation, launch, debug=False):
        aliveCrew = GameMaster.getAlive(self.crew)
        FENCE_USE_CHANCE = fence
        SHIP_DETONATION_CHANCE = detonation
        SHIP_LAUNCH_CHANCE = launch
        
        self.discardUselessWeapons(aliveCrew)
        self.crewPickup(aliveCrew)      #GRAB
        
        self.fence(aliveCrew, FENCE_USE_CHANCE)           #try to place a fence
        
        for c in aliveCrew:
            self.shipDetonation(c, SHIP_DETONATION_CHANCE)
            self.launchShip(c, SHIP_LAUNCH_CHANCE)
            self.moveOrganism(c)    #MOVE
            self.dumbAttack(c)          #ATTACK
            c.roundEnd()                #RESET CONDITIONAL FLAGS AND REDUCE STUN

        self.giveWeaponPermanent()      #ASSIGN WEAPON EFFECTS
        
        for g in self.gt:
            self.resolveDamage(g)       #DAMAGE GT
        
    def discardUselessWeapons(self, aliveCrew):
        for member in aliveCrew:
            if len(member.weaponOptions) <= 1:
                #only has bare hand
                continue
            
            if member.weaponOptions[1].effect() in ["NO EFFECT", "GROW", "FRAGMENT"]:
                weapon = member.weaponOptions[1]
                self.note(member, "DISCARDED", weapon)
                member.weaponOptions[1].heldBy = None
                del member.weaponOptions[1]
                
        for room in self.rooms:
            room.removeUselessWeapons(self)
                    
        
    def fence_smart(self, aliveCrew):
        for member in aliveCrew:
            fence = member.findWeapon("Electric Fence")
            if fence == None:
                continue
            #member has a fence
            
            #fence has desireable effect
            if fence.effect() in [None, "KILL 5", "KILL 4", "KILL 3", "STUN", "SHRINK"]:
                if member.outmatchedSur() or member.outmatched():
                    fence.EF(member, self, [], [], "")
            #fence has a bad effect
            else:
                self.note(member, "DISCARDED", fence)
                fence.heldBy = None
                del member.weaponoptions[1]
                
        
    def fence(self, aliveCrew, FENCE_USE_CHANCE):
        for c in aliveCrew:
            for w in c.weaponOptions:
                if w.name == "Electric Fence":
                    #roll for fence use
                    if FENCE_USE_CHANCE >= randrange(0, 100)+1:
                        w.EF(c, self, [], [], "No") #place fence
        
    def crewPickup(self, aliveCrew):
        
        for member in sample(aliveCrew, len(aliveCrew)):
            if member.stun > 0:
                self.note(member, "STUNNED", P("CANNOT GRAB"))
                continue
            
            if not member.name in ["Robot", "Mascot"] and member.isAlive: #cannot grab items
                choice = randrange(0, len(member.currentRoom.pickups) + 1)
                if choice == len(member.currentRoom.pickups): #no weapon available / decided not to pick one up
                    self.note(member, "GRABBED", P("NOTHING ({})".format(len(member.currentRoom.pickups))))
                else:
                    member.currentRoom.pickups[choice].pickup(member, self)
                    
    def crewPickup_smart(self, aliveCrew):
        for member in sample(aliveCrew, len(aliveCrew)):
            if member.stun > 0:
                self.note(member, "STUNNED", P("CANNOT GRAB"))
                continue
            
            if not member.name in ["Robot", "Mascot"] and member.isAlive: #cannot grab items
                if len(member.currentRoom.pickups) > 0 and len(member.weaponOptions) <= 1:
                    choice = randrange(0, len(member.currentRoom.pickups))
                    member.currentRoom.pickups[choice].pickup(member, self)
                
            
    def growGTStage(self):
        stages = {"Egg": [], "Fragment": [], "Baby": [], "Adult": []}
        aliveGT = []
        for g in self.gt:
            if g.isAlive:
                aliveGT.append(g)
        for g in aliveGT:
            stages[g.stage].append(g)
        stages = stages.values() #list of lists hopefully
        growableStages = []
        for s in stages:
            if len(s) > 0:
                growableStages.append(s)
        if len(growableStages) > 0:
            growableStages = growableStages[randrange(0, len(growableStages))] #select stage randomly
            self.note(P("GROWING"), "STAGE", P(growableStages[0].stage))
            for g in growableStages:
                self.growGT(g, False)
        else:
            self.note(P("GROWING"), "STAGE", P("NONE"))
        
    def giveWeaponPermanent(self):
        #assign weaponEffects
        toGetEffects = []
        for gt in self.gt:
            unknowns = []
            for _, w, _ in gt.damageStack:
                if w.effect() == None:
                    unknowns.append(w)
            #add weapon to permanent list
            if len(unknowns) <= 1:
                for w in unknowns:
                    toGetEffects.append(w)
            else: #weapon might need to be removed from toGetEffects
                for permCandidate in toGetEffects:
                    for unknown in unknowns:    
                        if permCandidate.name == unknown.name:
                            toGetEffects.remove(permCandidate)
                            break
        for weapon in toGetEffects:
            weapon.getPermanent()
            self.note(weapon, "ASSIGNED", P(weapon.effect()))
            
    def growGT(self, GT, fromWeapon = True):
        from .weaponEffect import Effect
        
        stages = {
            "Egg": "Baby",
            "Fragment": "Baby",
            "Baby": "Adult",
            "Adult": "Egg"
        }
        
        if GT.stun > 0:
            self.note(GT, "CANNOT GROW", P("STUNNED"))
            return
        
        nextStage = str(stages.get(GT.stage, "Invalid"))
        if nextStage == "Egg" and not fromWeapon:
            egg = self.createGT("Egg")
            if egg != None:
                self.note(GT, "LAID EGG", egg)
                GT.currentRoom.enterRoom(egg)
        if nextStage in ["Baby", "Adult"]:
            a, c, m, stageMaximum = self.GTAttributes[nextStage]
            
            if self.currentGTs[nextStage] < stageMaximum:
                GT.attack = int(a)
                GT.constitution = int(c)
                GT.movement = int(m)
                self.currentGTs[GT.stage] -= 1 #decrement old stage counter
                GT.stage = nextStage
                self.currentGTs[GT.stage] += 1 #increment new stage counter
                #upgrade attack
                GT.weaponOptions[0] = Weapon("Bare Hand", "One", [("0", "Yes")], "No", 100, Effect("KILL {}".format(GT.attack)), EffectBag())
                GT.weaponOptions[0].heldBy = GT
                self.note(GT, "GREW TO", P(GT.stage))
            else:
                self.note(GT, "CANNOT GROW", P("MAXIMUM REACHED: {}".format(nextStage)))
            
    #assuming vaporised if no tokens for down stage
    def shrinkGT(self, GT):
        from .weaponEffect import Effect, EffectBag
        
        stages = {
            "Baby": "Egg",
            "Fragment": "Egg",
            "Adult": "Baby"
        }
        
        nextStage = stages.get(GT.stage, "Dead")
        
        #will decrement in any case
        self.currentGTs[GT.stage] -= 1
        
        if nextStage == "Dead":
            GT.die(self)
            return

        #Get traits for organism
        a, c, m, stageMaximum = self.GTAttributes[nextStage]
        if self.currentGTs[nextStage] >= stageMaximum:
            GT.die(self)
            return
        
        self.currentGTs[nextStage] += 1
        
        a, c, m, stageMaximum = self.GTAttributes[nextStage]
        GT.attack = int(a)
        GT.constitution = int(c)
        GT.movement = int(m)
        GT.stage = nextStage
        GT.weaponOptions[0] = Weapon("Bare Hand", "One", [("0", "Yes")], "No", 100, Effect("KILL {}".format(GT.attack)), EffectBag())
        GT.weaponOptions[0].heldBy = GT
        
    def createGT(self, stage):
        from .organism import Organism
        GT = None
        a, c, m, stageMaximum = self.GTAttributes[stage]
        if self.currentGTs[stage] < stageMaximum:
            GT = Organism("GT {}".format(self.GTNameCounter), a, c, m, stage)
            self.currentGTs[GT.stage] = int(self.currentGTs[GT.stage]) + 1
            self.gt.append(GT)
            self.GTNameCounter += 1
            self.note(GT, "CREATED AT", P(GT.stage))
        else:
            self.note(P(stage),"CANNOT CREATE", P("MAXIMUM REACHED"))
        return GT
    
    def launchShip(self, organism, LAUNCH_CHANCE = 0):
        if organism.currentRoom.name in ["Scout Bay", "Saucer Bay", "Cockboat Bay"] and not organism.currentRoom.alreadyLaunched:
            if LAUNCH_CHANCE >= randrange(0, 100) + 1:
                from .room import Room
                shipCapacity = {
                  "Scout Bay": 2,
                  "Saucer Bay": 4,
                  "Cockboat Bay": 1000
                }.get(organism.currentRoom.name)
                #create ship
                ship = Room(organism.currentRoom.name[0:organism.currentRoom.name.find(" ")])
                self.note(organism, "INITIATED LAUNCH", ship)
                organism.currentRoom.alreadyLaunched = True
                loadedCrew = 0
                for o in sample(organism.currentRoom.organisms, len(organism.currentRoom.organisms)):
                    if o.name[0:2] != "GT" and o.isAlive:
                        self.note(o, "BOARDED", ship)
                        ship.enterRoom(o)
                        o.isAlive = False #revived during epilogue
                        o.canAttack = False
                        loadedCrew += 1
                        if loadedCrew >= shipCapacity:
                            break
                self.escapingShips.append(ship)
                
    def launchShip_smart(self, organism):
        if organism.currentRoom.name in ["Scout Bay", "Saucer Bay", "Cockboat Bay"] and not organism.currentRoom.alreadyLaunched:
            from .room import Room
            shipCapacity = {
              "Scout Bay": 2,
              "Saucer Bay": 4,
              "Cockboat Bay": 22
            }.get(organism.currentRoom.name)
            if len(organism.currentRoom.getCrew()) >= min(shipCapacity, len(GameMaster.getAlive(self.crew))) / 5:
                #create ship
                ship = Room(organism.currentRoom.name[0:organism.currentRoom.name.find(" ")])
                self.note(organism, "INITIATED LAUNCH", ship)
                organism.currentRoom.alreadyLaunched = True
                loadedCrew = 0
                for o in sorted(organism.currentRoom.getCrew(), key = lambda a: -a.constitution):
                    if o.isAlive:
                        self.note(o, "BOARDED", ship)
                        ship.enterRoom(o)
                        o.isAlive = False #revived during epilogue
                        o.canAttack = False
                        loadedCrew += 1
                        if loadedCrew >= shipCapacity:
                            break
                self.escapingShips.append(ship)

    def outmatch(self):
        om = 0
        aliveCrew = GameMaster.getAlive(self.crew)
        for member in aliveCrew:
            om += member.outmatchedSur_num()
        return om / len(aliveCrew)

    def shipDetonation_smart(self, aliveCrew, OUTMATCHED_THRESHOLD = 0.8):
        if self.detonation:
            return #already triggererd
        if len(aliveCrew) == 0:
            return
        om = self.outmatch()
        
        for organism in aliveCrew:
            if not organism.isAlive:
                continue
            #if person who can detonate ship
            if organism.name in ["Captain Yid", "First Officer", "Engineering Officer", "Pilot 1", "Pilot 2"]:
                if organism.currentRoom.name in ["Bridge 1", "Bridge 2"]:
                    #name and room match up, chance of actually activating
                    if OUTMATCHED_THRESHOLD >= om:
                        self.note(organism, "ACTIVATED SELF DESTRUCT", organism.currentRoom)
                        self.detonation = True
                        organism.canMove = False
                        organism.canAttack = False
                        return True
        return False

    def shipDetonation(self, organism, DETONATION_CHANCE = 0):
        if self.detonation:
            return #already triggererd
        
        if organism.isAlive:
            #if person who can detonate ship
            if organism.name in ["Captain Yid", "First Officer", "Engineering Officer", "Pilot 1", "Pilot 2"]:
                if organism.currentRoom.name in ["Bridge 1", "Bridge 2"]:
                    #name and room match up, chance of actually activating
                    if DETONATION_CHANCE >= randrange(0, 100) + 1:
                        self.note(organism, "ACTIVATED SELF DESTRUCT", organism.currentRoom)
                        self.detonation = True
                        organism.canMove = False
                        organism.canAttack = False
      
    #accpetableDanger: lower = more dangerous, 0 = suicidal
    def moveOrganism_smart(self, organism, acceptableDanger = 0.01):
        #Move Break Conditions
        if organism.currentRoom == None or len(organism.currentRoom.connectedRooms) == 0:
            return #organism is on escaped ship
        
        if organism.stun > 0:
            self.note(organism, "CANNOT MOVE", P("STUNNED"))
            return
        
        if not organism.canMove:
            self.note(organism, "CANNOT MOVE", P("VARIABLE TRIGGERED"))
            return

        if not organism.isAlive:
            self.note(organism, "CANNOT MOVE", P("DEAD"))
            return
        
        def roomDamage(o, room):
            enemyAtk = 0
            for o in room.organisms:
                if o.isGT():
                    enemyAtk += o.attack
            return (enemyAtk / 2) + 1
        
        def compareRoom(room1, room2):
            return room1.name == room2.name
        
        def mover(organism):
            rooms = []
            #get ally-enemy values for surrounding rooms
            for room in organism.currentRoom.connectedRooms:
                ally = organism.countAlly(room)
                enemy = organism.countEnemy(room)
                num = 0
                #if ally + enemy > 0:
                #    num = ally / (ally + enemy)
                rooms.append((roomDamage(organism, room), room))
            #parse lowest to highest
            if len(rooms) > 0:
                acceptableRooms = list(filter(lambda a: a[0] <= organism.constitution, rooms))
                #acceptableRooms = list(filter(lambda a: a[0] >= acceptableDanger, rooms))
                if len(acceptableRooms) <= 1:
                    #use the best worst case
                    tup = sorted(rooms, key= lambda comp: comp[0])[0]
                    tup[1].enterRoom(organism)
                    #entered a new room
                    self.note(organism, "MOVING WORST CASE ({})".format(tup[0]), organism.currentRoom)
                else:
                    #randomly enter one of the accpetable rooms
                    acceptableRooms[randrange(0, len(acceptableRooms))][1].enterRoom(organism)
                    self.note(organism, "MOVING ACCEPTABLE", organism.currentRoom)
                

        startingRoom = organism.currentRoom
        cmpr = lambda a : compareRoom(startingRoom, a)
        #Move
        for movementIteration in range(0, organism.movement):
            mover(organism)
            if cmpr(organism.currentRoom):
                self.note(organism, "STAYING", organism.currentRoom)
                continue
            
            #check for fence halt
            if organism.currentRoom.containsActiveFence():
                self.note(organism, "ENCOUNTERED FENCE", organism.currentRoom)
                #add effect to GT
                if organism.isGT():
                    fence = organism.currentRoom.getFence()
                    if fence != None:
                        organism.addDamage(organism.currentRoom, fence, fence.weaponEffect)
                return
            #check for GT halt
            if not organism.isGT():
                for o in organism.currentRoom.organisms:
                    if o.stage in ["Baby", "Adult"]:
                        organism.mustAttackCurrentRoom = True
                        self.note(organism, "ENCOUNTERED ENEMY", organism.currentRoom)
                        return #no more movement can be used
    
    def moveOrganism(self, organism):
        #Move Break Conditions
        if organism.currentRoom == None or len(organism.currentRoom.connectedRooms) == 0:
            return #organism is on escaped ship
        
        if organism.stun > 0:
            self.note(organism, "CANNOT MOVE", P("STUNNED"))
            return
        
        if not organism.canMove:
            self.note(organism, "CANNOT MOVE", P("VARIABLE TRIGGERED"))
            return

        if not organism.isAlive:
            self.note(organism, "CANNOT MOVE", P("DEAD"))
            return
            

        #Move
        timesMoved = 0
        
        while timesMoved < organism.movement:
            timesMoved += 1
            #pick a room from any connected room (existing room included)
            oldRoom = organism.currentRoom
            
            newRoom = oldRoom.connectedRooms[randrange(0, len(oldRoom.connectedRooms))]
            newRoom.enterRoom(organism)
            
            if newRoom.name == oldRoom.name:
                self.note(organism, "STAYING", newRoom)
            else:
                self.note(organism, "MOVING", newRoom)
                
            #crew conditions
            if organism.name[0:2] != "GT": #is a crew member
                #fence
                mustStop = False
                for w in organism.currentRoom.pickups:
                    if w.name == "Fence" and w.fenceActive:
                        mustStop == True
                
                #GT in room
                if organism.currentRoom.countGT() > 0:
                    for o in organism.currentRoom.organisms:
                        if o.stage in ["Baby", "Adult"]:
                            organism.mustAttackCurrentRoom = True
                            self.note(organism, "ENCOUNTERED ENEMY", organism.currentRoom)
                            #print("{} encountered {} Green Things!".format(organism.name, organism.currentRoom.countGT()))
                            mustStop = True
                if mustStop:
                    break
            else: #GT conditions
                fence = None
                for w in organism.currentRoom.pickups:
                    if w.name == "Fence":
                        fence = w
                        break
                if fence != None and fence.fenceActive: #GT needs to stop
                    organism.addDamage(organism.currentRoom, fence, fence.weaponEffect)
                    organism.mustAttackCurrentRoom = True
                
                
    def dumbAttack(self, organism):
        
        if not organism.canAttack:
            self.note(organism, "CANNOT ATTACK", P("VARIABLE TRIGGERED"))
            return
        
        if organism.stun > 0:
            self.note(organism, "CANNOT ATTACK", P("STUNNED"))
            return
        
        if not organism.isAlive:
            self.note(organism, "CANNOT ATTACK", P("DEAD"))
            return

        tree = organism.getAttackTree()
            
        weapon, attackTree = tree[randrange(0, len(tree))]
        rooms, reusable, targetType = attackTree[randrange(0, len(attackTree))]
            
        room, targets, collateral = rooms[0]
        if not organism.mustAttackCurrentRoom:
            #get at least 1 target
            targetCount = len(targets)
            for r, t, c in rooms:
                if len(t) > targetCount:
                    room, targets, collateral, targetCount = r, t, c, len(t)
                        
            #room, targets, collateral = rooms[randrange(0, len(rooms))]
            
        if len(targets) > 0:
            self.note(organism, "TARGETING ROOM", room)
            weapon.dealDamage(self, organism, targets, collateral, reusable)
    
    def rollDice(dice):
        result = 0
        for _ in range(0, dice):
            result += randrange(1, 7)
        return result
    
    def resolveDamage(self, organism):
        if organism.isAlive:
            grows = 0
            shrinks = 0
            kills = 0
            fragments = 0
            stuns = 0
            for atk, weap, eff in organism.damageStack: #effect class, not effect
                damageType = eff.effect
                if damageType == None:
                    damageType = weap.getTemporary()
                    self.note(weap, "TEMPORARY", P(damageType))
                if damageType == "GROW":
                    grows += 1
                if damageType == "SHRINK":
                    shrinks += 1
                if damageType.find("KILL") >= 0:
                    kills += int(damageType[damageType.find(" "):].strip())
                if damageType == "FRAGMENT":
                    fragments += 1
                if damageType == "STUN":
                    stuns += 1
    
            counter = 0
            #Grow, Shrink
            if organism.name[0:2] == "GT":
                while organism.isAlive and counter < grows:
                    self.note(organism, "GROWING FROM", P(organism.stage))
                    counter += 1
                    self.growGT(organism)
                
                counter = 0
                while organism.isAlive and counter < shrinks:
                    self.note(organism, "SHRINKING FROM", P(organism.stage))
                    counter += 1
                    self.shrinkGT(organism)
                        
            #Kill
            rollTotal = GameMaster.rollDice(kills)
            if organism.isAlive and organism.constitution < rollTotal:
                #destroy organism
                self.note(organism, "KILLED BY DAMAGE DICE", P("{}/{}".format(rollTotal, organism.constitution)))
                organism.die(self)
                    
            #Fragment
            if organism.isAlive and fragments > 0:
                frags = GameMaster.rollDice(1)
                self.note(organism, "FRAGMENTING", P(frags))
                for _ in range(0, frags):
                    gt = self.createGT("Fragment")
                    if gt != None:
                        organism.currentRoom.enterRoom(gt)
                organism.die(self)
                
            #Stun
            s = GameMaster.rollDice(stuns * 5)
            if organism.isAlive and organism.constitution < s:
                self.note(organism, "STUNNED", P("{}/{}".format(s, organism.constitution)))
                organism.stun = 2
            #clear damage stack
            organism.damageStack = []
            
    def epilogue(self):
        #kill those left on ship
        if self.detonation:
            for room in self.rooms:
                for o in room.organisms:
                    if o.isAlive:
                        self.note(o, "KILLED", P("SELF DESTRUCT"))
                        o.die(self)
                    
        crewPoints = 0
        
        for ship in self.escapingShips:
            for c in ship.organisms:
                c.isAlive = True
            crewPoints += self.one(ship)
        return crewPoints
                
    def one(self, ship):
        if randrange(0, 2) == 0:
            self.note(ship, "HEADING FOR", P("Snudl-1"))
            return self.seven(ship)
        else:
            self.note(ship, "HEADING FOR", P("Last Planet"))
            return self.three(ship)
            
    def two(self, ship):
        if randrange(0, 2) == 0:
            return self.seven(ship)
        else:
            return self.eight(ship)
        
    def three(self, ship):
        if randrange(0, 3) < 2: #66%
            return self.four(ship)
        else:
            return self.six(ship)
        
    def four(self, ship):
        if randrange(0, 2) == 0:
            self.note(ship, "RAN FROM", P("HOSTILES"))
            return self.eight(ship)
        else:
            self.note(ship, "FIGHTING", P("HOSTILES"))
            return self.five(ship)
        
    def five(self, ship):
        hostileAttack = GameMaster.rollDice(GameMaster.rollDice(1))
        crewAttack = 0
        for c in ship.organisms:
            if c.isAlive:
                crewAttack += c.attack
        if crewAttack > hostileAttack:
            self.note(ship, "DEFEATED", P("HOSTILES"))
            return self.six(ship)
        else:
            alive = GameMaster.getAlive(ship.organisms)
            if len(alive) <= 1:
                #alive[0].die(self)
                self.note(ship, "PERISHED", P("ALL CREW DEAD"))
                return 0
            else:
                alive[randrange(0, len(alive))].die(self)
                return self.four(ship)
        
    def six(self, ship):
        if randrange(0, 3) < 2: #66%
            return self.two(ship)
        else:
            return self.twelve(ship)
        
    def seven(self, ship):
        if randrange(0, 2) == 0:
            return self.thirteen(ship)
        else:
            return self.fourteen(ship)
        
    def eight(self, ship):
        if randrange(0, 2) == 0:
            return self.nine(ship)
        else:
            return self.ten(ship)
        
    def nine(self, ship):
        if randrange(0, 2) == 0:
            return self.two(ship)
        else:
            return self.eleven(ship)
        
    def ten(self, ship):
        if randrange(0, 2) == 0:
            return self.eight(ship)
        else:
            return self.fifteen(ship)
        
    def eleven(self, ship):
        self.note(ship, "PERISHED", P("LOST"))
        return 0
        
    def twelve(self, ship):
        self.note(ship, "ARRIVED", P("Snudl-1"))
        totalCon = 0
        for o in GameMaster.getAlive(ship.organisms):
            totalCon += o.constitution
        return totalCon
        
    def thirteen(self, ship):
        if randrange(0, 2) == 0:
            return self.six(ship)
        else:
            return self.fifteen(ship)
        
    def fourteen(self, ship):
        if randrange(0, 2) == 0:
            self.note(ship, "HEADING FOR", P("Snudl-1"))
            return self.seven(ship)
        else:
            self.note(ship, "HEADING FOR", P("Last Planet"))
            return self.three(ship)
        
    def fifteen(self, ship):
        for c in GameMaster.getAlive(ship.organisms):
            if GameMaster.rollDice(4) >= c.constitution:
                c.die(self)
        if len(GameMaster.getAlive(ship.organisms)) == 0:
            self.note(ship, "PERISHED", P("DISEASE"))
            return 0
        else:
            if randrange(0, 2) == 0:
                return self.six(ship)
            else:
                return self.seven(ship)
