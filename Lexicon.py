
import rg
import random

'''
Created May 2, 2014

Lexicon was intended as a short and sweet bot that could handle prediction and fleeing.
It didn't turn out so short.

'''
class Robot:
    
    local_turn = -1
    movements = []
    
    def act(self, game):
        (mi, ma) = rg.settings.attack_range
        MIN_HP = (mi + ma) 
        turn = game['turn']
        game_bots = game['robots']
        hunts = {}
        if self.local_turn != turn:
            self.local_turn = turn
            self.movements = []
        health = self.hp
        curr = self.location
        all_bots = [bot for bot in game_bots.values()]
        my_id = self.player_id
        til_spawn = (10 - (turn % 10)) % 10
        
        def nearby(enemy, radius=1):
            return nearby_of_location(curr, enemy, radius)
        
        def nearby_of_location(loc, enemy, radius=1):
            if enemy:
                return [bot for bot in all_bots if rg.wdist(loc, bot['location']) == radius and bot['player_id'] != my_id]
            return [bot for bot in all_bots if rg.wdist(loc, bot['location']) == radius and bot['player_id'] == my_id]
        
        def nearest_enemy_loc():
            enemy_dict = {}
            enemies = [bot for bot in all_bots if bot['player_id'] != my_id]
            for enemy in enemies:
                eloc = enemy['location']
                enemy_dict[eloc] =rg.wdist(curr, eloc)
            top = sorted(enemy_dict, key=lambda loc : enemy_dict[loc])[0]
            dist = enemy_dict[top]
            similar = {}
            for bot in enemy_dict:
                if enemy_dict[bot] == dist:
                    if bot not in hunts:
                        similar[bot] = 0
                    else:
                        similar[bot] = hunts[bot]
            nearby_en = sorted(similar, key=lambda s : similar[s])[0]
            if nearby_en in hunts:
                tagged = hunts[nearby_en]
                hunts[nearby_en] = tagged + 1
            else:
                hunts[nearby_en] = 0
            return nearby_en
        
        def nearest_spawn():
            return sorted(rg.settings.spawn_coords, key=lambda loc : rg.dist(curr, loc))[0]
        
        def moveable(loc):
            if 'obstacle' in rg.loc_types(loc) or loc in [bloc for bloc in game_bots if  game_bots[bloc]['player_id'] != my_id]:
                return False
            if (til_spawn == 0) and loc in rg.settings.spawn_coords:
                return False
            if (til_spawn <= 1) and (abs(loc[0]-9), abs(loc[1]-9)) == (6, 6):
                return False
            return True
        
        def stupid_move(loc):
            possible = rg.locs_around(loc, filter_out=('invalid','obstacle','spawn'))
            for near in nearby(True):
                possible.remove(near)
            if len(possible) == (0 or 1):
                return True
            return False
        
        def safe():
            around = {}
            for loc in rg.locs_around(curr, filter_out=('invalid','obstacle','spawn')):
                if loc not in self.movements:
                    if loc not in game_bots:
                        danger = (len(nearby(True)) * 5)
                        + len(nearby(True, 2)) 
                        + rg.wdist(curr, nearest_spawn()) 
                        + rg.wdist(curr, rg.CENTER_POINT)
                        if loc in rg.settings.spawn_coords:
                            danger += 100 * (10 - til_spawn)
                        if rg.wdist(loc, nearest_spawn()) == 1:
                            if nearest_spawn() in game_bots:
                                if game_bots[nearest_spawn()].player_id == self.player_id:
                                    danger += 1000
                                else:
                                    danger -= 100
                        if moveable(loc) == False:
                            danger += 2500
                        around[loc] = danger
            output = sorted(around, key=lambda a : around[a])
            if len(output) == 0:
                return None
            duplicated = {}
            supposed_best = output[0]
            duplicated[supposed_best] = len(nearby_of_location(supposed_best, False))
            for out in around.keys():
                if supposed_best != out:
                    if around[supposed_best] == around[out]:
                        duplicated[out] = len(nearby_of_location(out, False))
            
            return sorted(duplicated, key=lambda p : duplicated[p])[0] # Move to a less crowded area
        
        def panic(include_suicide):
            poss = []
            ar = rg.locs_around(curr, filter_out=('invalid','obstacle'))
            if include_suicide:
                ar = rg.locs_around(curr, filter_out=('invalid','obstacle','spawn'))
            for around in ar:
                if around not in game_bots:
                    poss.append(around)
            if len(poss) == 0:
                return None
            return poss[random.randint(0, len(poss) - 1)]
        
        if til_spawn <= 3 and curr in rg.settings.spawn_coords:
            panic_move = panic(False)
            if til_spawn == 1:
                panic_move = panic(True)
            if panic_move != None:
                self.movements.append(panic_move)
                return ['move',panic_move]
            else:
                if til_spawn == 0:
                    return ['suicide']
                else:
                    return ['guard']
            
        
        poss_enemies = nearby(True, 2)
        nearby_enemies = nearby(True)
        ne_len = len(nearby_enemies)
        pe_len = len(poss_enemies)
        
        if ne_len > 1:
            if ne_len == 4:
                return ['suicide']
            if health > MIN_HP:
                return ['attack', sorted(nearby_enemies, key=lambda x : x['hp'])[0]['location']]
            safe_move = safe()
            if safe_move == None:
                panic_move = panic(False)
                if panic_move != None:
                    self.movements.append(panic_move)
                    return ['move', panic_move]
                return ['attack', sorted(nearby_enemies, key=lambda x : x['hp'])[0]['location']]
            self.movements.append(safe_move)
            return ['move', safe_move]
        elif ne_len == 1:
            if health > MIN_HP:
                return ['attack', nearby_enemies[0]['location']]
            safe_move = safe()
            if safe_move == None:
                panic_move = panic(False)
                if panic_move != None:
                    self.movements.append(panic_move)
                    return ['move',panic_move]
                return ['attack', nearby_enemies[0]['location']]
            self.movements.append(safe_move)
            return ['move', safe_move]
            
        if pe_len == 1:
            only_enemy = poss_enemies[0]
            only_enemy_loc = only_enemy['location']
            if health > MIN_HP and health > only_enemy['hp']:
                actual_move = rg.toward(curr, only_enemy_loc)
                if stupid_move(actual_move) == False:
                    if len(nearby_of_location(only_enemy_loc, False)) > 0 or moveable(actual_move):
                        self.movements.append(rg.toward(curr, only_enemy_loc))
                        return ['move',rg.toward(curr, only_enemy_loc)]
            return ['attack', rg.toward(curr, only_enemy_loc)]
        
        elif pe_len > 1:
            hp_bots = sorted(poss_enemies, key=lambda e : e['hp'], reverse=True)
            best = hp_bots[0]['location']
            return ['attack', rg.toward(curr, best)]

        self.movements.append(rg.toward(curr, nearest_enemy_loc()))
        return ['move', rg.toward(curr, nearest_enemy_loc())]
    
    