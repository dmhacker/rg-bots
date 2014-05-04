import rg
import random

# Currently unused
def sqdist(p1, p2):
    return (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2

def corner(loc):
    return (abs(loc[0]-9), abs(loc[1]-9)) in [(2, 8), (4, 7), (6, 6), (7, 4)]

def deepCorner(loc):
    return (abs(loc[0]-9), abs(loc[1]-9)) == (6, 6)

'''
Created April 30, 2014

They call me Monsieur the Marquis.

Marquis is my first real attempt at good prediction. Its main strategy is to camp spawn locations.
It also implements dynamic move and attack queues to tell friendlies and enemies to avoid certain areas
Its best match against liquid 1.0 was: 38 - 48
Its best match against Plat10 was: 49 - 28

I plan to adapt some of these methods to future bots while improving Marquis' attack + danger evaluation

KNOWN BUGS/FUTURE IMPROVEMENTS: 
    - Returns to spawn after fleeing from it and is subsequently killed due to new spawns
'''
class Robot:
    id = 9000
    turn = -1
    all_bots = {} # All bots: {tuple,dict}
    ally_locs = [] # Allied bots: [tuple]
    enemy_locs = [] # Enemy bots: [tuple]
    safe_spawnpoints = [] # List of spawnpoints to go to: [tuple]
    move_queue = [] # List of taken moves: [tuple]
    moving_allies = [] # List of allied locs that are moving: [tuple]
    attack_queue = [] # List of attacked locs: [tuple]
    bump_queue = [] # The stored queue of bumped bots (think history): [tuple]
    urgent_queue = [] # Urgent locations that bots need to avoid
    bumped = [] # List of locs to be bumped: [tuple]
    urgent = [] # List of locs to be bumped with a priority above regular: [tuple]
    tillspawn = 10 # Credit to liquid 1.0 for this
    board_locs = [] # Cached board locations
    kill_me_now = []
    
    MIN_HEALTH = 15
    
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
        
        if curr in self.kill_me_now:
            self.kill_me_now.remove(curr)
            return ['suicide']
        
        if self.isTrapped(curr):
            if self.tillspawn == 1 and self.isSpawn(curr):
                return ['suicide']
            else:
                enemies = self.nearbyEnemies(curr)
                if corner(curr):
                    if self.canFightOut(curr):
                        weakest_arr = self.weakest(enemies)
                        if len(weakest_arr) == 0:
                            return self.safeMove(curr)
                        where_to_attack = weakest_arr[0]
                        self.attack_queue.append(where_to_attack)
                        return ['attack', where_to_attack]
                    else:
                        if len(enemies) * 15 > self.hp and len(enemies) > 1:
                            return ['suicide']
                        where_to_attack = self.bestAttack(curr)
                        self.attack_queue.append(where_to_attack)
                        return ['attack', where_to_attack]
                bump_me = self.unTrap(curr)
                if bump_me == None or self.empty(bump_me) == False:
                    if len(enemies) == 0:
                        return ['guard'] 
                    else:
                        where_to_attack = self.bestAttack(curr)
                        self.attack_queue.append(where_to_attack)
                        return ['attack', where_to_attack]
                    
        if curr in self.urgent_queue:
            action = self.safeMove(curr)
            if action[0] == 'guard':
                self.urgent.append(curr)
            return action
        
        if self.isSpawn(curr) and self.tillspawn == 9:
            
            if corner(curr):
                possible_trappers = self.nearbyEnemies(curr, radius=2, borderonly=True)
                if len(possible_trappers) > 1:
                    # Should never happen, because if it does, then the robot is trapped and will execute above code
                    where_to_attack = self.bestAttack(curr)
                    self.attack_queue.append(where_to_attack)
                    return ['attack', where_to_attack]
                elif len(possible_trappers) == 1:
                    can_escape = self.escapes(curr, possible_trappers[0])
                    if len(can_escape) > 0:
                        self.move_queue.append(can_escape[0])
                        self.moving_allies.append(curr)
                        return ['move', can_escape[0]] 
                    else:
                        where_to_attack = self.bestAttack(curr)
                        self.attack_queue.append(where_to_attack)
                        return ['attack', where_to_attack]
                
            fresh_start = self.toward(curr, rg.CENTER_POINT)
            if fresh_start == None:
                return ['guard']
            
            if self.isTrapped(fresh_start, with_spawn=True):
                if len(self.nearbyEnemies(fresh_start)) * 10 > self.botAt(curr)['hp']:
                    self.kill_me_now.append(fresh_start)
                    
            self.move_queue.append(fresh_start)
            self.moving_allies.append(curr)
            return ['move',fresh_start]
        
        direct = self.nearbyEnemies(curr)
        amount_direct = len(direct)
        if amount_direct == 1:
            only_enemy = direct[0]
            if self.isSpawn(only_enemy) and (self.tillspawn == 0 or self.tillspawn == 9):
                return ['attack', only_enemy]
            if self.botAt(curr)['hp'] < self.MIN_HEALTH and self.isSpawn(only_enemy) == False:
                return self.safeMove(curr)
            helpers = self.nearbyAllies(only_enemy)
            if len(helpers) > 0:
                total_hp = self.netHP(helpers)
                if (self.botAt(only_enemy)['hp'] >= total_hp):
                    return self.safeMove(curr)
            else:
                safest = self.safe(curr)
                if safest != None:
                    if safest not in rg.settings.spawn_coords and safest not in self.safe_spawnpoints:
                        return self.safeMove(curr)
            self.attack_queue.append(only_enemy)
            return ['attack',only_enemy]
        elif amount_direct > 1:
            if amount_direct == 4:
                return ['suicide']
            return self.safeMove(curr)
        
        possible = self.nearbyEnemies(curr, radius=2, borderonly=True)
        amount_possible = len(possible)
        if amount_possible == 1:
            if self.isCamping(curr):
                if corner(possible[0]):
                    guess = rg.toward(curr, possible[0])
                    self.attack_queue.append(guess)
                    return ['attack', guess]
            return self.safeMove(curr)
        elif amount_possible > 1:
            if self.isSpawn(curr) and self.tillspawn <= 2:
                return self.safeMove(curr)
            where_to_attack = self.bestAttack(curr)
            self.attack_queue.append(where_to_attack)
            return ['attack', where_to_attack]
        
        if curr in self.bump_queue:
            action = self.safeMove(curr)
            if action[0] == 'guard':
                self.bumped.append(curr)
            return action
       
        if self.nearbyAllies(curr) == 4:
            bump_me = self.untrap(curr)
            if bump_me not in self.moving_allies:
                self.move_queue.append(bump_me)
                self.moving_allies.append(curr)
                return ['move',bump_me]
            return ['guard']
        
        newly_spawned_enemies = filter(lambda x : corner(x), self.nearbyNewEnemySpawns(curr, 2))
        if len(newly_spawned_enemies) > 0:
            fu = self.toward(curr, sorted(newly_spawned_enemies, key=lambda x : rg.dist(curr, x))[0])
            if fu != None:
                self.move_queue.append(fu)
                self.moving_allies.append(curr)
            return ['move', fu]
        
        if self.isCamping(curr):
            attackloc = self.nearestSpawn(curr)
            self.attack_queue.append(attackloc)
            return ['attack',attackloc]
        
        return self.safeMove(curr)
    
    def update(self, game):
        if game['turn'] is not self.turn:
            self.turn = game['turn']
            self.tillspawn = (10 - (self.turn % 10)) % 10
            if self.turn > 90:
                self.tillspawn = 10
            del self.move_queue[:]
            del self.attack_queue[:]
            
            del self.moving_allies[:]
            
            del self.bump_queue[:]
            for bump_me in self.bumped:
                self.bump_queue.append(bump_me)
            del self.bumped[:]
            
            del self.urgent_queue[:]
            for gtfo in self.urgent:
                self.urgent_queue.append(gtfo)
            del self.urgent[:]
            
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
            if self.nearestSpawn(loc) != None:
                if self.tillspawn == 1:
                    danger += 500
            closest_spawn = self.closestSpawnpoint(loc)
            if closest_spawn != None:
                danger += ((rg.settings.board_size - rg.wdist(loc,  closest_spawn)) * (10 - self.tillspawn))
            danger += (rg.settings.board_size - rg.wdist(loc,  rg.CENTER_POINT))
            # It's okay if we move to the center
            if self.isSpawn(loc):
                danger += 499 * (10 - self.tillspawn)
            if loc in self.attack_queue:
                danger += 1000
            if deepCorner(loc):
                danger += 9000
            if len(self.nearbyEnemies(loc)) > 0:
                if len(self.nearbyEnemies(loc)) == 1 and self.botAt(self.nearbyEnemies(loc)[0]) > self.MIN_HEALTH:
                    danger += 200
                else:
                    danger += 500 * len(self.nearbyEnemies(loc))
            if len(self.nearbyEnemies(loc, 2, True)) > 0:
                danger += 250 + (10 * len(self.nearbyEnemies(loc, 2, True)))
            screw_me = len(self.nearbyAllies(loc))
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
                    if self.tillspawn != 1 and self.tillspawn != 0:
                        danger_dict[loc] = danger
                else:
                    danger_dict[loc] = danger
        return danger_dict
    
    # If good to attack, add to evaluation
    # Else if bad, subtract from it
    # Best location is one with highest evaluation
    def attack_eval(self, locs):
        attack_dict = {}
        for loc in locs:
            evaluation = 0
            evaluation += self.netHP(self.nearbyEnemies(loc))
            poss = self.botAt(loc)
            if poss != None and poss['player_id'] != self.player_id:
                evaluation += poss['hp'] * 100
            if loc in self.attack_queue:
                evaluation -= 10
            for adj in rg.locs_around(loc, filter_out=('invalid','obstacle')):
                if self.isInEnemyCluster(adj, 3):
                    evaluation += 10
            if loc not in self.ally_locs:
                attack_dict[loc] = evaluation
        return attack_dict
    
    def bestAttack(self, currLoc):
        locs = rg.locs_around(currLoc, filter_out=('invalid','obstacle'))
        attacks = self.attack_eval(locs)
        good = sorted(attacks, key=lambda loc : attacks[loc], reverse=True)
        assert len(good) != 0
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
    
    def safeMove(self, currLoc,appendme=True):
        safest = self.safe(currLoc)
        if safest == None:
            return ['guard']
        stupidity = self.stupidMove(currLoc, safest)
        if stupidity != 0:
            if stupidity == 1:
                if appendme:
                    attackloc = self.bestAttack(currLoc)
                    self.attack_queue.append(attackloc)
                return ['attack', attackloc]
            elif stupidity == 2:
                self.kill_me_now.append(safest)
            elif stupidity == 3:
                return ['suicide']
            elif stupidity == 4:
                if appendme:
                    self.attack_queue.append(safest)
                return ['attack', safest]
            return ['guard']
        if appendme:
            self.move_queue.append(safest)
            self.moving_allies.append(safest)
        return ['move',safest]
    
    # KEY:=
    # 0 = Move as normal
    # 1 = Attack weighted location
    # 2 = Move to safest and suicide
    # 3 = Suicide at location
    # 4 = Attack topos
    def stupidMove(self, frompos, topos):
        current_enemies = self.nearbyEnemies(frompos)
        direct_enemies = self.nearbyEnemies(topos)
        future_allies = self.nearbyAllies(topos, 2, True)
        
        if self.isSpawn(frompos) and self.tillspawn == 1:
            if self.isTrapped(topos, with_spawn=True):
                return 2
            if len(direct_enemies) > 1 and self.canFightOut(topos, True) == False:
                if corner(frompos):
                    return 3
                return 2
            if self.canFightOut(frompos) == False and self.canFightOut(topos, True):
                return 0
            elif self.canFightOut(frompos) == False and self.canFightOut(topos, True) == False:
                return 2
        
        if self.isSpawn(topos) and self.tillspawn == 1:
            return 1
        
        if len(direct_enemies) == 1 and self.botAt(direct_enemies[0])['hp'] > self.hp and len(future_allies) > 0:
            return 4
        
        if (len(current_enemies) == 3 or len(current_enemies) == 2) and len(direct_enemies) > 0:
            if len(future_allies) > 0:
                return 0
            else:
                if len(direct_enemies) * 15 > self.hp and self.hp > self.MIN_HEALTH:
                    return 2
                elif len(direct_enemies) < len(current_enemies):
                    return 3
                elif len(direct_enemies) == 1:
                    return 1
        return 0
    
    def canFightOut(self, currLoc, predicted=False):
        enemies = self.nearbyEnemies(currLoc)
        if len(enemies) == 0:
            return True
        weakest = self.weakest(enemies)[0]
        hits_to_kill_me = 50 / self.MIN_HEALTH
        if predicted:
            hits_to_kill_me = self.hitsToKill(currLoc) + len(self.nearbyEnemies(currLoc))
        else:
            hits_to_kill_me = self.hitsToKill(currLoc)
        weakest_hits = self.hitsToKill(weakest)
        if hits_to_kill_me <= weakest_hits:
            return False
        if self.isSpawn(currLoc) and weakest_hits <= self.tillspawn:
            return False
        return True
    
    def weakest(self, locs):
        return sorted(locs, key=lambda weak : self.botAt(weak)['hp'])
        
        
    def hitsToKill(self, loc):
        botat = self.botAt(loc)
        if botat == None:
            return 0
        health = botat['hp']
        hits = 0
        while health > 0:
            health -= self.MIN_HEALTH
            hits += 1
        return hits
    
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
    
    def nearbyAllies(self, location, radius=1, borderonly=False):
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
    
    def nearbyNewEnemySpawns(self, location, radius=1):
        spawns = []
        for loc,bot in self.all_bots.iteritems():
            if self.justSpawned(loc) and bot['player_id'] != self.player_id:
                spawns.append(loc)
        radius_spawns = [near_spawn for near_spawn in spawns if rg.wdist(location, near_spawn) <= radius]
        return radius_spawns
    
    #################### LOCATIONS ####################
    
    def botAt(self, loc):
        if loc in self.all_bots:
            return self.all_bots[loc]
        return None
    
    def nearestSpawn(self, location):
        aroundme = rg.locs_around(location, filter_out=('invalid', 'obstacle'))
        for a in aroundme:
            if a in rg.settings.spawn_coords:
                return a
    
    def isCamping(self, location):
        return location in self.safe_spawnpoints
    
    def isSpawn(self, loc):
        return loc in rg.settings.spawn_coords
    
            
    def closestSpawnpoint(self, loc, radius=rg.settings.board_size):
        spawn = None
        initial = radius
        for s in rg.settings.spawn_coords:
            if rg.dist(loc, s) <= initial:
                spawn = s
                initial = rg.dist(loc, s)
        return spawn
    
    def nearbySpawnpoints(self, loc, radius=1):
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
    
    def unTrap(self, loc):
        nearby = rg.locs_around(loc, filter_out=('invalid','obstacle'))
        for near in nearby:
            if near in self.ally_locs:
                self.urgent.append(near)
                return near
        return None
    
    def isInEnemyCluster(self, location, radius=3):
        locs = [loc for loc in self.board_locs if rg.wdist(location, loc) <= radius]
        enemies = [enemy for enemy in self.enemy_locs if rg.wdist(location, enemy) <= radius]
        if len(enemies) > (len(locs) / 2):
            return True
        return False
        
        
    def isTrapped(self, loc, with_spawn=False):
        trap = True
        nearby = []
        if with_spawn:
            nearby = rg.locs_around(loc, filter_out=('invalid','obstacle','spawn'))
        else:
            nearby = rg.locs_around(loc, filter_out=('invalid','obstacle'))
        for near in nearby:
            if near not in self.all_bots:
                trap = False
        return trap
    
    def nextToTrapped(self, loc):
        for around in rg.locs_around(loc, filter_out=('invalid','obstacle')):
            if self.isTrapped(around, with_spawn=True):
                return True
        return False
    
    def justSpawned(self, loc):
        return self.tillspawn == 9 and self.isSpawn(loc)
    
    def escapes(self, location, trapper_loc):
        around_me = rg.locs_around(location, filter_out=('invalid','obstacle'))
        attack_area = rg.toward(location, trapper_loc)
        if attack_area in around_me:
            around_me.remove(attack_area)
        return around_me

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
    
    def netHP(self, locs):
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
            