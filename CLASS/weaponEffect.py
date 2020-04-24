#a canister that ensures all weapons of the same type have a synchronised effect
#this original class is still referenced by the weapon after the copy to crew
class Effect:
    def __init__(self, effect = None):
        self.effect = effect
        
class EffectBag:
    def __init__(self, chitBag = []):
        self.bag = chitBag
        
    def generatePermanent(self):
        from random import randrange
        index = randrange(0, len(self.bag))
        gen = self.bag[index]
        del self.bag[index]
        return gen.strip()
    
    def generateTemporary(self):
        from random import randrange
        return self.bag[randrange(0, len(self.bag) - 1)].strip()