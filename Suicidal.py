
import random
import rg

'''
Born out of a code defect with Pontiff
The enemy nearby functions are screwed up but the robot functions better than Kamek (somehow?!)
'''
class Robot:
    
    def act(self, game):
        attacking = self.enemiesAround(game, self.location)
        if len(attacking) > 1:
            if (self.canFlee(game, attacking)):
                return ['move', self.flee(game, attacking)]
            else:
                return ['suicide']
        elif len(attacking) == 1:
            if (self.canFlee(game, attacking)):
                return ['move', self.flee(game, attacking)]
            else:
                return ['attack',rg.toward(self.location, attacking[0])]
        enemies = self.possibleEnemiesAround(game, self.location)
        if len(enemies) > 1:
            if (self.canFlee(game, enemies)):
                return ['move', self.flee(game, enemies)]
            else:
                return ['attack',rg.toward(self.location, enemies[random.randint(0, len(enemies) - 1)])]
        elif len(enemies) == 1:
            return ['attack',rg.toward(self.location, enemies[0])]
        trymove = self.randomMove()
        if trymove == self.location:
            return ['guard']
        return ['move', self.randomMove()]
    
    def possibleEnemiesAround(self, game, loc):
        locs = []
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                if rg.wdist(self.location, loc) == 2:
                    locs.append(loc)
        return locs
    
    def enemiesAround(self, game, loc):
        locs = []
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                if rg.wdist(self.location, loc) == 1:
                    locs.append(loc)
        return locs
        
    def randomMove(self):
        locs = rg.locs_around(self.location, filter_out=('invalid','obstacle','spawn'))
        if len(locs) == 0:
            return self.location
        pick = random.randint(0, len(locs) - 1)
        return locs[pick]
    
    def canFlee(self, game, enemies):
        locs = rg.locs_around(self.location, filter_out=('invalid','obstacle','spawn'))
        for loc in locs:
            if len(self.enemiesAround(game, loc)) == 0:
                return True;
        return False;
    
    def flee(self, game, enemies):
        locs = rg.locs_around(self.location, filter_out=('invalid','obstacle','spawn'))
        target = (9,9)
        for loc in locs:
            if len(self.enemiesAround(game, loc)) == 0:
                target = loc
        return target
        