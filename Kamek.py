
import rg

'''
Created April 19, 2014

Successor of Divident and Ponies
Typically, my robots would 'preselect' a grid space to move towards and fill the grid space
    EX: ClusterBot (t=1), Trident (t=3), and Divident (t=random(3-6))
The only exception would be Ponies in which attackers went after the nearest enemy

Kamek is essentially a cross between all of those versions
It uses Divident's attack vectors + Ponies' filters to target enemies
However, it does predict enemy attack locations and adapts respondingly
'''
class Robot():
    
    def act (self, game):
        converge = self.weakest(game)
         
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) == 2:
                    attacking = rg.toward(self.location, loc)
                    number = self.badnearbylocale(attacking, game)
                    helpers = self.friendlynearbylocale(attacking, game)
                    if number == 2 and helpers > 0:
                        return ['move', attacking] # Probably going to die
                    else :
                        return ['attack', attacking] 
                if rg.dist(loc, self.location) == 1:
                        return ['attack', rg.toward(self.location, loc)]
        
        locs = []
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                locs.append(loc)
        
        return ['move', rg.toward(self.location, converge)]
    
    # Returns the location of the weakest enemy robot in the game
    def weakest(self, game):
        lowesthealth = 50
        nub = (9,9)
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                if lowesthealth > bot.hp:
                    lowesthealth = bot.hp
                    nub = loc
        return nub
    
    def friendlynearbylocale(self, locale, game):
        robots = 0
        for loc, bot in game.robots.iteritems():
            if bot.player_id == self.player_id:
                if rg.dist(loc, locale) <= 1:
                    robots = robots + 1
        return robots
    
    # How many robots are l
    def badnearbylocale(self, locale, game):
        robots = 0
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                if rg.dist(loc, locale) <= 1:
                    robots = robots + 1
        return robots
    
        