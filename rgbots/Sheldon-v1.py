import rg, random

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

def valid(loc):
    return 'obstacle' not in rg.loc_types(loc) and 'invalid' not in rg.loc_types(loc)

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

########################################
#
#
#
#              SHELDON
#
#
#
########################################
#
# Following the success of Paarthurnax, I've decided to look at new strategies to further elevate my bot up the ladder
# Sheldon is the prudent product of such an attempt
#
# Basically, what I've done is meld the gtfo queue with the attacking mechanism
# In Paarthurnax, these mechanisms were split into two seperate methods, creating discrepancies and mis-coordination between bots
# Sheldon follows an approach seen in bots like Andriod 383 and Sfpar I and II:
#     It simply finds nearby allies, moves towards them, and attacks nearby bots on its way
# Since Paarthurnax used very nice movement strategies, I'm incorporating some of them into Sheldon
# I also plan to reduce code wordiness and improve readibility, something I had difficulty with in Paarthurnax
#     Admittedly, however, the update method for Mission class is a bit long, but it's necessary in its approach
#
'''
TODO: ...
    - Suicide prediction (heuristic)
    - More enemy fleeing prediction (heuristic)
    - Guard when enemy bot is sure to die from other allies
'''
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
    moving_allies = {}
    old_allies = {}
    old_robots = {}
    directives = {}
    dead_bots = {}
    failed_moves = []
    
    enemy_flees_when_hp_low = False
    moving_into_enemy = {}
    tested_enemy_flees = False
    
    enemy_chases = False
    might_be_chased = []
    
    # Constants
    VERBOSE = False
    
    def directive(self, game, location):
        if location not in self.directives:
            return ['attack', random.choice(around(location, False))]
        action = self.directives[location]
        nubby = self.false_directive(game, location, action)
        if nubby != None:
            self.directives[location] = nubby
            return nubby
        return action
    
    def false_directive(self, game, location, action):
        hp = game['robots'][location]['hp']
        if 'move' in action:
            if game['turn'] < 91 and (spawn(action[1]) and game['turn'] % 10 <= 1) or (game['turn'] % 10 <= 2 and unmovable_spawn(action[1])):
                en_around_me = [e for e in around(location, False) if e in game['robots'] and game['robots'][e]['player_id'] != self.player_id]
                en_around_me.sort(key=lambda r : game['robots'][r]['hp'])
                if len(en_around_me) > 0:
                    if hp <= len(en_around_me) * 9:
                        return ['suicide']
                    return ['attack', en_around_me[0]]
    
    def update(self, game, p_id):
        robots = game['robots']
        self.turn = game['turn']
        self.player_id = p_id
        
        self.history = {}
        
        allies_left = self.count_allies(robots)
        enemies_left = self.count_enemies(robots)
        print "Current match [Sheldon | Enemy] :",allies_left[0],"("+str(allies_left[1])+") ---",enemies_left[0],"("+str(enemies_left[1])+")\n"
        for old_ally in self.old_allies.keys():
            actual_ally = self.old_allies[old_ally]
            id_of = actual_ally['robot_id']
            alive = False
            for r in robots.values():
                if r['player_id'] == p_id:
                    if r['robot_id'] == id_of:
                        alive = True
                        break
            if alive == False:
                fused = [old_ally, id_of, (self.turn - 1)]
                if old_ally not in self.directives:
                    fused.append(None)
                else:
                    fused.append(self.directives[old_ally])
                self.dead_bots[old_ally] = fused
                    
        if self.turn == 99:
            
            print "+=== ENEMY STATS ===+"
            print "Enemy chases friendlies low on hp:",self.enemy_chases
            print "Enemy flees when low on hp:",self.enemy_flees_when_hp_low
            print "\n"
            
            print "+=== FAILED MOVES ("+str(len(self.failed_moves))+") ===+"
            self.failed_moves.sort(key=lambda x : x[2])
            for fail in self.failed_moves:
                orig = fail[0]
                attempt = fail[1]
                turn = fail[2]
                id_of = fail[3]
                print "[T"+str(turn)+"] Robot #"+str(id_of)+" at",orig,"failed to move to:",attempt
            print "\n"
            
            print "+=== DEATHS ("+str(len(self.dead_bots.keys()))+") ===+"
            turn_based_dead_bots = sorted(self.dead_bots.values(), key=lambda x : x[2])
            for info in turn_based_dead_bots:
                old_ally = info[0]
                id_of = info[1]
                turn = info[2]
                direct = info[3]
                print "[T"+str(turn)+"] Robot #"+str(id_of)+" at",old_ally,"died while executing:",direct
                if spawn(old_ally) and turn % 10 == 0:
                        print "    *** ALERT: Robot died at spawn!"
                if direct != None and len(direct) == 2 and direct[0] == 'move':
                    moved_to = direct[1]
                    if spawn(moved_to) and turn % 10 == 0:
                        print "    *** ALERT: Robot moved to bad spawn!"
            print "\n"
                
        self.directives = {}
        
        for mower, prev_move in self.moving_allies.iteritems():
            if 'robot_id' in self.old_robots[mower]:
                idd = self.old_robots[mower]['robot_id']
                if prev_move in robots:
                    if 'robot_id' in robots[prev_move]:
                        nidd = robots[prev_move]['robot_id']
                        if idd != nidd:
                            self.failed_moves.append([mower, prev_move, self.turn - 1, idd])
                else:
                    self.failed_moves.append([mower, prev_move, self.turn - 1, idd])
                
        self.moving_allies = {}
        self.attacking_allies = {}
        self.old_robots = robots
        
        tillspawn = (10 - (self.turn % 10)) % 10
        if self.turn > 90:
            tillspawn = 10
            
        actual_ally_locs = [rloc for rloc in robots.keys() if robots[rloc].player_id == self.player_id]
        self.old_allies = {}
        for gg in actual_ally_locs:
            self.old_allies[gg] = robots[gg] 
        enemy_locs = [rloc for rloc in robots.keys() if robots[rloc]['player_id'] != self.player_id]
                
        if len(self.might_be_chased) > 0:
            for poss_chase in self.might_be_chased:
                if poss_chase in enemy_locs:
                    self.enemy_chases = True
            self.might_be_chased = []
            
        if len(self.moving_into_enemy) > 0:
            for moved_to, id_of in self.moving_into_enemy.iteritems():
                if moved_to in actual_ally_locs:
                    if robots[moved_to]['robot_id'] == id_of:
                        self.enemy_flees_when_hp_low = True
            self.tested_enemy_flees = True
            self.moving_into_enemy = {}
        
        MIN_ATTACK_HP = max(rg.settings.attack_range) + 5
        
        def enemy_might_flee(loc):
            if loc in enemy_locs:
                if robots[loc]['hp'] <= 10:
                    return True
                return False
            return True
                
        def bumpable(loc):
            if loc in self.moving_allies.values():  
                return False
            return True
        
        def move(curr, dest):
            cleanse(curr)
            if dest in self.moving_allies.values() or stupid(dest):
                attack(curr, best_attack(curr))
            if curr == dest:
                guard(curr)
            else:
                self.directives[curr] = ['move',dest]
                self.moving_allies[curr] = dest
                
        def attack(curr, dest):
            cleanse(curr)
            if curr == dest:
                guard(curr)
            else:
                self.directives[curr] = ['attack',dest]
                self.attacking_allies[curr] = dest         
            
        def guard(curr):
            cleanse(curr)
            self.directives[curr] = ['guard']
            
        def suicide(curr):
            cleanse(curr)
            self.directives[curr] = ['suicide']
            
        def cleanse(curr):
            if curr in self.moving_allies:
                del self.moving_allies[curr]
            if curr in self.attacking_allies:
                del self.attacking_allies[curr]
        
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
        
        def sorta_dangerous(loc):
            if stupid(loc):
                return True
            if loc in enemy_locs:
                if robots[loc]['hp'] > 5:
                    return True
            return False
                
        def safest_arrangement(curr, locs, health):
            return sorted(locs, key=lambda x : danger_value_with_hp(curr, x, health))
    
        def get_hp(loc):
            return robots[loc]['hp']
                
        def closest_enemy(loc):
            closest = sorted(enemy_locs, key=lambda l :rg.wdist(loc, l))
            if len(closest) == 0:
                return loc
            return closest[0]
                
        def nearby_enemies(loc, radius):
            return [rloc for rloc in enemy_locs if rg.wdist(loc, rloc) == radius]
        
        def danger_value(loc):
            danger = 0
                    
            if spawn(loc):
                delta = 10 * (10 - tillspawn)
                if tillspawn <= 4:
                    delta ** 3
                danger += delta
                   
            adj_en = len(nearby_enemies(loc, 1))
            pos_en = len(nearby_enemies(loc, 2))
                        
            if adj_en > 0:
                danger += 500 + (1000 * adj_en)
                        
            if pos_en > 0:
                danger += 50 + (100 * pos_en)
            
            if loc in enemy_locs and enemy_might_flee(loc):
                danger -= 10
                
            danger += rg.wdist(loc, rg.CENTER_POINT)
                
            return danger
        
        def danger_value_with_hp(curr, loc, health):
            meh_locs = add_lists(subtract_lists(actual_ally_locs, self.moving_allies.keys()), self.moving_allies.values())
            danger = 0
                    
            if spawn(loc):
                delta = 10 * (10 - tillspawn)
                if tillspawn <= 4:
                    delta ** 3
                danger += delta
                   
            adj_en = len(nearby_enemies(loc, 1))
            pos_en = len(nearby_enemies(loc, 2))
                        
            if adj_en > 0:
                danger += 500 + (1000 * adj_en)
                if len(nearby_enemies(curr, 1)) == 0:
                    fir = nearby_enemies(loc, 1)[0]
                    if adj_en == 1:
                        allies = [rloc for rloc in meh_locs if rg.wdist(fir, rloc) == 1]
                        amt_allies = len(allies) 
                        if amt_allies > 2:
                            if health > 10:
                                danger -= 1000
                            if health > 15:
                                danger -= 600
                        
            if pos_en > 0:
                danger += 50 + (100 * pos_en)
            
            if loc in enemy_locs and enemy_might_flee(loc):
                danger -= 10
                
            #danger += rg.wdist(loc, rg.CENTER_POINT)
                
            return danger
        
        def safe_toward(frompos, topos):
            meh_locs = add_lists(subtract_lists(actual_ally_locs, self.moving_allies.keys()), self.moving_allies.values())
            around_moves = around(frompos, tillspawn<=2)
            move_dict = {}
            for ar in around_moves:
                move_dict[ar] = rg.wdist(ar, topos)
            closest_moves = [m for m in sorted(around_moves, key=lambda x : move_dict[x]) if m not in meh_locs and (m not in enemy_locs or (m in enemy_locs and enemy_might_flee(m))) and valid(m)]
            if len(closest_moves) == 0:
                return frompos
            best_dist = move_dict[closest_moves[0]]
            try_these = []
            for close in closest_moves:
                if move_dict[close] == best_dist:
                    try_these.append(close)
            return safest_arrangement(frompos, try_these, robots[frompos]['hp'])[0]
            
        def should_suicide(loc):
            en = nearby_enemies(loc, 1)
            if len(en) == 4:
                if robots[loc]['hp'] < 40:
                    return True
            elif len(en) == 2 or len(en) == 1:
                open_spaces = [os for os in around(loc, False) if os not in filter(lambda x : robots[x]['hp'] > MIN_ATTACK_HP - 5 and self.enemy_flees_when_hp_low, enemy_locs)]
                dont_move = []
                for osp in open_spaces:
                    if stupid(osp):
                        dont_move.append(osp)
                oss = subtract_lists(open_spaces, dont_move)
                if len(oss) == 0:
                    if robots[loc]['hp'] < 20 or (spawn(loc) and tillspawn == 0):
                        return True
            elif len(en) == 3:
                escapes = filter(lambda x : x not in en, around(loc, tillspawn <= 1))
                if len(escapes) == 0:
                    if robots[loc]['hp'] < 30 or (spawn(loc) and tillspawn == 0):
                        return True
                elif len(escapes) == 1:
                    only_esc = escapes[0]
                    if len(nearby_enemies(only_esc, 1)) > 0:
                        if robots[loc]['hp'] < 30 or (spawn(loc) and tillspawn == 0):
                            return True
            return False
        
        def urgent_leave(loc):
            if corner(loc) or unmovable_spawn(loc) or stupid_spawn(loc):
                return tillspawn <= 3
            else:
                if spawn(loc):
                    if robots[loc]['hp'] > MIN_ATTACK_HP:
                        return tillspawn <= 2
                    else:
                        return tillspawn <= 1
        # Credit to liquid10 for this
        # GTFO bots are currently only bots that are stuck in spawn and need to gtfo out.
        gtfo_bots = filter(lambda x : urgent_leave(x), actual_ally_locs)
        
        # Remember, lowest priority to highest priority!
        for bot in actual_ally_locs:
            if bot not in gtfo_bots:
                ally_locs = add_lists(subtract_lists(actual_ally_locs, self.moving_allies.keys()), self.moving_allies.values())
                
                def closest_ally(loc):
                    closest = filter(lambda x : x != loc, sorted(ally_locs, key=lambda l :rg.wdist(loc, l)))
                    return closest[0]
                    
                def nearby_allies(loc, radius):
                    return [rloc for rloc in ally_locs if rg.wdist(loc, rloc) == radius]
                
                def could_die(loc):
                    enens = len(nearby_enemies(loc, 1))
                    extra = 0
                    for suicider in nearby_enemies(loc, 1):
                        if robots[suicider]['hp'] < 9 * len(nearby_allies(suicider, 1)):
                            extra += 5
                    hp = robots[loc]['hp']
                    if enens > 1:
                        return hp > ((MIN_ATTACK_HP - 5) * enens) + extra
                    return False
        
                def best_attack(loc):
                    locs = around(loc, False)
                    arran = sorted(locs, key=lambda x : attack_value(x), reverse=True)
                    return arran[0]
                        
                def best_attack_of(locs):
                    arran = sorted(locs, key=lambda x : attack_value(x), reverse=True)
                    return arran[0]
                    
                def attack_value(loc):
                    val = 0
                    if loc in ally_locs:
                        if val in self.moving_allies.keys():
                            val += 0
                        else:
                            val -= 100
                    if loc in enemy_locs:
                        val += 1000 + (robots[loc]['hp'] * 4)
                    else:
                        if len(nearby_enemies(loc, 1)) == 0:
                            if loc not in ally_locs and loc not in enemy_locs:
                                val += len(nearby_enemies(loc, 3))
                        for en in nearby_enemies(loc, 1):
                            val += (robots[en]['hp'] * 2)
                    return val
                
                
                if could_die(bot):
                    gtfo_bots.append(bot)
                    
                die_mofo = closest_enemy(bot)
                move(bot, safe_toward(bot, die_mofo))
                    
                ignore = False
                
                poss_enemies = nearby_enemies(bot, 2)
                adj_enemies = nearby_enemies(bot, 1)
                if len(poss_enemies) > 0:
                    attack(bot, best_attack(bot))
                    new_enemies = sorted(poss_enemies, key=lambda x : robots[x]['hp'])
                    
                    for pe in new_enemies:
                        attacking_allies = nearby_allies(pe, 1)
                        helpers = filter(lambda x : spawn(x) == False, nearby_allies(pe, 2))
                        if len(attacking_allies) > 0:
                            lets_kill = safe_toward(bot, pe)
                            if len(nearby_enemies(lets_kill, 1)) == 1:
                                if robots[bot]['hp'] > MIN_ATTACK_HP:
                                    move(bot, lets_kill)
                                else:
                                    if lets_kill != bot:
                                        attack(bot, lets_kill)
                                break
                        else:
                            if len(helpers) >= 3:
                                lets_kill = safe_toward(bot, pe)
                                if len(nearby_enemies(lets_kill, 1)) == 1 or robots[bot]['hp'] > 20:
                                    if robots[bot]['hp'] > MIN_ATTACK_HP:
                                        move(bot, safe_toward(bot, pe))
                                    else:
                                        if safe_toward != bot:
                                            attack(bot, safe_toward(bot, pe))
                                    break
                        
                    # We want to target bots that have the highest health as those could be the most dangerous
                    trapped_enemies = sorted(poss_enemies, key=lambda x : robots[x]['hp'], reverse=True)
                    if spawn(bot) == False:
                        for pe in trapped_enemies:
                            if spawn(pe) and tillspawn <= 2:
                                poss_moves = filter(lambda b : b not in ally_locs, around(bot, no_spawn=True))
                                if len(poss_moves) == 1:
                                    predicted_move = poss_moves[0]
                                    if predicted_move in around(bot, no_spawn=True):
                                        # Maybe make this 15 as opposed to 10
                                        if robots[bot]['hp'] > 10:
                                            if robots[pe]['hp'] > 8:
                                                move(pe, predicted_move)
                                                if bot in gtfo_bots:
                                                    gtfo_bots.remove(bot)
                                            else:
                                                attack(pe, predicted_move)
                                        else:
                                            attack(pe, predicted_move)
                                        ignore = True
                                        break
                        
                if len(adj_enemies) > 0 and ignore == False:
                                
                    first_enemy = adj_enemies[0]
                    
                    if len(adj_enemies) == 1:
                        if robots[bot]['hp'] > MIN_ATTACK_HP:
                            esc = 4
                            counted = []
                            for route_out in around(first_enemy, tillspawn<=1):
                                if route_out in ally_locs:
                                    esc -= 1
                                else:
                                    nearby_a = filter(lambda x : x not in counted, nearby_allies(first_enemy, 1))
                                    if len(nearby_a) > 0:
                                        esc -= 1
                                        counted.append(nearby_a[0])
                            if esc <= 1:
                                attack(bot, first_enemy)
                            if robots[first_enemy]['hp'] <= (MIN_ATTACK_HP - 5):
                                if self.enemy_flees_when_hp_low:
                                    move(bot, first_enemy)
                                if self.tested_enemy_flees == False:
                                    move(bot, first_enemy)
                        elif robots[bot]['hp'] < 10:
                            already_attacking = len(nearby_allies(first_enemy, 1)) 
                            if already_attacking == 4:
                                gtfo_bots.append(bot)
                            elif already_attacking > 0 and already_attacking < 4:
                                if self.enemy_chases:
                                    if len(nearby_enemies(first_enemy, 1)) == 0:
                                        # HP check here maybe?
                                        guard(bot)
                                    else:
                                        standby = len(nearby_allies(bot, 1))
                                        if standby > 0 and standby < 3:
                                            guard(bot)
                                        else:
                                            gtfo_bots.append(bot)
                                else:
                                    gtfo_bots.append(bot)
                    elif len(adj_enemies) > 1:
                        gtfo_bots.append(bot)
                            
                    adj_enemies.sort(key=lambda gg : danger_value(gg))
                    for adj_en in adj_enemies:
                        if robots[bot]['hp'] > MIN_ATTACK_HP:
                            if len(nearby_allies(adj_en, 1)) + len(nearby_allies(adj_en, 2)) >= 4:
                                attack(bot, adj_en)
                                break
                    for adj_en in adj_enemies:
                        if spawn(adj_en) and tillspawn <= 2 and spawn(bot) == False:
                            possible_escapes = filter(lambda gg : gg in ally_locs, around(adj_en, no_spawn=True))
                            if len(possible_escapes) == 0:
                                if robots[bot]['hp'] > 5 * tillspawn:
                                    guard(adj_en)
                                    break
                                    
                if robots[bot]['hp'] <= (MIN_ATTACK_HP - 5):
                    self.might_be_chased.append(bot)
                            
                if should_suicide(bot):
                    suicide(bot)
                            
    
        gtfo_bots.sort(key=lambda x : danger_value(x))
        while len(gtfo_bots) > 0:
            best_gtfo = gtfo_bots.pop()
            best_act = None
            
            best_wishes = around(best_gtfo, tillspawn <= 2)
                
            better_wants_to = filter(lambda x : sorta_dangerous(x) == False, safest_arrangement(best_gtfo, best_wishes, robots[best_gtfo]['hp']))
            for wish in better_wants_to:
                if bumpable(wish):
                    best_act = wish
                    break
            
            if best_act != None:
                move(best_gtfo, best_act)
                if best_act in actual_ally_locs:
                    gtfo_bots.append(best_act)
                    
        for moving, move in self.moving_allies.iteritems():
            if move in enemy_locs and robots[move]['hp'] <= (MIN_ATTACK_HP - 5):
                if moving in robots and 'robot_id' in robots[moving]:
                    self.moving_into_enemy[move] = robots[moving]['robot_id']
                    
    def count_allies(self, game):
        c = 0
        d = 0 
        for robot in game.values():
            if robot['player_id'] == self.player_id:
                c += 1
                d += robot['hp']
        return [c, d]
    
    def count_enemies(self, game):
        c = 0
        d = 0
        for robot in game.values():
            if robot['player_id'] != self.player_id:
                c += 1
                d += robot['hp']
        return [c, d]