import rg
import random

'''
Created April 20, 2014

Plat1.0/Plat10 (short for Platoon v1.0) is the first edition in my 'Plat' series
Platoon robots are initially divided into 5 different platoons that target robots within their range
Plat1.0 correctly implements the grouping methods and order layout with a strong attack vector
It has proven to beat former bots like Ponies and Divident with 100% efficiency.
With that said, I think it's ready for the battlefield.

NOTE: The Platoon series is nice, but not good because it splits bots up into inefficient teams.
I plan on using these attack vectors in a more unified approach (since flee now correctly assesses where to go and plans attacks accordingly)
'''
class Robot:
    turn_count = -1
    platoons = []
    platoon_amount = 0
    move_queue = []
    attack_queue = [] # Currently unused
    
    def __init__(self):
        self.platoon_amount = random.randint(4,7)
        for i in range(0, self.platoon_amount):
            self.platoons.append(Platoon(i, self))
        return
    
    def act(self, game):
        if len(self.enemies(game)) == 0:
            return ['guard']
        if self.turn_count is not game['turn']:
            self.turn_count = game['turn']
            self.faux_id = 0
            self.move_queue = []
        myrobots = self.bots(game)
        for platattack in self.platoons:
            platattack.clear()
        for bot in myrobots: 
            robid = bot.robot_id
            assigned = self.platoons[robid % self.platoon_amount]
            assigned.add(bot)
        current = game.robots[self.location]
        platoony = self.platoon(current)
        direct = platoony.directive(current, self.location, game)
        if direct[0] is 'move':
            self.move_queue.append(direct[1])
            if direct[1] == self.location:
                return ['move',rg.toward(self.location, (random.randint(7,11), random.randint(7,11)))]
        return direct
    
    def bots(self, game):
        robots = []
        for loc, bot in game.robots.iteritems():
            loc = loc
            if bot.player_id is self.player_id:
                robots.append(bot)
        return robots
    
    def enemies(self, game):
        robots = []
        for loc, bot in game.robots.iteritems():
            loc = loc
            if bot.player_id is not self.player_id:
                robots.append(bot)
        return robots
    
    def platoon(self, bot):
        for plat in self.platoons:
            for worker in plat.all():
                if worker is bot:
                    return plat
    
