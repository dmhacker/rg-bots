
import rg

# Created April 19, 2014
# Sends all units after nearest robot in game that is isolated
# Then attacks and destroys the robot and on next move, searches for a new target
# Note that this class was a test form for detecting enemies
# It got revamped in Kamek
class Robot(object):
    converge = (9,9)
    
    def __init__(self):
        global converge
        converge = (9,9)
        
    def act (self, game):
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    if self.nearby(game) >= 2:
                        if self.hp < 16: # Robot is about to die
                            return ['suicide']
                        else:
                            return ['attack', loc]
                    else:
                        return ['attack', loc]
                
        global converge
        enemylocation = (9,9)
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
                
        converge = enemylocation
        return ['move', rg.toward(self.location, converge)]
    
    #How many robots are nearby?
    def nearby(self, game):
        robots = 0
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    robots = robots + 1
        return robots
    
