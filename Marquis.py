
import rg
import random

'''
Created April 30, 2014

Marquis is my first real attempt at good prediction. Its main strategy is to camp spawn locations.
It also implements dynamic move and attack queues to tell friendlies and enemies to avoid certain areas
Its best match against liquid 1.0 was: 36 - 42

I plan to adapt some of these methods to future bots while improving Marquis' attack + danger evaluation
'''
class Robot:
    id = 9000
    turn = -1
    all_bots = {} # All bots: {tuple,dict}
    ally_locs = [] # Allied bots: [tuple]
    enemy_locs = [] # Enemy bots: [tuple]
    safe_spawnpoints = [] # List of spawnpoints to go to: [tuple]
    marked_spawnpoints = []
    move_queue = [] # List of taken moves: [tuple]
    moving_allies = [] # List of allied locs that are moving: [tuple]
    attack_queue = [] # List of attacked locs: [tuple]
    bump_queue = [] # The stored queue of bumped bots (think history): [tuple]
    bumped = [] # List of locs to be bumped: [tuple]
    tillspawn = 10 # Credit to liquid 1.0 for this
    board_locs = [] # Cached board locations
    
    def __init__(self):
        for spawn in rg.settings.spawn_coords:
            locs = rg.locs_around(spawn, filter_out=('invalid','obstacle','spawn'))
            for nearby in locs:
                self.safe_spawnpoints.append(nearby)
        self.board_locs = self.entireBoard()
                
    ################
    # MAIN METHOD! #
    ################
    def act(self, game):
        self.update(game)
        curr = self.location
        
        if self.isTrapped(curr):
            if self.tillspawn == 0 and self.isSpawn(curr):
                return ['suicide']
            else:
                bump_me = self.untrap(curr)
                if bump_me not in self.moving_allies:
                    if bump_me == None:
                        return ['guard']
                    self.move_queue.append(bump_me)
                    self.moving_allies.append(curr)
                    return ['move',bump_me]
                
        if self.isSpawn(curr):
            return self.flee(curr)
        
        # Enemies always take priority
        direct = self.nearbyEnemies(curr)
        amount_direct = len(direct)
        if amount_direct == 1:
            only_enemy = direct[0]
            if self.isSpawn(only_enemy) and self.tillspawn == 0:
                return ['attack', only_enemy]
            helpers = self.nearbyAllies(only_enemy)
            helpers.remove(curr)
            total_hp = self.nethp(helpers) + self.botAt(curr)['hp']
            if (self.botAt(only_enemy)['hp'] >= total_hp):
                return self.flee(curr)
            else:
                self.attack_queue.append(only_enemy)
                return ['attack',only_enemy]
        elif amount_direct > 1:
            if amount_direct == 4:
                return ['suicide']
            return self.flee(curr)
        
        possible = self.nearbyEnemies(curr, radius=2, borderonly=True)
        amount_possible = len(possible)
        if amount_possible == 1:
            return self.flee(curr)
        elif amount_possible > 1:
            if self.isSpawn(curr) and self.tillspawn <= 2:
                return self.flee(curr)
            where_to_attack = self.bestAttack(curr)
            # one_enemy = possible[random.randint(0, amount_possible - 1)]
            self.attack_queue.append(where_to_attack)
            return ['attack', rg.toward(curr, where_to_attack)]
        
        if curr in self.bump_queue:
            return self.flee(curr)
       
        if self.nearbyAllies(curr) == 4:
            bump_me = self.untrap(curr)
            if bump_me not in self.moving_allies:
                self.move_queue.append(bump_me)
                self.moving_allies.append(curr)
                return ['move',bump_me]
            return ['guard']
        
        if self.isCamping(curr):
            attackloc = self.nearestSpawn(curr)
            self.attack_queue.append(attackloc)
            return ['attack',attackloc]
        
        spawnMove = self.toward(curr, self.nearestCamp(curr))
        if spawnMove is None:
            return ['guard']
        self.move_queue.append(spawnMove)
        self.moving_allies.append(curr)
        return ['move',spawnMove]
    
    def update(self, game):
        if game['turn'] is not self.turn:
            self.turn = game['turn']
            self.tillspawn = (10 - (self.turn % 10)) % 10
            del self.move_queue[:]
            del self.attack_queue[:]
            
            del self.moving_allies[:]
            del self.bump_queue[:]
            for bump_me in self.bumped:
                self.bump_queue.append(bump_me)
            del self.bumped[:]
            del self.marked_spawnpoints[:]
            
        del self.ally_locs[:]
        del self.enemy_locs[:]   
        
        self.all_bots = game['robots']
        
        for loc, bot in self.all_bots.iteritems():
            if bot.player_id is self.id:
                self.ally_locs.append(loc) 
            else:
                self.enemy_locs.append(loc)
        return
    
    #################### PREDICTION ####################
    
    # If dangerous, add to danger
    # Else, subtract from danger
    # Best location is one with least danger
    def danger(self, locs):
        danger_dict = {}
        for loc in locs:
            danger = 0
            if self.isNearAnySpawnpoint(loc, 2):
                turn_til_spawn = self.turn % 10
                if turn_til_spawn == 9 or turn_til_spawn == 0:
                    turn_danger = turn_til_spawn
                    if turn_danger == 0:
                        turn_danger = 10
                    danger += 500 * (turn_danger + 1)
            if self.isSpawn(loc):
                danger += 9000
            if loc in self.attack_queue:
                danger += 5000
            if len(self.nearbyEnemies(loc)) > 0:
                danger += 500 * len(self.nearbyEnemies(loc))
            if len(self.nearbyEnemies(loc, 2, True)) > 0:
                danger += 250 + (10 * len(self.nearbyEnemies(loc, 2, True)))
            screw_me = len(self.nearbyAllies(loc, 1))
            if screw_me > 0:
                danger -= 25
            danger += screw_me * 25
            if len(self.nearbyAllies(loc, 2, True)) > 0:
                danger -= 75
            ally = self.nearestAlly(loc)
            if ally is not None: # Safety check
                danger += rg.wdist(loc, ally) * 5
            if self.empty(loc):
                if self.isSpawn(loc):
                    if (self.tillspawn <= 1) == False:
                        danger_dict[loc] = danger
                else:
                    count_me = True
                    for potential in self.nearbySpawnpoints(loc, radius=1):
                        if potential in self.ally_locs:
                            count_me = False
                    if count_me:
                        danger_dict[loc] = danger
        return danger_dict
    
    # TODO: Improve
    # If good to attack, add to evaluation
    # Else if bad, subtract from it
    # Best location is one with highest evaluation
    def attack_eval(self, locs):
        attack_dict = {}
        for loc in locs:
            evaluation = 0
            # Net HP of nearby enemies?
            adjacent_enemies = self.nearbyEnemies(loc)
            total_adj_hp = self.nethp(adjacent_enemies)
            evaluation += total_adj_hp
            if self.isSpawn(loc) and self.tillspawn <= 1:
                evaluation += 500
            if loc in self.attack_queue:
                evaluation -= 10
            if self.isInEnemyCluster(loc, 4):
                evaluation += 100
            for adj in rg.locs_around(loc, filter_out=('invalid','obstacle')):
                if self.isInEnemyCluster(adj, 3):
                    evaluation += 10
            attack_dict[loc] = evaluation
        return attack_dict
    
    def bestAttack(self, currLoc):
        locs = rg.locs_around(currLoc, filter_out=('invalid','obstacle'))
        attacks = self.attack_eval(locs)
        good = sorted(attacks, key=lambda loc : attacks[loc], reverse=True)
        if len(good) == 0:
            return None
        return good[0]
    
    def safe(self, currLoc):
        locs = rg.locs_around(currLoc, filter_out=('invalid','obstacle'))
        danger_locs = self.danger(locs)
        safe = sorted(danger_locs, key=lambda loc : danger_locs[loc])
        if len(safe) == 0:
            return None
        return safe[0]
    
    def safeOfGiven(self, allLocs):
        danger_locs = self.danger(allLocs)
        safe = sorted(danger_locs, key=lambda loc : danger_locs[loc])
        if len(safe) == 0:
            return None
        return safe[0]
    
    def flee(self, currLoc,appendme=True):
        safest = self.safe(currLoc)
        if safest == None:
            #print "\n Cannot find a safe location to flee to at:",currLoc
            return ['guard']
        if appendme:
            self.move_queue.append(safest)
            self.moving_allies.append(safest)
        return ['move',safest]
    
    #################### USEFUL ####################
    
    def empty(self, location):
        if location in self.move_queue:
            self.bumped.append(location)
            return False
        if location in self.all_bots and location not in self.moving_allies:
            self.bumped.append(location)
            return False
        return True
    
    def nearestAlly(self, location):
        targetting = self.enemy_locs
        selected = None
        least_dist = 1000
        for loc in targetting:
            dist = rg.wdist(location, loc)
            if dist < least_dist:
                selected = loc
                least_dist = dist
        return selected
    
    def nearestEnemy(self, location):
        targetting = self.enemy_locs
        selected = None
        least_dist = 1000
        for loc in targetting:
            dist = rg.wdist(location, loc)
            if dist < least_dist:
                selected = loc
                least_dist = dist
        return selected
    
    def nearbyEnemies(self, location, radius=1, borderonly=False):
        robots = []
        for loc, bot in self.all_bots.iteritems():
            if bot.player_id is not self.player_id:
                if borderonly: 
                    if rg.wdist(loc, location) == radius:
                        robots.append(loc)
                else:
                    if rg.wdist(loc, location) <= radius:
                        robots.append(loc)
        return robots
    
    def nearbyAllies(self, location, radius = 1, borderonly=False):
        robots = []
        for loc, bot in self.all_bots.iteritems():
            if bot.player_id is self.player_id:
                if bot.location is not location:
                    if borderonly: 
                        if rg.wdist(loc, location) == radius:
                            robots.append(loc)
                    else:
                        if rg.wdist(loc, location) <= radius:
                            robots.append(loc)
        return robots
    
    #################### LOCATIONS ####################
    
    def botAt(self, loc):
        return self.all_bots[loc]
    
    def nearestCamp(self, location):
        selected = rg.CENTER_POINT
        least_dist = rg.settings.board_size ** 2
        for loc in self.safe_spawnpoints:
            dist = rg.wdist(location, loc)
            if dist < least_dist: # and self.empty(location)
                selected = loc
                least_dist = dist
        return selected
    
    def nearestSpawn(self, location):
        aroundme = rg.locs_around(location, filter_out=('invalid', 'obstacle'))
        for a in aroundme:
            if a in rg.settings.spawn_coords:
                return a
    
    def isCamping(self, location):
        return location in self.safe_spawnpoints
    
    def isSpawn(self, loc):
        return loc in rg.settings.spawn_coords
    
            
    def closestSpawnpoint(self, loc, radius=4):
        spawn = None
        initial = radius
        for s in self.safe_spawnpoints:
            if rg.dist(loc, s) <= initial:
                spawn = s
                initial = rg.dist(loc, s)
        return spawn
    
    def nearbySpawnpoints(self, loc, radius=4):
        spawn = []
        for s in self.safe_spawnpoints:
            if rg.wdist(loc, s) <= radius:
                spawn.append(s)
        return spawn
    
    def isNearAnySpawnpoint(self, loc, radius=4):
        for s in self.safe_spawnpoints:
            if rg.wdist(loc, s) <= radius:
                return True
        return False
    
    def untrap(self, loc):
        nearby = rg.locs_around(loc, filter_out=('invalid','obstacle'))
        for near in nearby:
            if near in self.ally_locs:
                self.bumped.append(near)
                return near
        return None
    
    def isInEnemyCluster(self, location, radius=3):
        cluster = []
        locs = []
        for loc in self.board_locs:
            if rg.dist(loc, location) <= radius:
                locs.append(loc)
                if loc in self.enemy_locs:
                    cluster.append(loc)
        if len(cluster) > (len(locs) / 2):
            return True
        return False
        
        
    def isTrapped(self, loc):
        trap = True
        nearby = rg.locs_around(loc, filter_out=('invalid','obstacle'))
        for near in nearby:
            if near not in self.all_bots:
                trap = False
        return trap

    # I take no credit for this code! Credit goes to: Rage MK1
    # I only optimized it by adding in danger evaluation
    def toward(self, frompos, topos):
        if frompos == topos:
            return None

        dx = topos[0] - frompos[0]
        dy = topos[1] - frompos[1]
        dirs = []

        if dx and dy:
            dxn = dx/abs(dx)
            dyn = dy/abs(dy)
            if abs(dx) >= abs(dy):
                dirs = [(dxn, 0), (0, dyn)]
            else:
                dirs = [(0, dyn), (dxn, 0)]
            random.shuffle(dirs)
        elif dx:
            dxn = dx/abs(dx)
            dirs = [(0, -1), (0, 1)]
            random.shuffle(dirs)
            dirs = [(dxn, 0)] + dirs
        elif dy:
            dyn = dy/abs(dy)
            dirs = [(-1, 0), (1, 0)]
            random.shuffle(dirs)
            dirs = [(0, dyn)] + dirs
    
        posits = []
        for d in dirs:
            newpos = (frompos[0] + d[0], frompos[1] + d[1])
            if self.empty(newpos):
                posits.append(newpos)
        safest = self.safeOfGiven(posits)
        if safest is None:
            return None
        if 'normal' in rg.loc_types(safest):
            return safest
        return None 
    
    def nethp(self, locs):
        net = 0
        for loc in locs:
            bot = self.all_bots[loc]
            net += bot['hp']
        return net
    
    def entireBoard(self):
        board = []
        lmin = 0
        lmax = 18
        for x in range(lmin, lmax + 1):
            for y in range(lmin, lmax + 1):
                loc = (x,y)
                if 'normal' in rg.loc_types(loc) or 'spawn' in rg.loc_types(loc):
                    board.append((x,y))
        return board
            