class Platoon:
    id = -1
    turn_count = -1
    all_bots = {}
    bots = []
    targetbot = {}
    base = None
    
    def __init__(self, iderp, baseRobot):
        self.id = iderp
        self.base = baseRobot
        return
    
    def all(self):
        return self.bots
    
    def add(self, robot):
        self.bots.append(robot)
        return
    
    def botIds(self):
        ids = []
        for bot in self.bots:
            ids.append(bot.robot_id)
        return ids
    
    def clear(self):
        self.bots = []
        return
    
    def averageLocation(self):
        targetloc = [0,0]
        for bot in self.bots:
            [x,y] = bot.location;
            targetloc[0] += x
            targetloc[1] += y
        ax = targetloc[0] / len(self.bots)
        ay = targetloc[1] / len(self.bots)
        return (ax, ay)
    
    # Get first robot on the platoon and check for id
    def playerid(self):
        return self.bots[0].player_id
    
    def target(self, game):
        enemies = self.enemies(game)
        nearest = self.findNearest(enemies, self.averageLocation())
        if nearest == None:
            self.targetbot = {}
            return
        self.targetbot = nearest
        return
    
    def findNearest(self, bots, loc):
        if len(bots) == 0:
            return None
        nearest = bots[random.randint(0, len(bots) - 1)]
        dist = rg.settings.board_size ** 2
        for bot in bots:
            newdist = rg.wdist(bot.location, loc)
            if newdist < dist:
                dist = newdist
                nearest = bot
        return nearest
    
    def enemies(self, game):
        robots = []
        for loc, bot in game.robots.iteritems():
            loc = loc
            if bot.player_id is not self.playerid():
                robots.append(bot)
        return robots
    
    def update(self, game):
        self.all_bots = {}
        for loc, bot in game.robots.iteritems():
            self.all_bots[loc] =  bot
        return
    
    def directive(self, currentBot, currentLocation, game):
        turn = game['turn']
        if turn is not self.turn_count:
            self.target(game)
            self.turn_count = turn
            print "\n Platoon "+str(self.id)+" contains bots: "+str(self.botIds())
            print " Established directive :"
            print self.targetbot
        self.update(game)
        
        if self.nearbyAllies(currentLocation, 1) == 4:
            return ['guard']
        
        result = self.action(currentBot, currentLocation, game)
        if result is not None:
            return result
        
        targetting = self.targetbot
        if targetting is {} or targetting is None:
            return ['guard']
        return ['move', rg.toward(currentLocation, targetting.location)]
    
    # Calculates suicide net damage
    def expectedSuicideDmg(self, currentLocation):
        return len(self.nearbyEnemies(currentLocation)) * 10
    
    def action(self, currentBot, currentLocation, game):
        if self.isSpawn(currentLocation): # We're at spawn, let's gtfo
            return ['move',self.panic(currentLocation)]
        
        enemies = self.nearbyEnemies(currentLocation) # Enemies directly around bot
        # print " Current ["+str(currentBot.robot_id)+"] surrounded by "+str(len(enemies))+" enemies"
        if len(enemies) > 1: # Surrounded by 2 or more enemies
            if len(enemies) == 4: # BY 4! JESUS!
                print "\n Goodbye world, I hope to do: "+str(self.expectedSuicideDmg(currentLocation))+" damage!"
                return ['suicide'] # Net damage should be great
            return self.safeMove(currentLocation) # Else, let's flee
        elif len(enemies) == 1:
            target = enemies[0] # Only enemy
            allies = self.nearbyAllies(target.location)
            allies.remove(currentBot)
            ally_amount = len(allies)
            # print " Current ["+str(currentBot.robot_id)+"] surrounded by "+str(len(allies))+" allies"
            # print "    Allies:",allies\n
            if ally_amount == 0:
                if currentBot.hp > 10:
                    return ['attack', target.location]
                return self.safeMove(currentLocation)
            elif ally_amount > 0:
                if target.hp > (self.netHP(allies) + currentBot.hp):
                    return self.safeMove(currentLocation)
                elif currentBot.hp < 10:
                    return self.safeMove(currentLocation)
                else:
                    return ['attack', target.location] # Never mind, we found a buddy, ATTACCKKK!
        else:
            possibleEnemies = self.nearbyEnemies(currentLocation, 2, True) # Enemies 2 spaces away
            if len(possibleEnemies) == 1: # Found one, attack it
                onlyenemy = possibleEnemies[0]
                return ['attack', rg.toward(currentLocation, onlyenemy.location)]
            elif len(possibleEnemies) > 1: 
                if len(possibleEnemies) == 3: # Multiple, flee with escape route     
                    return self.safeMove(currentLocation)
                else: # Attack towards one of them
                    return ['attack', rg.toward(currentLocation, possibleEnemies[0].location)]
        return None
    
    def danger(self, locs):
        danger_dict = {}
        for loc in locs:
            danger = 5
            if self.isEmptySpace(loc) is False:
                danger += 100000
            if self.isSpawn(loc):
                danger += 10000
            if loc in self.base.move_queue:
                danger += 9000
            if len(self.nearbyEnemies(loc, 1)) > 0:
                danger += 1000
            if len(self.nearbyEnemies(loc, 2)) > 0:
                danger += 500
            if len(self.nearbyEnemies(loc, 3)) > 0:
                danger += 10
            if len(self.nearbyAllies(loc, 1)) > 0:
                danger -= 100
            if len(self.nearbyAllies(loc, 2)) > 0:
                danger -= 20
            danger_dict[loc] = danger
        # print "\n Location-danger: ",danger_dict
        return danger_dict
    
    def safeMove(self, currLoc):
        safe = self.safest(currLoc)
        # print " Order locations:",safe
        if len(safe) == 0:
            fightordie = rg.locs_around(currLoc, filter_out=('invalid', 'obstacle'))
            return ['attack', fightordie[random.randint(len(fightordie - 1))]]
        safest = safe[0]
        # print " Found safest:",safest
        return ['move', safest]
        
    def safest(self, currLoc):
        locs = rg.locs_around(currLoc, filter_out=('invalid','obstacle'))
        danger_locs = self.danger(locs)
        least_danger = sorted(danger_locs, key=lambda loc : danger_locs[loc])
        return least_danger
    
    def panic(self, currLoc):
        locs = rg.locs_around(currLoc, filter_out=('invalid','obstacle','spawn'))
        target = currLoc
        for loc in locs:
            if self.isEmptySpace(loc) is True:
                target = loc
        return target
    
    def botAt(self, loc):
        for bloc, bot in self.all_bots.iteritems():
            if bloc is loc:
                return bot
    
    def isEmptySpace(self, moveTo):
        isEmpty = True
        for loc in self.all_bots.iterkeys():
            if moveTo == loc:
                isEmpty = False
        return isEmpty
    
    def nearbyEnemies(self, location, radius=1, borderonly=False):
        robots = []
        for loc, bot in self.all_bots.iteritems():
            if bot.player_id != self.playerid():
                if borderonly: 
                    if rg.wdist(loc, location) == radius:
                        robots.append(bot)
                else:
                    if rg.wdist(loc, location) <= radius:
                        robots.append(bot)
        return robots
    
    def nearbyAllies(self, location, radius = 1, borderonly=False):
        robots = []
        for loc, bot in self.all_bots.iteritems():
            if bot.player_id is self.playerid():
                if bot.location is not location:
                    if borderonly: 
                        if rg.wdist(loc, location) == radius:
                            robots.append(bot)
                    else:
                        if rg.wdist(loc, location) <= radius:
                            robots.append(bot)
        return robots
    
    def nearbyMembers(self, location, radius = 1, borderonly=False):
        robots = []
        for bot in self.bots:
            if bot.location is not location:
                if borderonly: 
                    if rg.wdist(bot.location, location) == radius:
                            robots.append(bot)
                else:
                    if rg.wdist(bot.location, location) <= radius:
                        robots.append(bot)
        return robots
    
    def netHP(self, bots):
        total = 0
        for bot in bots:
            total += bot.hp
        return total
    
    def nearestMember(self, location):
        selected = {}
        dist = 100
        for bot in self.bots:
            if rg.dist(bot.location, location) < dist:
                selected = bot
        return selected
    
    def isSpawn(self, loc):
        return loc in rg.settings.spawn_coords
        # return loc in [(7,1),(8,1),(9,1),(10,1),(11,1),(5,2),(6,2),(12,2),(13,2),(3,3),(4,3),(14,3),(15,3),(3,4),(15,4),(2,5),(16,5),(2,6),(16,6),(1,7),(17,7),(1,8),(17,8),(1,9),(17,9),(1,10),(17,10),(1,11),(17,11),(2,12),(16,12),(2,13),(16,13),(3,14),(15,14),(3,15),(4,15),(14,15),(15,15),(5,16),(6,16),(12,16),(13,16),(7,17),(8,17),(9,17),(10,17),(11,17)]
