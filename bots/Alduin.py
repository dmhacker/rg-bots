
import rg

def add_lists(list1, list2):
    tlist = []
    for i in list1:
        tlist.append(i)
    for i in list2:
        tlist.append(i)
    return tlist

def subtract_lists(list1, list2):
    tlist = []
    for i in list1:
        if i not in list2:
            tlist.append(i)
    return tlist

def spawn(loc):
    return 'spawn' in rg.loc_types(loc) or loc in rg.settings.spawn_coords

def nearest_spawn(loc):
    return sorted(rg.settings.spawn_coords, key=lambda x : rg.dist(loc, x))[0]

def corner(loc):
    return (abs(loc[0]-9), abs(loc[1]-9)) in [(2, 8), (4, 7), (6, 6), (7, 4)]

def around(loc, no_spawn=True):
    filter_out = ('invalid','obstacle')
    if no_spawn:
        filter_out = ('invalid','obstacle','spawn')
    return rg.locs_around(loc, filter_out)
        
def near_spawn(loc):
    near = around(loc)
    for n in near:
        if spawn(n):
            return True
    return False

def unmoveable_spawn(loc):
    if spawn(loc) == False:
        return False
    potent_around = around(loc)
    return len(potent_around) == 0
    

def deepCorner(loc):
    return (abs(loc[0]-9), abs(loc[1]-9)) == (6, 6)
    
