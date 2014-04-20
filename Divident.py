
import random
import rg

'''
Created April 19, 2014
Successor of Trident
Rather than selecting only three grid spaces to occupy, Divident can select a random amount between 3 and 6.
This traps and destroys enemies faster than Trident
It also uses new attack vectors that attempt to predict enemy attack locations
'''

class Robot:
    numberof = 3
    targets = [(9,9)]
    
    def __init__(self):
        global targets
        global numberof
        targets = [(9,9)]
        numberof = random.randint(3, 5)
        for i in range(0, numberof):
            i = i # Dead code
            targets.append((random.randint(7,11),random.randint(7,11)))
        print "Targets established: "
        print targets
        return
    
    def act(self, game):
        global targets
        route = random.randint(0, numberof)
        target = targets[route];
        
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) == 2:
                    attacking = rg.toward(self.location, loc)
                    number = self.badnearbylocale(attacking, game)
                    helpers = self.friendlynearbylocale(attacking, game)
                    if number == 2 & helpers > 0:
                        return ['move', attacking] # Probably going to die
                    else :
                        return ['attack', attacking] 
                if rg.dist(loc, self.location) == 1:
                    if self.badnearbylocale(self.location, game) > 1: # Surrounding by enemies? DIE!
                        if self.hp < 25:
                            return ['suicide']
                    else:
                        return ['attack', rg.toward(self.location, loc)]
        if self.location == target:
            return ['guard']
        return ['move', rg.toward(self.location, target)]
    
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
        