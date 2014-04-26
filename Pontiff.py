
import random
import rg

'''
Created April 20, 2014
Pontiff was originally intended to viciously attack enemies in the game ...
I guess that didn't work out.

Pontiff is the customary 'escape' bot.
It evaluates enemy and ally positions and tries to flee/attack accordingly
While it does work against robots like Suicidal (where planning is taken into consideration)
It fails against cluster-oriented robots like Bully and Kamek, both which end up grouping in large masses
'''
class Robot:
    
    def act(self, game):
        attacking = self.enemiesAround(game, self.location) 
        if len(attacking) > 1: # Multiple enemies are directly around us
            for attackpoint in attacking: 
                if (self.alliesAround(game, attackpoint) > 0):
                    return ['attack', attackpoint]
            if (self.canFlee(game, attacking)): # We can flee so let's gfto
                tryFlee = self.flee(game, attacking)
                if tryFlee == self.location:
                    return ['suicide']# ['attack',rg.toward(self.location, attacking[random.randint(0, len(attacking))])]
                else:
                    return ['move', tryFlee]
        elif len(attacking) == 1:
            if (self.canFlee(game, attacking)):
                return ['move', self.flee(game, attacking)]
            else:
                forceFlea = self.forceFlee(game, attacking)
                if forceFlea != self.location:
                    return ['move', forceFlea]
                else:
                    return ['attack',rg.toward(self.location, attacking[0])]
        enemies = self.possibleEnemiesAround(game, self.location)
        if len(enemies) > 1:
            if (self.canFlee(game, enemies)):
                return ['move', self.flee(game, enemies)]
            else:
                return ['attack',rg.toward(self.location, enemies[random.randint(0, len(enemies) - 1)])]
        elif len(enemies) == 1:
            if (self.canFlee(game, attacking)):
                return ['move', self.flee(game, attacking)]
            else:
                return ['attack',rg.toward(self.location, enemies[0])]
        trymove = self.nextStepNearest(game)
        if trymove == self.location:
            return ['guard']
        return ['move', trymove]
    
    def possibleEnemiesAround(self, game, boxedLoc):
        locs = []
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                if rg.wdist(boxedLoc, loc) == 2:
                    locs.append(loc)
        return locs
    
    def enemiesAround(self, game, boxedLoc):
        locs = []
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                if rg.wdist(boxedLoc, loc) == 1:
                    locs.append(loc)
        return locs
    
    def possibleAlliesAround(self, game, boxedLoc):
        locs = []
        for loc, bot in game.robots.iteritems():
            if bot.player_id == self.player_id:
                if rg.wdist(boxedLoc, loc) == 2:
                    locs.append(loc)
        return locs
    
    def alliesAround(self, game, boxedLoc):
        locs = []
        for loc, bot in game.robots.iteritems():
            if bot.player_id == self.player_id:
                if rg.wdist(boxedLoc, loc) == 1:
                    locs.append(loc)
        return locs
    
    def botsAround(self, game, boxedLoc):
        locs = []
        for loc, bot in game.robots.iteritems():
            bot = bot # Dead code
            if rg.wdist(boxedLoc, loc) == 1:
                locs.append(loc)
        return locs
    
    def randomMove(self):
        locs = rg.locs_around(self.location, filter_out=('invalid','obstacle','spawn'))
        if len(locs) == 0:
            return self.location
        pick = random.randint(0, len(locs) - 1)
        return locs[pick]
    
   
    def nextStepNearest(self, game): # Location in path to nearest enemy
        enemylocation = self.location
        distance = 0
        
        locs = []
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                locs.append(loc)
        
        for loc in locs:
            dist = rg.dist(loc, self.location)
            if dist > distance:
                distance = dist
                enemylocation = loc
        return rg.toward(self.location, enemylocation)
    
    def canFlee(self, game, enemies):
        pathout = False
        locs = rg.locs_around(self.location, filter_out=('invalid','obstacle','spawn'))
        for loc in locs:
            if self.isEmptySpace(game, loc) == True and len(self.enemiesAround(game, loc)) == 0:
                pathout = True
        return pathout;
    
    def isEmptySpace(self, game, moveTo):
        isEmpty = True
        for loc, bot in game.robots.iteritems():
            bot = bot # Dead code
            if moveTo == loc:
                isEmpty = False
        return isEmpty
    
    def flee(self, game, enemies):
        locs = rg.locs_around(self.location, filter_out=('invalid','obstacle','spawn'))
        target = self.location
        for loc in locs:
            if self.isEmptySpace(game, loc) == True and len(self.enemiesAround(game, loc)) == 0:
                target = loc
        return target
    
    def forceFlee(self, game, enemies):
        locs = rg.locs_around(self.location, filter_out=('invalid','obstacle','spawn'))
        target = self.location
        for loc in locs:
            if self.isEmptySpace(game, loc) == True:
                target = loc
        return target
    

        