import rg, random
        
class Robot:
    local_turn = -1
    
    def act(self, game):
        turn = game['turn']
        if turn != self.local_turn:
            self.local_turn = turn
            self.moves = {}
        robots = game['robots']
        loc = self.location
        health = self.hp
        allies = filter(lambda x : robots[x]['player_id'] == self.player_id, robots)
        enemies = filter(lambda x : robots[x]['player_id'] != self.player_id, robots)
        if len(enemies) == 0:
            return ['guard']
        enemies.sort(key=lambda y : rg.wdist(loc, y))
        
        tillspawn = (10 - (turn % 10)) % 10     
        if turn > 90:
            tillspawn = 10
        filter_out = ('invalid','obstacle')
        if tillspawn < 2:
            filter_out = ('invalid','obstacle', 'spawn')
            
        def around_loc(l):
            return rg.locs_around(l, filter_out)
        
        def move(l):
            if l not in self.moves.values():
                self.moves[loc] = l
                return ['move', l]
            else:
                if l in enemies or len(nearby_of(l, 1, False)) > 0:
                    return ['attack', l]
                return ['guard']
            
        def nearby_of(l, radius, allied):
            if allied == True:
                return filter(lambda x : rg.wdist(l, x) == radius, allies)
            return filter(lambda x : rg.wdist(l, x) == radius, enemies)
        
        def empty(l):
            if l in self.moves.values():
                return False
            if l in enemies:
                if robots[l]['hp'] <= 10 * len(nearby_of(l, 1, True)):
                    escapes = filter(lambda x : (len(nearby_of(x, 1, True)) == 0) and x not in allies, around_loc(l))
                    if len(escapes) > 0:
                        return True
            if l in allies:
                if l in self.moves.keys() and self.moves[l] != loc:
                    return True
                else:
                    return False
            return True
        
        def empty_danger(l):
            danger = 0
            if l in enemies:
                danger += 10000 + robots[l]['hp']
            else:
                danger += 10 * len(nearby_of(l, 2, False))
            danger += rg.wdist(l, rg.CENTER_POINT)
            return danger
        
        def can_move(l):
            if 'spawn' in rg.loc_types(l) and tillspawn <= 8:
                return False
            if empty(l):
                return True
            return False
        
        adj_enemies = nearby_of(loc, 1, False)
        adj_enemies.sort(key=lambda x : robots[x]['hp'])
        adj = len(adj_enemies)
        poss_enemies = nearby_of(loc, 2, False)
        
        should_gtfo = 'spawn' in rg.loc_types(loc) and tillspawn <= 3
        around = filter(lambda x : empty(x), around_loc(loc))
        around.sort(key=lambda x : empty_danger(x))
        
        if should_gtfo:
            if len(around) > 0:
                return move(around[0])
            else:
                if tillspawn == 0:
                    return ['suicide']
        if health > 10:
            if adj == 1:
                only = adj_enemies[0]
                if 'spawn' in rg.loc_types(only) and tillspawn <= 3 and robots[only]['hp'] > 5 * (tillspawn - 1) + 7:
                    return ['guard']
                else:
                    if health > 20:
                        only_hp = robots[only]['hp']
                        if (only_hp <= 10 * len(nearby_of(only, 1, True))) and only not in self.moves.values():
                                esc = filter(lambda x : x not in allies and (len(nearby_of(x, 1, True)) == 0) and 'spawn' not in rg.loc_types(x), around_loc(only))
                                if len(esc) > 0:
                                    return move(only)
                    return ['attack', only]
            elif adj > 1:
                if len(around) == 0 and adj > 2:
                    return ['suicide']
                else:
                    better = filter(lambda e : len(filter(lambda x : len(nearby_of(x, 1, True)) == 0,nearby_of(e, 1, False))) == 0, around)
                    if len(better) > 0:
                        return move(better[0])
                    else:
                        if health > 10 * (adj + 1):
                            return ['attack', adj_enemies[0]]
                        else:
                            return ['guard']
        else:
            esc = filter(lambda e : len(filter(lambda x : len(nearby_of(x, 1, True)) == 0 or robots[x]['hp'] <= 10 * len(nearby_of(x, 1, True)), nearby_of(e, 1, False))) == 0, around)
            esc.sort(key=lambda x : empty_danger(x))
            if adj > 0:
                if len(esc) > 0:
                    return move(esc[0])
                else:
                    if health > 5 or len(filter(lambda e : len(nearby_of(e, 1, True)) == 3, adj_enemies)) > 0:
                        return ['guard']
                    return ['suicide']
            if len(poss_enemies) > 0:
                attacks = filter(lambda x : len(nearby_of(x, 1, False)) > 0, around_loc(loc))
                if len(attacks) > 0:
                    return ['attack', random.choice(attacks)]
            
        for poss_enemy in poss_enemies:
            if len(nearby_of(poss_enemy, 1, True)) > 0:
                good_locs_around = filter(lambda y : empty(y), around_loc(poss_enemy))
                good_locs_around.sort(key=lambda x : len(nearby_of(x, 1, True)))
                for gg in good_locs_around:
                    if gg in around and gg != loc:
                        if robots[poss_enemy]['hp'] <= 8 or health < 20:
                            return ['attack', gg]
                        else:
                            if len(filter(lambda x : len(nearby_of(x, 1, True)) == 0, nearby_of(gg, 1, False))) <= 1:
                                return move(gg)
                                
                            
        moves = filter(lambda ar : can_move(ar), around)
        moves.sort(key=lambda x : rg.wdist(x, enemies[0]))
        if len(moves) > 0:
            m = moves[0]
            if len(nearby_of(m, 1, False)) > 1:
                return ['attack', m]
            return move(m)
        else:
            return ['guard']