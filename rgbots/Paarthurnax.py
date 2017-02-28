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

def unmovable_spawn(loc):
    if spawn(loc) == False:
        return False
    potent_around = around(loc)
    return len(potent_around) == 0

def stupid_spawn(loc):
    return loc == (3,3) or loc == (15, 15) or loc == (3, 15) or loc == (15, 3)

'''
  PAARTHURNAX
 ==== v1.5 ====
 
Rawr ...

'''
class Robot:
    missions = None
    
    def __init__(self):
        self.missions = Missions()
        
    def act(self, game):
        return self.missions.directive(game, self.location, self.player_id)
    
class Missions:
    turn = -1
    player_id = -1
    tillspawn = -1
    moving = {}
    attacking = {}
    directives = {}
    
    def move(self, curr, dest):
        if dest in self.moving.values():
            return self.attack(curr, dest)
        self.directives[curr] = ['move', dest]
        if curr in self.attacking:
            self.attacking.pop(curr)
        self.moving[curr] = dest
        return self.directives[curr]
    
    def attack(self, curr, dest):
        self.directives[curr] = ['attack', dest]
        if curr in self.moving:
            self.moving.pop(curr)
        self.attacking[curr] = dest
        return self.directives[curr]
    
    def directive(self, game, curr, p_id):
        local_turn = game['turn']
        if self.turn != local_turn:
            self.turn = local_turn
            self.update(game, p_id)
            self.tillspawn = (10 - (self.turn % 10)) % 10
            if self.turn > 90:
                self.tillspawn = 10
            
        if curr not in self.directives:
            robots = game['robots']
            self.hp = robots[curr]['hp']
            ally_locs = add_lists(subtract_lists([rloc for rloc in robots.keys() if robots[rloc].player_id == self.player_id], self.moving.keys()), self.moving.values())
            enemy_locs = [rloc for rloc in robots.keys() if robots[rloc].player_id != self.player_id]
            
            self.hunts = {}
            for en in enemy_locs:
                self.hunts[en] = 0
            
                
            def nearby_enemies(loc, radius):
                return [rloc for rloc in enemy_locs if rg.wdist(loc, rloc) == radius]
            
            def nearby_allies(loc, radius):
                return [rloc for rloc in ally_locs if rg.wdist(loc, rloc) == radius]
            
            def closest_enemy(loc):
                closest = sorted(enemy_locs, key=lambda l :rg.wdist(loc, l))
                return closest[0]
            
            def closest_ally(loc):
                closest = sorted(ally_locs, key=lambda l :rg.wdist(loc, l))
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
                if self.tillspawn == 0:
                    return spawn(loc)
                elif self.tillspawn == 1:
                    return unmovable_spawn(loc)
                return False
            
            def weakest(locs):
                actual_robots = []
                for loc in locs:
                    if loc in robots:
                        actual_robots.append(robots[loc])
                if len(actual_robots) == 0:
                    return None
                return locations_of_bots(sorted(actual_robots, key=lambda r : r['hp']))
            
            def possibly_trapped(loc):
                return (len(nearby_enemies(loc, 1)) + len(nearby_enemies(loc, 2))) == 3
        
            def really_trapped(loc):
                return (len(nearby_enemies(loc, 1)) + len(nearby_enemies(loc, 2))) >= 4
    
            def danger(loc):
                danger = (1000 * len(nearby_enemies(loc, 1))) + (100 * len(nearby_enemies(loc, 2)))
                    
                if spawn(loc):
                    if unmovable_spawn(loc):
                        danger += 2000 * ((10 - self.tillspawn) ** 2)
                    else:
                        danger += 500 * ((10 - self.tillspawn) ** 2)
                    
                if corner(loc):
                    danger += 9000
                    
                if possibly_trapped(loc):
                    if really_trapped(loc):
                        danger += 9000
                    danger += 2500
                    
                if loc in ally_locs:
                    danger += 50
                    
                if loc in enemy_locs:
                    if robots[loc]['hp'] < max(rg.settings.attack_range):
                        danger -= 999
                    
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
                    val += 250 + robots[loc]['hp']
                else:
                    val += nethp(nearby_enemies(loc, 1))
                return val
            
            def safest_arrangement(locs):
                return filter(lambda x : stupid(x) == False, sorted(locs, key=lambda act : danger(act)))
            
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
                    return frompos
        
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
                    return frompos
                else:
                    safest = safer[0]
                    if 'normal' in rg.loc_types(safest):
                        return safest
                    
            def flee(loc):
                possible_escapes = empty_around(loc, False)
                safest_escapes = safest_arrangement(possible_escapes)
                if len(safest_escapes) == 0:
                    return ['attack', best_attack(curr)]
                else:
                    return ['move', safest_escapes[0]]
                
            def good_escapes(loc):
                possible_escapes = empty_around(loc, False)
                return filter(lambda x : len(nearby_enemies(x, 1)) == 0, possible_escapes)
            
            def hits_to_kill(loc):
                gg = robots[loc]['hp']
                counter = 0
                (mi, ma) = rg.settings.attack_range
                avg = (mi + ma) / 2
                while gg > 0:
                    gg -= avg
                    counter += 1
                return counter
            
            def can_fight_out(loc):
                nearby = nearby_enemies(loc, 1)
                if len(nearby) == 4:
                    weakest = sorted(nearby, key=lambda x : robots[x]['hp'])[0]
                    if (hits_to_kill(loc) / 4) > hits_to_kill(weakest):
                        return True
                return False
            
            def screwed(loc):
                if spawn(loc) and self.tillspawn == 0:
                    esc = around(loc)
                    return len(esc) == 0
                if can_fight_out(loc):
                    return False
            
            action = ['guard']
            hunting = best_hunt(curr)
            if hunting == None:
                return ['guard']
            action = ['move', safe_toward(curr, hunting)]
            
            enemy_range = closest_enemy_dist(curr)
            enemies_in_range = nearby_enemies(curr, enemy_range)
            
            if enemy_range == 1:
                if len(enemies_in_range) == 1:
                    only_enemy = enemies_in_range[0]
                    already = [ally for ally in nearby_allies(only_enemy, 1) if ally != curr and ally in self.attacking]
                    already_attacking = [ally for ally in already if self.attacking[ally] == only_enemy]
                    if len(already_attacking) == 0:
                        if self.hp > max(rg.settings.attack_range):
                            possible_helpers = nearby_allies(only_enemy, 2)
                            if len(possible_helpers) > 0:
                                action = ['attack', only_enemy]
                    elif len(already_attacking) > 0:
                        action = ['attack', only_enemy]
                        
                for enemy in enemies_in_range:
                    if robots[enemy]['hp'] < max(rg.settings.attack_range):
                        if self.hp > max(rg.settings.attack_range):
                            if enemy not in self.moving.values():
                                poss_escapes = [esc for esc in around(enemy) if empty(esc)]
                                if len(poss_escapes) == 0:
                                    action = ['attack', enemy]
                                else:
                                    if stupid(enemy) == False and len(nearby_enemies(enemy, 1)) < 2:
                                        action = ['move', enemy]
                        
            elif enemy_range == 2:
                action = ['attack', best_attack(curr)]
                first_enemy = enemies_in_range[0]
                        
                if len(enemies_in_range) == 1:
                    if spawn(first_enemy):
                        if len(empty_around(first_enemy)) == 1:
                            predicted_escape = rg.toward(first_enemy, rg.CENTER_POINT)
                            if predicted_escape in empty_around(curr):
                                action = ['attack', predicted_escape]
                        elif len(empty_around(first_enemy)) == 0:
                            action = ['guard']
                    
                    move_toward = rg.toward(curr, first_enemy)
                    possible_enemy_escapes = filter(lambda x : x in enemy_locs or empty(x), around(first_enemy))
                    for pee in possible_enemy_escapes:
                        if spawn(pee) and self.tillspawn == 0:
                            possible_enemy_escapes.remove(pee)
                    if len(possible_enemy_escapes) == 0:
                        action = ['move', move_toward]
                        
                for enemy in enemies_in_range:
                    
                    adj_allies = nearby_allies(enemy, 1)
                    allies_to_help = nearby_allies(enemy, 2) # Includes the current bot
                    
                    if len(adj_allies) + len(allies_to_help) >= 3:
                        if self.hp > max(rg.settings.attack_range):
                            towards = safe_toward(curr, enemy)
                            other = len(nearby_enemies(towards, 1))
                            if other == 1: 
                                action = ['move', towards]
                        
                        
                best_to_kill = sorted(enemies_in_range, key=lambda r : robots[r]['hp'])
                for enemy in best_to_kill:
                    predicted_escape = rg.toward(enemy, rg.CENTER_POINT)
                    if predicted_escape not in self.moving.values():
                        # We account for enemies that can move to allow the spawner in
                        around_actual = filter(lambda x : x in enemy_locs or empty(x), around(enemy))
                        if spawn(enemy) and predicted_escape in empty_around(curr) and len(around_actual) == 1:
                            # Enemy is in spawn, the location is safe to move to, and this is the enemy's only escape
                            if self.tillspawn == 1:
                                if self.hp > 5:
                                    action = ['move', predicted_escape]
                            elif self.tillspawn == 0:
                                if robots[enemy]['hp'] <= 5:
                                    action = ['attack', predicted_escape]
                                else:
                                    action = ['move', predicted_escape]
                              
                                    
                                    
            if spawn(curr):
                if self.hp <= max(rg.settings.attack_range):
                    if self.tillspawn == 1:
                        routes_out = empty_around(curr, True)
                        if len(routes_out) == 1:
                            only_out = routes_out[0]
                            action = ['move', only_out]
                        elif len(routes_out) > 1:
                            action = flee(curr)
                    elif self.tillspawn == 0:
                        routes_out = around(curr, True)
                        if len(routes_out) == 1:
                            only_out = routes_out[0]
                            action = ['move', only_out]
                        elif len(routes_out) > 1:
                            action = flee(curr)      
                    else:
                        routes_out = empty_around(curr, False)
                        if len(routes_out) == 1:
                            only_out = routes_out[0]
                            action = ['move', only_out]
                        elif len(routes_out) > 1:
                            action = flee(curr)
            
            
            if screwed(curr):
                action = ['suicide']
            
            if action[0] == 'move':
                if stupid(action[1]) or action[1] == curr:
                    return self.attack(curr, best_attack(curr))
                return self.move(curr, action[1])
            if action[0] == 'attack':
                return self.attack(curr, action[1])
            return action
        else:
            return self.directives[curr]
    
    def update(self, game, p_id):
        robots = game['robots']
        self.player_id = p_id
        self.directives = {}
        self.moving = {}
        ally_locs = [rloc for rloc in robots.keys() if robots[rloc]['player_id'] == self.player_id]
        enemy_locs = [rloc for rloc in robots.keys() if robots[rloc]['player_id'] != self.player_id]
        
        def adjacent_enemies(loc):
            return [rloc for rloc in enemy_locs if rg.wdist(loc, rloc) == 1]
            
        def adjacent_allies(loc):
            return [rloc for rloc in ally_locs if rg.wdist(loc, rloc) == 1]
        
        def possible_enemies(loc):
            return [rloc for rloc in enemy_locs if rg.wdist(loc, rloc) == 2]
            
        def possible_allies(loc):
            return [rloc for rloc in ally_locs if rg.wdist(loc, rloc) == 2]
        
        def empty(loc):
            return loc not in ally_locs and loc not in enemy_locs
        
        def really_empty(loc):
            return loc not in enemy_locs
        
        def possibly_trapped(loc):
            if (len(adjacent_enemies(loc)) + len(possible_enemies(loc))) == 3:
                return True
            if really_trapped(loc):
                return True
            return False
        
        def really_trapped(loc):
            return len(adjacent_enemies(loc)) + len(possible_enemies(loc)) >= 4
        
        def bumpable(loc):
            if loc in ally_locs:
                if loc in self.moving.values(): 
                    return False
            return True
       
        def danger(loc):
            danger = (1000 * len(adjacent_enemies(loc))) + (100 * len(possible_enemies(loc)))
                    
            if spawn(loc):
                if unmovable_spawn(loc):
                    danger += 2000 * ((10 - self.tillspawn) ** 2)
                else:
                    danger += 500 * ((10 - self.tillspawn) ** 2)
                    
            if corner(loc):
                danger += 9000
                    
            if possibly_trapped(loc):
                if really_trapped(loc):
                    danger += 9000
                danger += 2500
                
            if loc in ally_locs:
                danger += 50
                
            if loc in enemy_locs:
                if robots[loc]['hp'] < max(rg.settings.attack_range):
                    danger -= 999
                
            return danger
        
        def good_wish(wish):
            ar = around(wish)
            for a in ar:
                if bumpable(a) == False:
                    ar.remove(a)
            return len(ar) != 0
                
        def actually_dangerous(loc):
            if robots[loc]['hp'] <= 5:
                unfiltered = adjacent_enemies(loc)
                if unfiltered > 0 and unfiltered < 4:
                    return True
            # Ignore really trapped bots since they are doomed
            near = len(filter(lambda x : robots[x]['hp'] > max(rg.settings.attack_range), adjacent_enemies(loc)))
            if near > 1 and near < 4:
                return True
            if near == 1:
                if robots[loc]['hp'] <= max(rg.settings.attack_range):
                    return True
            if (stupid_spawn(loc) or unmovable_spawn(loc) or corner(loc)) and self.tillspawn <= 2:
                if robots[loc]['hp'] > max(rg.settings.attack_range):
                    return True
            if spawn(loc) and self.tillspawn <= 1:
                if robots[loc]['hp'] > max(rg.settings.attack_range):
                    return True
            return False
        
        def sorta_dangerous(loc):
            if possibly_trapped(loc):
                return True
            if loc in enemy_locs:
                return True
            return False
                
        def safest_arrangement(locs):
            return sorted(locs, key=lambda x : danger(x))
        
        # Credit to liquid10 for this
        gtfo_bots = filter(lambda x : actually_dangerous(x), safest_arrangement(ally_locs))
        
        while len(gtfo_bots) > 0:
            best_gtfo = gtfo_bots.pop()
            best_act = None
            
            best_wishes = around(best_gtfo)
            
            if unmovable_spawn(best_gtfo) or stupid_spawn(best_gtfo) or self.tillspawn == 0:
                best_wishes = around(best_gtfo, no_spawn=False)
                
            better_wants_to = filter(lambda x : sorta_dangerous(x) == False, safest_arrangement(best_wishes))
            
            for wish in better_wants_to:
                if bumpable(wish):
                    best_act = wish
                    break
            if best_act != None:
                self.move(best_gtfo, best_act)
                if best_act in ally_locs:
                    gtfo_bots.append(best_act)