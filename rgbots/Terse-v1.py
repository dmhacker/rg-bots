
import rg, random

'''
This is the old version of Terse (v1.0.2).
It compresses to about a grand total of 996 characters.
Feel free to modify and use; the new version of Terse (v2.0.0) has been improved much.
'''
class Robot:
    
    def act(self, game):
        turn = game['turn']
        robots = game['robots']
        loc = self.location
        health = self.hp
        allies = filter(lambda x : robots[x]['player_id'] == self.player_id, robots)
        enemies = filter(lambda x : robots[x]['player_id'] != self.player_id, robots)
        enemies.sort(key=lambda y : rg.wdist(loc, y))
        if len(enemies) == 0:
            return ['guard']
        def nearby_of(l, radius, allied):
            if allied:
                filter(lambda x : rg.wdist(l, x) == radius, allies)
            return filter(lambda x : rg.wdist(l, x) == radius, enemies)
        def empty(l):
            if l in allies:
                return False
            if l in enemies:
                return robots[l]['hp'] < 6
            return True
        adj_enemies = nearby_of(loc, 1, False)
        adj = len(adj_enemies)
        poss_enemies = nearby_of(loc, 2, False)
        tillspawn = (10 - (turn % 10)) % 10
        if turn > 90:
            tillspawn = 10
        filter_out = ('invalid','obstacle')
        if tillspawn < 2:
            filter_out = ('invalid','obstacle', 'spawn')
        def around_loc(l):
            return rg.locs_around(loc, filter_out)
        should_gtfo = 'spawn' in rg.loc_types(loc) and tillspawn <= 2
        around = filter(lambda x : x not in enemies or (x in enemies and robots[x]['hp'] < 5), around_loc(loc))
        around.sort(key=lambda x : rg.dist(x, rg.CENTER_POINT))
        if should_gtfo:
            if len(around) > 0:
                return ['move', around[0]]
            else:
                if tillspawn == 0:
                    return ['suicide']
        if health > 10:
            if adj == 1:
                return ['attack', adj_enemies[0]]
            elif adj > 1:
                if len(around) == 0 and adj > 2:
                    return ['suicide']
                else:
                    for ar in around:
                        actual = filter(lambda x : robots[x]['hp'] > 10, nearby_of(ar, 1, False))
                        if empty(ar) and len(actual) == 0:
                            return ['move', ar]
        else:
            esc = filter(lambda ar : empty(ar) and len(nearby_of(ar, 1, False)) == 0, around)
            if adj > 0:
                if len(esc) > 0:
                    return ['move', esc[0]]
                else:
                    if health > 5:
                        return ['guard']
                    return ['suicide']
            if len(poss_enemies) > 0:
                return ['attack', rg.toward(loc, random.choice(poss_enemies))]
            
        for poss_enemy in poss_enemies:
            if len(nearby_of(poss_enemy, 1, True)) > 0:
                good_locs_around = filter(lambda y : y not in allies, around_loc(poss_enemy))
                good_locs_around.sort(key=lambda x : -(len(nearby_of(x, 1, False))))
                for gg in good_locs_around:
                    if gg in around and gg != loc:
                        return ['move', gg]
        
        m = rg.toward(loc, enemies[0])
        if len(nearby_of(m, 1, False)) > 1:
            return ['attack', m]
        poss_movers = filter(lambda ally : robots[ally]['hp'] > health, nearby_of(m, 1, True))
        if len(poss_movers) > 1:
                return ['attack', m]
        return ['move', m]
