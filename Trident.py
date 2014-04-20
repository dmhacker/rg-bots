import random

import rg

# Created April 19, 2014
# Trident is a fork of my original robot, ClusterBot.
# While ClusterBot only picks one location to go to, Trident stores three randomized locations plus the center point
#
# This diversified approach has shown great results when fighting the conventional StandardBot
# However, when actually pitted against ClusterBot in consecutive rounds, it showed varied results
# This is my hypothesis as to why that occurred:
#     - ClusterBot's performance depends primarily on the location of its randomly selected point
#     - If an 'outlier' point [i.e (3,3)] its robots cannot effectly move to the position
#     - The enemy then destroys it
#     - Trident's mulitple target points however give its robots several 'fallback' options, each of which is randomly equal
#     - This is useful so that one stray point doesn't create a ripple effect on its performance
#     - Unfortunately, this divides its strength into separate groups which can be defeated by a unified bot cluster
class Robot:
    X = 7
    Y = 7
    XX = 8
    YY = 8
    XXX = 10
    XXX = 10
    # (9,9) is the grid's center object
    
    def __init__(self):
        global X
        global Y
        global XX
        global YY
        global XXX
        global YYY
        
        X = random.randint(7, 11) 
        Y = random.randint(7, 11)
        XX = random.randint(7, 11) 
        YY = random.randint(7, 11) 
        XXX = random.randint(7, 11) 
        YYY = random.randint(7, 11)  
        return
    
    def act(self, game):
        global X
        global Y
        global XX
        global YY
        global XXX
        global YYY
        randy = random.randint(0, 3)
        if (randy == 1):
            x = X
            y = Y
            for loc, bot in game.robots.iteritems():
                if bot.player_id != self.player_id:
                    if rg.dist(loc, self.location) <= 1:
                        return ['attack', loc]
            for loc, bot in game.robots.iteritems():
                if bot.player_id == self.player_id:
                    if rg.dist(loc, (x, y)) <= 1:
                        for otherloc, bot in game.robots.iteritems():
                            if (bot.player_id != self.player_id):
                                if (rg.dist(self.location, otherloc) <= 1):
                                    return ['attack', otherloc]
                if self.location == (x, y):
                    return ["guard"]
                return ["move", rg.toward(self.location, (x, y))]
        elif (randy == 2):
            x = XX
            y = YY
            for loc, bot in game.robots.iteritems():
                if bot.player_id != self.player_id:
                    if rg.dist(loc, self.location) <= 1:
                        return ['attack', loc]
            for loc, bot in game.robots.iteritems():
                if bot.player_id == self.player_id:
                    if rg.dist(loc, (x, y)) <= 1:
                        for otherloc, bot in game.robots.iteritems():
                            if (bot.player_id != self.player_id):
                                if (rg.dist(self.location, otherloc) <= 1):
                                    return ['attack', otherloc]
                if self.location == (x, y):
                    return ["guard"]
                return ["move", rg.toward(self.location, (x, y))]
        elif (randy == 3):
            x = XXX
            y = YYY
            for loc, bot in game.robots.iteritems():
                if bot.player_id != self.player_id:
                    if rg.dist(loc, self.location) <= 1:
                        return ['attack', loc]
            for loc, bot in game.robots.iteritems():
                if bot.player_id == self.player_id:
                    if rg.dist(loc, (x, y)) <= 1:
                        for otherloc, bot in game.robots.iteritems():
                            if (bot.player_id != self.player_id):
                                if (rg.dist(self.location, otherloc) <= 1):
                                    return ['attack', otherloc]
                if self.location == (x, y):
                    return ["guard"]
                return ["move", rg.toward(self.location, (x, y))]
        else: # Automatically go to center if random lands on a 0
            x = 9 
            y = 9
            for loc, bot in game.robots.iteritems():
                if bot.player_id != self.player_id:
                    if rg.dist(loc, self.location) <= 1:
                        return ['attack', loc]
            for loc, bot in game.robots.iteritems():
                if bot.player_id == self.player_id:
                    if rg.dist(loc, (x, y)) <= 1:
                        for otherloc, bot in game.robots.iteritems():
                            if (bot.player_id != self.player_id):
                                if (rg.dist(self.location, otherloc) <= 1):
                                    return ['attack', otherloc]
                if self.location == (x, y):
                    return ["guard"]
                return ["move", rg.toward(self.location, (x, y))]