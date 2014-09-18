import rg as d,random
class Robot:
 def act(k,s):
  t=s['turn'];c=s['robots'];b=k.location;n=k.hp;o=filter(lambda a:c[a]['player_id']==k.player_id,c);f=filter(lambda a:c[a]['player_id']!=k.player_id,c);f.sort(key=lambda p:d.wdist(b,p))
  if len(f)==0:return['guard']
  def e(g,u,C):
   if C:filter(lambda a:d.wdist(g,a)==u,o)
   return filter(lambda a:d.wdist(g,a)==u,f)
  def v(g):
   if g in o:return False
   if g in f:return c[g]['hp']<6
   return True
  w=e(b,1,False);l=len(w);q=e(b,2,False);m=(10-t%10)%10
  if t>90:m=10
  x='invalid','obstacle'
  if m<2:x='invalid','obstacle','spawn'
  def y(g):return d.locs_around(b,x)
  D='spawn'in d.loc_types(b)and m<=2;h=filter(lambda a:a not in f or a in f and c[a]['hp']<5,y(b));h.sort(key=lambda a:d.dist(a,d.CENTER_POINT))
  if D:
   if len(h)>0:return['move',h[0]]
   elif m==0:return['suicide']
  if n>10:
   if l==1:return['attack',w[0]]
   elif l>1:
    if len(h)==0and l>2:return['suicide']
    else:
     for i in h:
      E=filter(lambda a:c[a]['hp']>10,e(i,1,False))
      if v(i)and len(E)==0:return['move',i]
  else:
   z=filter(lambda i:v(i)and len(e(i,1,False))==0,h)
   if l>0:
    if len(z)>0:return['move',z[0]]
    else:
     if n>5:return['guard']
     return['suicide']
   if len(q)>0:return['attack',d.toward(b,random.choice(q))]
  for A in q:
   if len(e(A,1,True))>0:
    B=filter(lambda p:p not in o,y(A));B.sort(key=lambda a:-len(e(a,1,False)))
    for r in B:
     if r in h and r!=b:return['move',r]
  j=d.toward(b,f[0])
  if len(e(j,1,False))>1:return['attack',j]
  F=filter(lambda G:c[G]['hp']>n,e(j,1,True))
  if len(F)>1:return['attack',j]
  return['move',j]