'''

>>> ALDUIN <<<
==============
Version 2.1

Created on May 4, 2014

Best match against liquid10: 42 - 17 (v1.0)
Best match against CuteLilPlasma: 43 - 2 (v2.1)
'''
class Robot:
    turn_counter = -1
    taken = []
    moving = []
    friendlies_attacking = {}
    hunts = {}
    
    def act(self, game):
        robots = game['robots']
        turn = game['turn']
        curr = self.location
        tillspawn = (10 - (turn % 10)) % 10
        if turn > 90:
            tillspawn = 10
        ally_locs = add_lists(subtract_lists([rloc for rloc in robots.keys() if robots[rloc].player_id == self.player_id], self.moving), self.taken)
        enemy_locs = [rloc for rloc in robots.keys() if robots[rloc].player_id != self.player_id]
        
        if self.turn_counter != turn:
            self.turn_counter = turn
            self.taken = []
            self.moving = []
            #self.gtfo = []
            self.friendlies_attacking = {}
            self.hunts = {}
            for en in enemy_locs:
                self.hunts[en] = 0
        
            
        def nearby_enemies(loc, radius):
            return [rloc for rloc in enemy_locs if rg.wdist(loc, rloc) == radius]
        
        def nearby_allies(loc, radius):
            return [rloc for rloc in ally_locs if rg.wdist(loc, rloc) == radius]
        
        def closest_enemy(loc):
            closest = sorted(sorted(enemy_locs, key=lambda l :rg.wdist(loc, l)), key=lambda x : robots[x]['hp'])
            return closest[0]
        
        def closest_ally(loc):
            closest = sorted(sorted(ally_locs, key=lambda l :rg.wdist(loc, l)), key=lambda x : danger(x))
            return closest[0]
        
        def closest_enemy_dist(loc):
            closest = sorted(enemy_locs, key=lambda l :rg.wdist(loc, l))
            return rg.wdist(loc, closest[0])
        
        def closest_ally_dist(loc):
            closest = sorted(ally_locs, key=lambda l :rg.wdist(loc, l))
            return rg.wdist(loc, closest[0])
        
        def best_attack(loc):
            if len(enemy_locs) == 0:
                return None
            around_me = around(loc, False)
            blarg = sorted(around_me, key=lambda attackloc : attack_value(attackloc), reverse=True)
            return blarg[0]
        
        def locations_of_bots(bots):
            locs = []
            for bot in bots:
                locs.append(bot.location)
            return locs
        
        def empty_around(loc, no_spawn=True):
            return [ar for ar in around(loc, no_spawn) if empty(ar)]
        
        def empty(loc):
            return loc not in ally_locs and loc not in enemy_locs
        
        def valid(loc):
            return 'obstacle' not in rg.loc_types(loc) and 'invalid' not in rg.loc_types(loc)
        
        def stupid(loc):
            if tillspawn == 0:
                return spawn(loc)
            elif tillspawn == 1:
                return unmoveable_spawn(loc)
            return False
        
        def weakest(locs):
            actual_robots = []
            for loc in locs:
                if loc in robots:
                    actual_robots.append(robots[loc])
            if len(actual_robots) == 0:
                return None
            return locations_of_bots(sorted(actual_robots, key=lambda r : r['hp']))

        def danger(loc):
            danger = (1000 * len(nearby_enemies(loc, 1))) + (100 * len(nearby_enemies(loc, 2)))
                
            if spawn(loc):
                if unmoveable_spawn(loc):
                    if tillspawn < 3:
                        danger += 10000
                else:
                    if tillspawn < 2:
                        danger += 10000
                
            if corner(loc):
                danger += 9000
                
            if possibly_trapped(loc):
                if trapped(loc):
                    danger += 9000
                danger += 2500
            return danger
        
        def nethp(locs):
            total = 0
            for loc in locs:
                if loc in robots:
                    total += robots[loc]['hp']
            return total
        
        def attack_value(loc):
            val = 0
            if loc in ally_locs:
                val -= 1000
            if loc in enemy_locs:
                val += 250 - robots[loc]['hp']
            else:
                val += nethp(nearby_enemies(loc, 1))
            return val
        
        def safest_arrangement(locs):
            return filter(lambda x : spawn(x) == False or tillspawn > 1, sorted(locs, key=lambda act : danger(act)))
        
        def trapped(loc):
            return len(empty_around(loc)) == 0
        
        def best_hunt(loc):
            if len(enemy_locs) == 0:
                return None
            lowest_hunt_power = self.hunts[sorted(self.hunts, key=lambda h : self.hunts[h])[0]]
            lowest_hunts = filter(lambda h : self.hunts[h] == lowest_hunt_power, self.hunts)
            parfait = sorted(lowest_hunts, key=lambda x : rg.wdist(loc, x))[0]
            self.hunts[parfait] = self.hunts[parfait] + 1
            return parfait
        
        def possibly_trapped(loc):
            return len(empty_around(loc)) <= 1
        
        def safe_toward(frompos, topos):
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
            elif dx:
                dxn = dx/abs(dx)
                dirs = [(0, -1), (0, 1)]
                dirs = [(dxn, 0)] + dirs
            elif dy:
                dyn = dy/abs(dy)
                dirs = [(-1, 0), (1, 0)]
                dirs = [(0, dyn)] + dirs
        
            posits = []
            for d in dirs:
                newpos = (frompos[0] + d[0], frompos[1] + d[1])
                if empty(newpos):
                    posits.append(newpos)
            safer = filter(lambda move : empty(move) and valid(move), safest_arrangement(posits))
            if len(safer) == 0:
                return curr
            else:
                safest = safer[0]
                if 'normal' in rg.loc_types(safest):
                    return safest
            
        def flee(loc):
            possible_escapes = empty_around(loc, False)
            safest_escapes = safest_arrangement(possible_escapes)
            if len(safest_escapes) == 0:
                return None
            else:
                return ['move', safest_escapes[0]]
            
        def good_escapes(loc):
            possible_escapes = empty_around(loc, False)
            return filter(lambda x : len(nearby_enemies(x, 1)) == 0, possible_escapes)
        
        hunting = best_hunt(curr)
        if hunting == None:
            return ['guard']
        action = ['move', safe_toward(curr, hunting)]
        
        enemy_range = closest_enemy_dist(curr)
        enemies_in_range = nearby_enemies(curr, enemy_range)
        
        if enemy_range == 1:
            fleeing = flee(curr)
            if fleeing == None:
                action = ['attack', best_attack(curr)]
            if len(enemies_in_range) == 4:
                action = ['suicide']
            elif len(enemies_in_range) == 1:
                only_enemy = enemies_in_range[0]
                already = [ally for ally in nearby_allies(only_enemy, 1) if ally != curr and ally in self.friendlies_attacking]
                already_attacking = [ally for ally in already if self.friendlies_attacking[ally] == only_enemy]
                if len(already_attacking) == 0:
                    if self.hp > max(rg.settings.attack_range):
                        possible_helpers = nearby_allies(only_enemy, 2)
                        if len(possible_helpers) > 0:
                            action = ['attack', only_enemy]
                elif len(already_attacking) > 0:
                    action = ['attack', only_enemy]
            
        elif enemy_range == 2:
            action = ['attack', best_attack(curr)]
            first_enemy = enemies_in_range[0]
                    
            if len(enemies_in_range) == 1:
                if spawn(first_enemy):
                    if len(empty_around(first_enemy)) == 1:
                        predicted_escape = rg.toward(first_enemy, rg.CENTER_POINT)
                        if predicted_escape in empty_around(curr):
                            action = ['attack', predicted_escape]
                            
                # This could be dead code, but it seems to work so I'm keeping it
                move_toward = rg.toward(curr, first_enemy)
                possible_enemy_escapes = filter(lambda x : x in enemy_locs or empty(x), around(first_enemy))
                for pee in possible_enemy_escapes:
                    if spawn(pee) and tillspawn == 0:
                        possible_enemy_escapes.remove(pee)
                if len(possible_enemy_escapes) == 0:
                    action = ['move', move_toward]
                    
                    
            for enemy in enemies_in_range:
                
                adj_allies = nearby_allies(enemy, 1)
                allies_to_help = nearby_allies(enemy, 2) # Includes the current bot
                
                if len(adj_allies) + len(allies_to_help) >= 3:
                    if self.hp > max(rg.settings.attack_range): # >= ?
                        towards = safe_toward(curr, enemy)
                        if len(nearby_enemies(towards, 1)) == 1: 
                            action = ['move', towards]
                    
                    
            best_to_kill = sorted(enemies_in_range, key=lambda r : robots[r]['hp'])
            for enemy in best_to_kill:
                predicted_escape = rg.toward(enemy, rg.CENTER_POINT)
                if predicted_escape not in self.taken:
                    # We account for enemies that can move to allow the spawner in
                    around_actual = filter(lambda x : x in enemy_locs or empty(x), around(enemy))
                    if spawn(enemy) and predicted_escape in empty_around(curr) and len(around_actual) == 1:
                        # Enemy is in spawn, the location is safe to move to, and this is the enemy's only escape
                        if tillspawn == 1:
                            if self.hp > 5:
                                action = ['move', predicted_escape]
                        elif tillspawn == 0:
                            if robots[enemy]['hp'] <= 5:
                                action = ['attack', predicted_escape]
                            else:
                                action = ['move', predicted_escape]
                    
        if spawn(curr):
            no_spawn = (unmoveable_spawn(curr) and tillspawn <= 2) or (unmoveable_spawn(curr) == False and tillspawn <= 1)
            routes_out = empty_around(curr, no_spawn)
            if len(routes_out) == 0:
                if tillspawn == 0:
                    action = ['suicide']
            else:
                action = flee(curr)
                if len(routes_out) == 1 and no_spawn:
                    only_out = routes_out[0]
                    action = ['move', only_out]
                
        if action == None:
            return ['guard']
        if action[0] == 'move':
            if stupid(action[1]) or action[1] == self.location:
                best_att = best_attack(curr)
                self.friendlies_attacking[curr] = best_att
                return ['attack', best_att]
            self.taken.append(action[1])
            self.moving.append(curr)
        if action[0] == 'attack':
            self.friendlies_attacking[curr] = action[1]
        return action
    
    