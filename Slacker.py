import rg as c;import random
def k(a):return'spawn'in c.loc_types(a)or a in c.settings.spawn_coords
def aB(a):return sorted(c.settings.spawn_coords,key=lambda e:c.dist(a,e))[0]
def aC(a):return(abs(a[0]-9),abs(a[1]-9))in[(2,8),(4,7),(6,6),(7,4)]
def h(a,no_spawn=True):
 U='invalid','obstacle'
 if no_spawn:U='invalid','obstacle','spawn'
 return c.locs_around(a,U)
def aD(a):
 ag=h(a,False)
 for ah in ag:
  if k(ah):return True
 return False
def E(a):
 if k(a)==False:return False
 ai=h(a);return len(ai)==0
def V(a):return a==(3,3)or a==(15,15)or a==(3,15)or a==(15,3)
class Robot:
 missions=None;turn=-1
 def __init__(b):b.missions=aj()
 def act(b,t):
  W=t['turn']
  if b.turn!=W:b.turn=W;b.missions.update(t,b.player_id)
  return b.missions.directive(t,b.location)
class aj:
 turn=-1;player_id=-1;safe_camps=[];directives={};moving_allies={};attacking_allies={};bumped_allies={}
 def __init__(b):
  for k in c.settings.spawn_coords:
   z=h(k)
   for ak in z:b.safe_camps.append(ak)
 def directive(b,t,location):
  if location not in b.directives:return['attack',random.choice(h(location,False))]
  return b.directives[location]
 def update(b,t,al):
  b.player_id=al;b.directives={};b.bumped_allies={};b.moving_allies={};b.attacking_allies={};i=(10-b.turn%10)%10
  if b.turn>90:i=10
  g=t['robots'];j=[f for f in g.keys()if g[f]['player_id']==b.player_id];l=[f for f in g.keys()if g[f]['player_id']!=b.player_id]
  def aE(a):m=sorted(sorted(l,key=lambda n:c.wdist(a,n)),key=lambda e:g[e]['hp']);return m[0]
  def aF(a):m=filter(lambda e:e!=a,sorted(sorted(j,key=lambda n:c.wdist(a,n)),key=lambda e:M(e)));return m[0]
  def am(a):m=sorted(l,key=lambda n:c.wdist(a,n));return c.wdist(a,m[0])
  def aG(a):m=sorted(j,key=lambda n:c.wdist(a,n));return c.wdist(a,m[0])
  def o(a):return[f for f in l if c.wdist(a,f)==1]
  def N(a):return[f for f in j if c.wdist(a,f)==1]
  def F(a):return[f for f in l if c.wdist(a,f)==2]
  def an(a):return[f for f in j if c.wdist(a,f)==2]
  def ao(a):return a not in j and a not in l
  def aH(a):return a not in l
  def X(a):return len(o(a))+len(F(a))==3
  def ap(a):return len(o(a))+len(F(a))>=4
  def Y(a):
   if a in j:
    if a in b.bumped_allies or a in b.bumped_allies.values():return False
   return True
  def A(p,u):
   if u in b.moving_allies.values():b.directives[p]=['attack',O(h(p))]
   else:b.directives[p]=['move',u];b.moving_allies[p]=u
  def B(p,u):b.directives[p]=['attack',u];b.attacking_allies[p]=u
  def O(z):aq=sorted(z,key=lambda e:ar(e),reverse=True);return aq[0]
  def ar(a):
   v=0
   if k(a):v+=1
   if v in j:v-=100
   if a in l:v+=(250+g[a]['hp'])*3
   if len(o(a))>0:
    for C in o(a):v+=g[C]['hp']*2
   return v
  def M(a):
   q=0
   if k(a):
    if E(a):
     if i<=2:q+=2000*(10-i)
    elif i<=1:q+=1000*(10-i)
   Z=len(o(a));aa=len(F(a))
   if Z>0:q+=500+1000*Z
   if aa>0:q+=50+100*aa
   if X(a):q+=10000
   if a in j:q+=20
   return q
  def ab(at):
   D=h(at)
   for w in D:
    if ac(w):D.remove(w)
    elif w in j:D.remove(w)
    elif len(N(w))>0:D.remove(w)
   return len(D)<=1
  def ac(a):
   if k(a):
    if E(a):
     if i<=2:return True
    elif i<=1:return True
  def aI(G):
   P=h(G)
   for ad in P:
    if Y(ad)==False:P.remove(ad)
   return len(P)!=0
  def au(a):
   if(V(a)or E(a))and i<=2:return True
   if k(a)and i<=1:return True
   return False
  def av(a):
   if X(a)or ap(a):return True
   if a in l:return True
   return False
  def aw(z):return sorted(z,key=lambda e:M(e))
  def aJ(a):return g[a]['hp']
  r=filter(lambda e:au(e),j);print r
  for d in j:
   B(d,O(h(d,False)));ae=am(d)
   if ae==1:
    s=o(d);H=len(s)
    if H==1:
     I=s[0];ax=N(I);ay=[Q for Q in ax if Q not in N(d)and Q!=d]
     if len(ay)>0:
      if g[I]['hp']<max(c.settings.attack_range)or g[d]['hp']>max(c.settings.attack_range):B(d,I)
     elif g[d]['hp']>max(c.settings.attack_range):B(d,I)
     else:r.append(d)
    elif H==4:b.directives[d]=['suicide']
    else:r.append(d)
    for C in s:
     if g[d]['hp']>5:
      if g[C]['hp']<max(c.settings.attack_range):
       if ab(C)==False:A(d,C)
   elif ae==2:
    s=F(d);H=len(s)
    if H>0:
     B(d,O(h(d,False)))
     for R in s:
      if ab(R):
       for S in an(R):
        if g[S]['hp']>max(c.settings.attack_range):
         T=c.toward(S,R)
         if len(o(T))==1and ac(T)==False:A(S,T)
    for J in s:
     K=c.toward(J,c.CENTER_POINT);az=filter(lambda e:e in l or ao(e),h(J))
     if k(J)and K in h(d)and len(az)==1:
      if i==1:
       if g[d]['hp']>5:A(d,K)
      elif i==0:
       if g[J]['hp']<=5:B(d,K)
       else:A(d,K)
  r.sort(key=lambda e:M(e))
  while len(r)>0:
   x=r.pop();y=None;L=h(x,no_spawn=False)
   if i==0:
    for af in L:
     if k(af):L.remove(af)
   if E(x)or V(x):L=h(x,no_spawn=False)
   aA=filter(lambda e:av(e)==False,aw(L))
   for G in aA:
    if Y(G):y=G;break
   if y!=None:
    A(x,y);b.bumped_allies[y]=x
    if y in j:r.append(y)
