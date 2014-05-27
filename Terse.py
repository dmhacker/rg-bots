
import rg

class Robot:
    
    def act(self, game):
        turn = game['turn']
        robots = game['robots']
        guard = 'guard'
        attack = 'attack'
        move = 'move'
        suicide = 'suicide'
        hps = 'hp'
        invalid = 'invalid'
        obstacle = 'obstacle'
        spawn = 'spawn'
        loc = self.location
        health = self.hp
        allies = filter(lambda x : robots[x]['player_id'] == self.player_id, robots)
        enemies = filter(lambda x : robots[x]['player_id'] != self.player_id, robots)
        enemies.sort(key=lambda y : rg.wdist(loc, y))
        if enemies == None or len(enemies) == 0:
            return [guard]
        def nearby_enemies(l, radius):
            return filter(lambda x : rg.wdist(l, x) == radius, enemies)
        def nearby_allies(l, radius):
            return filter(lambda x : rg.wdist(l, x) == radius, allies)
        def empty(l):
            if l in allies:
                return False
            if l in enemies:
                if robots[l][hps] > 5 and health > 10:
                    return False
            return True
        adj_enemies = nearby_enemies(loc, 1)
        poss_enemies = nearby_enemies(loc, 2)
        tillspawn = (10 - (turn % 10)) % 10
        if turn > 90:
            tillspawn = 10
        filter_out = (invalid,obstacle)
        if tillspawn == 0:
            filter_out = (invalid,obstacle, spawn)
        around = filter(lambda x : x not in enemies or (x in enemies and robots[x][hps] < 10), rg.locs_around(loc, filter_out))
        around.sort(key=lambda x : rg.dist(x, rg.CENTER_POINT))
        if spawn in rg.loc_types(loc) and tillspawn <= 1:
            if len(around) > 0:
                return [move, around[0]]
            else:
                if tillspawn == 0:
                    return [suicide]
        if health > 10:
            num = len(adj_enemies)
            gtfo = spawn in rg.loc_types(loc) and tillspawn <= 2
            if num == 1:
                return [attack, adj_enemies[0]]
            elif num > 1:
                if num == 4:
                    return [suicide]
                elif num == 3 and len(around) == 0:
                    return [suicide]
                else:
                    gtfo = True
            if gtfo:
                for ar in around:
                    actual = filter(lambda x : robots[x][hps] > 10, nearby_enemies(ar, 1))
                    if empty(ar) and len(actual) == 0:
                        return [move, ar]
        else:
            esc = filter(lambda ar : empty(ar) and len(filter(lambda x : robots[x][hps] > 10, nearby_enemies(ar, 1))) == 0, around)
            if len(adj_enemies) > 0:
                if len(esc) > 0:
                    return [move, esc[0]]
                else:
                    if health > 5:
                        return [guard]
                    return [suicide]
            if len(poss_enemies) > 0:
                poss_enemies.sort(key=lambda x : -(robots[x][hps]))
                return [attack, rg.toward(loc, poss_enemies[0])]
            
        for poss_enemy in poss_enemies:
            if len(nearby_allies(poss_enemy, 1)) > 0:
                good_locs_around = sorted(filter(lambda y : y not in allies, rg.locs_around(poss_enemy, filter_out)), key=lambda x : len(nearby_allies(x, 1)), reverse=True)
                for gg in good_locs_around:
                    if gg in around and gg != loc:
                        return [move, gg]
        
        m = rg.toward(loc, enemies[0])
        if len(nearby_enemies(m, 1)) > 1:
            return [attack, m]
        poss_movers = nearby_allies(m, 1)
        if len(poss_movers) > 1:
            for ally in poss_movers:
                if robots[ally][hps] > health:
                    return [attack, m]
        return [move, m]