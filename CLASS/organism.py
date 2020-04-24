from sys import stderr
from random import randrange
from .weapon import Weapon
from .weaponEffect import Effect, EffectBag
from .gamemaster import GameMaster
#inherits Weapon from Ship class

class Organism:
    
    def __init__(self, name, attack, constitution, movement, stage=""):
        self.name = name
        
        #STATS
        self.movement = int(movement)
        self.constitution = int(constitution)
        self.attack = int(attack)
        self.firstWeapon = True
        
        #GAMEPLAY FLAGS
        self.stage = stage #for GT
        self.isAlive = True
        self.stun = 0
        self.canMove = True
        self.mustAttackCurrentRoom = False
        self.canAttack = True
        
        #BARE HAND AND WEAPON LIST
        self.weaponOptions = []
        self.weaponOptions.append(Weapon("Bare Hand", "One", [("0", "Yes")], "No", 100, Effect("KILL {}".format(self.attack)), EffectBag()))
        self.weaponOptions[0].heldBy = self
        
        #TRACKERS        
        self.currentRoom = None
        self.damageStack = [] #[(attacker, weapon, effect), *]
        
    def lookForEscape(self, roomToCheck, riskingLife = False, previousRooms = [], currentDepth = 0):
        if roomToCheck.name in ["Scout Bay", "Saucer Bay", "Cockboat Bay"] and not roomToCheck.alreadyLaunched:
            return (currentDepth, [roomToCheck])
        if roomToCheck.name in previousRooms:
            return (100, [])
        if not riskingLife and (roomToCheck.hasHostileGT() or roomToCheck.containsActiveFence()):
            return (100, [])
        
        depth = 100
        roomTraversal = []
        for r in roomToCheck.connectedRooms:
            #print(r.name)
            returnedDepth, returnedTraversal = self.lookForEscape(r, riskingLife, previousRooms + [roomToCheck.name], currentDepth + 1)
            if returnedDepth < depth:
                depth = returnedDepth
                roomTraversal = [roomToCheck] + returnedTraversal
        return (depth, roomTraversal)
        
    def isGT(self):
        return self.name[0:2] == "GT"
        
    def findWeapon(self, weaponName):
        for w in self.weaponOptions:
            if w.name == weaponName:
                return w
        return None
    
    def outmatched(self):
        allies = self.countAlly()
        enemies = self.countEnemy()
        if allies + enemies == 0:
            return False
        return (enemies / (allies + enemies)) > 0.5
    
    def outmatchedSur(self):
        allies = self.countAllySur()
        enemies = self.countEnemySur()
        if allies + enemies == 0:
            return False
        return (enemies / (allies + enemies)) > 0.5
    
    def outmatchedSur_num(self):
        allies = self.countAllySur()
        enemies = self.countEnemySur()
        if allies + enemies == 0:
            return 0
        return enemies / (allies + enemies)
    
    def countAllySur(self):
        allies = 0
        for room in self.currentRoom.connectedRooms:
            allies += self.countAlly(room)
        return allies
        
    def countEnemySur(self):
        enemies = 0
        for room in self.currentRoom.connectedRooms:
            enemies += self.countEnemy(room)
        return enemies
    
    def countAlly(self, room = None):
        if room == None:
            room = self.currentRoom #a shame this can't be the default
        return {True: lambda: room.countGT, False : lambda : room.countCrew}[self.isGT()]()()
    
    def countEnemy(self, room = None):
        if room == None:
            room = self.currentRoom
        return {True: lambda: room.countCrew, False : lambda : room.countGT}[self.isGT()]()()
        
    def roundEnd(self):
        if self.isAlive:
            self.mustAttackCurrentRoom = False
            if self.stun > 0:
                self.stun -= 1
            self.canMove = True
            self.canAttack = True
        
    def addDamage(self, attacker, weaponName, effect):
        self.damageStack.append((attacker, weaponName, effect))#effect is the class, not the effect
        
    def getRoom(self):
        if self.currentRoom == None:
            stderr.write("{} was never assigned a room".format(self.name))
            exit
        return self.currentRoom
    
    def die(self, gm):
        from .gamemaster import P
        #one of the attacking GTs must eat the crew
        if self.name[0:2] != "GT":
            gts = []
            for attacker, _, _ in self.damageStack:
                if attacker.name[0:2] == "GT" and attacker.isAlive:
                    gts.append(attacker)
            
            if len(gts) > 0:
                devourer = gts[randrange(0, len(gts))]
                if self.name == "Robot":
                    effect = gm.weapons[0].getTemporary()
                    gm.note(devourer, "ATE ROBOT", P(effect))
                    if effect.find("KILL") >= 0:
                        dice = int(effect[effect.find(" "):].strip())
                        if devourer.constitution <= GameMaster.rollDice(dice):
                            devourer.die(gm)
                    if effect == "STUN":
                        if devourer.constitution < GameMaster.rollDice(5):
                            devourer.stun = 2
                    if effect == "GROW":
                        gm.growGT(devourer)
                    if effect == "SHRINK":
                        _ = gm.shrinkGT(devourer)
                    if effect == "FRAGMENT":
                        fragments = GameMaster.rollDice(1)
                        gm.note(devourer, "FRAGMENTED", P(fragments))
                        for _ in range(0, fragments):
                            gt = gm.createGT("Fragment")
                            if gt != None:
                                devourer.currentRoom.enterRoom(gt)
                else:
                    gm.note(devourer, "ATE", self)
                    gm.growGT(devourer)
        else:
            #decrement stage counter
            gm.currentGTs[self.stage] -= 1


        gm.note(self, "DIED IN", self.currentRoom)
        self.isAlive = False
        if len(self.weaponOptions) > 1:
            #item is returned to spawn rooms
            if self.weaponOptions[1].name in ["Bottle of Acid",
                                              "Rocket Fuel",
                                              "Gas Grenade",
                                              "Canister of Zgwortz"]:
                respawnRoom = self.weaponOptions[1].spawnLocations[randrange(0, len(self.weaponOptions[1].spawnLocations))]
                respawnRoom.pickups.append(self.weaponOptions[1])
                gm.note(self.weaponOptions[1], "RETURNED", respawnRoom)
            else:
                self.currentRoom.pickups.append(self.weaponOptions[1])
                gm.note(self.weaponOptions[1], "DROPPED", self.currentRoom)
                
            self.weaponOptions[1].heldBy = None
            self.weaponOptions = []
        
        if self.currentRoom != None:
            self.currentRoom.exitRoom(self)
        self.currentRoom = None
    
    def removeWeapon(self, weapon):
        for w in self.weaponOptions:
            if w.name == weapon.name:
                self.weaponOptions.remove(w)
    
    def giveWeapon(self, weapon):
        if weapon.heldBy != None:
            weapon.heldBy.removeWeapon(weapon)
        weapon.heldBy = self
        self.weaponOptions.append(weapon)
        
    def getAttackTree(self):
        weaponTree = []
        for w in self.weaponOptions:
            a = None
            a = w.getDamageTree(self)
            b = (w, a)
            weaponTree.append(b)
        return weaponTree
    
    def printAttackTree(tree):
        for w in tree:
            for t in w[1]:
                print(Weapon.printTree([t]))
    
    def attributes(self):
        stats = []
        stats.append("Name:\t{}".format(self.name))
        stats.append("Stage:\t{}".format(self.stage))
        stats.append("Mov:\t{}".format(self.movement))
        stats.append("Con:\t{}".format(self.constitution))
        stats.append("Atk:\t{}".format(self.attack))
        if self.currentRoom == None:
            stats.append("Room:\t{}".format("None"))
        else:
            stats.append("Room:\t{}".format(self.currentRoom.name))
        return stats
    
    def prettyPrint(self):
        for att in self.attributes():
            print(att)
        print()
    
    def __str__(self):
        s = ""
        for att in self.attributes():
            s += "{}\n".format(att)
        s += "\n"
        return s