import rg
import random

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
    near = around(loc, False)
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

class Robot:
    missions = None
    turn = -1
    
    def __init__(self):
        self.missions = Missions()
        
    def act(self, game):
        local_turn = game['turn']
        if self.turn != local_turn:
            self.turn = local_turn
            self.missions.update(game, self.player_id)
        return self.missions.directive(game, self.location)
    
class Missions:
    turn = -1
    player_id = -1
    safe_camps = []
    directives = {}
    moving_allies = {}
    attacking_allies = {}
    bumped_allies = {} # Move taken and the ally going there
    
    def __init__(self):
        for spawn in rg.settings.spawn_coords:
            locs = around(spawn)
            for nearby in locs:
                self.safe_camps.append(nearby)
    
    def directive(self, game, location):
        if location not in self.directives:
            return ['attack', random.choice(around(location, False))]
        return self.directives[location]
    
    def update(self, game, p_id):
        self.player_id = p_id
        self.directives = {}
        self.bumped_allies = {}
        self.moving_allies = {}
        self.attacking_allies = {}
        tillspawn = (10 - (self.turn % 10)) % 10
        if self.turn > 90:
            tillspawn = 10
        robots = game['robots']
        ally_locs = [rloc for rloc in robots.keys() if robots[rloc]['player_id'] == self.player_id]
        enemy_locs = [rloc for rloc in robots.keys() if robots[rloc]['player_id'] != self.player_id]
        
        def closest_enemy(loc):
            closest = sorted(sorted(enemy_locs, key=lambda l :rg.wdist(loc, l)), key=lambda x : robots[x]['hp'])
            return closest[0]
        
        def closest_ally(loc):
            closest = filter(lambda x : x != loc, sorted(sorted(ally_locs, key=lambda l :rg.wdist(loc, l)), key=lambda x : danger_value(x)))
            return closest[0]
        
        def closest_enemy_dist(loc):
            closest = sorted(enemy_locs, key=lambda l :rg.wdist(loc, l))
            return rg.wdist(loc, closest[0])
        
        def closest_ally_dist(loc):
            closest = sorted(ally_locs, key=lambda l :rg.wdist(loc, l))
            return rg.wdist(loc, closest[0])
        
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
            return (len(adjacent_enemies(loc)) + len(possible_enemies(loc))) == 3
        
        def really_trapped(loc):
            return len(adjacent_enemies(loc)) + len(possible_enemies(loc)) >= 4
        
        def bumpable(loc):
            if loc in ally_locs:
                if loc in self.bumped_allies or loc in self.bumped_allies.values():  
                    return False
            return True
        
        def move(curr, dest):
            if dest in self.moving_allies.values():
                self.directives[curr] = ['attack', best_attack(around(curr))]
            else:
                self.directives[curr] = ['move',dest]
                self.moving_allies[curr] = dest
                
        def attack(curr, dest):
            self.directives[curr] = ['attack',dest]
            self.attacking_allies[curr] = dest
            
        def best_attack(locs):
            arran = sorted(locs, key=lambda x : attack_value(x), reverse=True)
            return arran[0]
            
        def attack_value(loc):
            val = 0
            if spawn(loc):
                val += 1
            if val in ally_locs:
                val -= 100
            if loc in enemy_locs:
                val += (250 + robots[loc]['hp']) * 3
            if len(adjacent_enemies(loc)) > 0:
                for en in adjacent_enemies(loc):
                    val += (robots[en]['hp']) * 2
            return val
            
        def danger_value(loc):
            danger = 0
            
            if spawn(loc):
                if unmovable_spawn(loc):
                    if tillspawn  <= 2:
                        danger += 2000 * (10 - tillspawn)
                else:
                    if tillspawn <= 1:
                        danger += 1000 * (10 - tillspawn)
                        
            adj_en = len(adjacent_enemies(loc))
            pos_en = len(possible_enemies(loc))
            
            if adj_en > 0:
                danger += 500 + (1000 * adj_en)
            
            if pos_en > 0:
                danger += 50 + (100 * pos_en)
                
            if possibly_trapped(loc):
                danger += 10000
                
            if loc in ally_locs:
                danger += 20
                
            return danger
        
        def enemy_trapped(enemy):
            poss_en_escapes = around(enemy)
            for esc in poss_en_escapes:
                if stupid(esc):
                    poss_en_escapes.remove(esc)
                else:
                    if esc in ally_locs:
                        poss_en_escapes.remove(esc)
                    else:
                        if len(adjacent_allies(esc)) > 0:
                            poss_en_escapes.remove(esc)
            return len(poss_en_escapes) <= 1
        
        def stupid(loc):
            if spawn(loc):
                if unmovable_spawn(loc):
                    if tillspawn <= 2:
                        return True
                else:
                    if tillspawn <= 1:
                        return True
        
        def good_wish(wish):
            ar = around(wish)
            for a in ar:
                if bumpable(a) == False:
                    ar.remove(a)
            return len(ar) != 0
                
        def actually_dangerous(loc):
            if (stupid_spawn(loc) or unmovable_spawn(loc)) and tillspawn <= 2:
                return True
            if spawn(loc) and tillspawn <= 1:
                return True
            return False
        
        def sorta_dangerous(loc):
            if possibly_trapped(loc) or really_trapped(loc):
                return True
            if loc in enemy_locs:
                return True
            return False
                
        def safest_arrangement(locs):
            #for loc in locs:
                #print loc,danger_value(loc)
            return sorted(locs, key=lambda x : danger_value(x))
        
        def get_hp(loc):
            return robots[loc]['hp']
        
        # Credit to liquid10 for this
        gtfo_bots = filter(lambda x : actually_dangerous(x), ally_locs)
        print gtfo_bots
        
        # Remember, lowest priority to highest priority!
        for bot in ally_locs:
            attack(bot, best_attack(around(bot, False)))
            min_enemy_dist = closest_enemy_dist(bot)
            if min_enemy_dist == 1:
                enemies = adjacent_enemies(bot)
                enemy_amount = len(enemies)
                if enemy_amount == 1:
                    only_enemy = enemies[0]
                    helpers = adjacent_allies(only_enemy)
                    actual_helpers = [h for h in helpers if h not in adjacent_allies(bot) and h != bot]
                    if len(actual_helpers) > 0:
                        if robots[only_enemy]['hp'] < max(rg.settings.attack_range) or robots[bot]['hp'] > max(rg.settings.attack_range):
                            attack(bot, only_enemy)
                    else:
                        if robots[bot]['hp'] > max(rg.settings.attack_range):
                            attack(bot, only_enemy)
                        else:
                            gtfo_bots.append(bot)
                                
                elif enemy_amount == 4:
                        self.directives[bot] = ['suicide']
                else:
                    gtfo_bots.append(bot)
                
                for en in enemies:
                    if robots[bot]['hp'] > 5:
                        if robots[en]['hp'] < max(rg.settings.attack_range):
                            if enemy_trapped(en) == False:
                                move(bot, en)
                                
            elif min_enemy_dist == 2:
                enemies = possible_enemies(bot)
                enemy_amount = len(enemies)
                if enemy_amount > 0:
                    attack(bot, best_attack(around(bot, False)))
                
                    for poss_en in enemies:
                        if enemy_trapped(poss_en):
                            for helper in possible_allies(poss_en):
                                if robots[helper]['hp'] > max(rg.settings.attack_range):
                                    towards = rg.toward(helper, poss_en)
                                    if len(adjacent_enemies(towards)) == 1 and stupid(towards) == False: 
                                        move(helper, towards)
                for pen in enemies:
                    predicted_escape = rg.toward(pen, rg.CENTER_POINT)
                    around_actual = filter(lambda x : x in enemy_locs or empty(x), around(pen))
                    if spawn(pen) and predicted_escape in around(bot) and len(around_actual) == 1:
                        # Enemy is in spawn, the location is safe to move to, and this is the enemy's only escape
                        if tillspawn == 1:
                            if robots[bot]['hp'] > 5:
                                move(bot, predicted_escape)
                        elif tillspawn == 0:
                            if robots[pen]['hp'] <= 5:
                                attack(bot, predicted_escape)
                            else:
                                move(bot, predicted_escape)
                            
        
        gtfo_bots.sort(key=lambda x : danger_value(x))
        while len(gtfo_bots) > 0:
            best_gtfo = gtfo_bots.pop()
            best_act = None
            
            best_wishes = around(best_gtfo, no_spawn=False)
            if tillspawn == 0:
                for poss_wish in best_wishes:
                    if spawn(poss_wish):
                        best_wishes.remove(poss_wish)
            
            if unmovable_spawn(best_gtfo) or stupid_spawn(best_gtfo):
                best_wishes = around(best_gtfo, no_spawn=False)
                
            better_wants_to = filter(lambda x : sorta_dangerous(x) == False, safest_arrangement(best_wishes))
            for wish in better_wants_to:
                if bumpable(wish):
                    best_act = wish
                    break
            
            if best_act != None:
                move(best_gtfo, best_act)
                self.bumped_allies[best_act] = best_gtfo
                if best_act in ally_locs:
                    gtfo_bots.append(best_act)