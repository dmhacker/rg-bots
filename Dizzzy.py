
import rg
import random

def add_locs(p1, p2):
    (x1, y1) = p1
    (x2, y2) = p2
    return (x1 + x2, y1 + y2)

'''
Created on May 3, 2014

'''
class Robot:
    provoked = {}
    
    def act(self, game):
        
        def provoked():
            return self.location in self.provoked
        
        def nextToEnemy():
            around = rg.locs_around(self.location, filter_out=('invalid','obstacle'))
            enemies = []
            for l, b in game['robots'].iteritems():
                if b['player_id'] != self.player_id:
                    enemies.append(l)
            next_e = False
            for ar in around:
                if ar in enemies:
                    next_e = True
            return next_e
        
        def nextOffset():
            current_offset = self.provoked[self.location]
            next_offset = (0, 1)
            if current_offset == (0, 1):
                next_offset = (-1, 0)
            elif current_offset == (-1, 0):
                next_offset = (0, -1)
            elif current_offset == (0, -1):
                next_offset = (1, 0)
            elif current_offset == (1, 0):
                next_offset = (0, 1)
            self.provoked[self.location] = next_offset
            return next_offset
        
        def randomMove():
            around = rg.locs_around(self.location, filter_out=('invalid','obstacle','spawn'))
            safe_around = [near for near in around if near not in game['robots']]
            if len(safe_around) == 0:
                return None
            return safe_around[random.randint(0, len(safe_around) - 1)]
        
        rand = randomMove()
        action = ['move',rand]
        if rand == None:
            action = ['guard']
            
        if (nextToEnemy() or provoked()) and self.location not in rg.settings.spawn_coords:
            if self.location not in self.provoked:
                self.provoked[self.location] = (0, 1)
            if random.randint(0, 6) == 3:
                del self.provoked[self.location]
            to_attack = add_locs(self.location, nextOffset())
            if 'normal' in rg.loc_types(to_attack):
                action = ['attack', to_attack]
                
                
        return action