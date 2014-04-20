import random

import rg

# Created April 18, 2014
# ClusterBot was derived from the typical "go-to-center" and attack robot
# It does however deviate from the conventional approach in several ways
#     - Goes to a random point of the grid originally defined to be the grid center
#     - Guards if close to destination, attacks surrounding robots
#     - If does not meet requirements, continues  moving to destination
class Robot:
    X = 9
    Y = 9
    # (9,9) is the grid's center object
    
    def __init__(self):
        global X
        global Y
        X = random.randint(3, 15) 
        Y = random.randint(3, 15) 
        return
    
    def act(self, game):
        global X
        global Y
        x = X
        y = Y
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    return ['attack', loc]
        for loc, bot in game.robots.iteritems():
            if bot.player_id == self.player_id:
                if rg.dist(loc, (x, y)) <= 1:
                    for otherloc, bot in game.robots.iteritems(): # Originally a suicide function but that turned out bad
                        if (bot.player_id != self.player_id):
                            if (rg.dist(self.location, otherloc) <= 1):
                                return ['attack', otherloc]
        if self.location == (x, y):
            return ["guard"]
        return ["move", rg.toward(self.location, (x, y))]
    
    