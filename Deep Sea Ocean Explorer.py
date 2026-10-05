"""
Deep Sea Ocean Explorer  ·  Level 1: The Drive
Pure-software 3D perspective renderer using Pygame.
"""
import pygame, sys, math, random
pygame.init()

SW, SH = 1000, 720
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Deep Sea Ocean Explorer  ·  3D Drive")
clock  = pygame.time.Clock()
FPS    = 60

# ── Fonts ──────────────────────────────────────────────────────────────────────
try:
    F_BIG  = pygame.font.SysFont("segoeui", 52, bold=True)
    F_MED  = pygame.font.SysFont("segoeui", 28, bold=True)
    F_HUD  = pygame.font.SysFont("segoeui", 18, bold=True)
    F_SM   = pygame.font.SysFont("segoeui", 15)
    F_TINY = pygame.font.SysFont("segoeui", 12)
except Exception:
    F_BIG  = pygame.font.Font(None, 52)
    F_MED  = pygame.font.Font(None, 28)
    F_HUD  = pygame.font.Font(None, 18)
    F_SM   = pygame.font.Font(None, 15)
    F_TINY = pygame.font.Font(None, 12)

# ── Colours ────────────────────────────────────────────────────────────────────
SKY_TOP  = ( 22,  50, 118)
SKY_BOT  = (138, 182, 228)
GND_NEAR = ( 55, 108,  42)
GND_FAR  = ( 32,  68,  25)
FOG_C    = (178, 204, 224)
ROAD_C   = ( 65,  68,  73)
ROAD_LN  = (255, 218,   0)
ROAD_EG  = (215, 215, 215)
SEA_C    = ( 28,  88, 198)
SEA2_C   = ( 42, 112, 225)
SAND_C   = (210, 192, 128)
WHITE    = (255, 255, 255)
RED_C    = (210,  32,  32)
GREEN_C  = ( 35, 200,  58)
YEL_C    = (255, 210,   0)
ORANGE_C = (255, 155,   0)
BLUE_C   = ( 30, 100, 245)
BLUE2_C  = ( 12,  58, 180)
CYAN_C   = (  0, 200, 255)
LAMP_C   = ( 55,  58,  68)
GLOW_C   = (255, 244, 188)
WOOD_C   = ( 92,  56,  26)
WOOD2_C  = ( 66,  40,  14)
ROOF_C   = (140,  58,  20)
SKIN_C   = (255, 205, 160)
JEANS_C  = ( 46,  88, 164)
SHIRT_C  = (216, 216, 222)
HAIR_C   = ( 46,  28,   8)
CAR_BLU  = ( 28,  96, 208)

# ── Road waypoints  (world X, world Z;  height Y = 0 = ground) ────────────────
WP = [
    (1000, 7400),   # 0  START
    (1000, 6600),   # 1
    (1000, 5800),   # 2  stop sign
    (1000, 5000),   # 3
    (1000, 4200),   # 4  traffic light
    (1000, 3400),   # 5
    (1800, 3400),   # 6  corner
    (2600, 3400),   # 7
    (3400, 3400),   # 8  traffic light
    (3400, 2600),   # 9  corner
    (3400, 1800),   # 10
    (4200, 1800),   # 11 corner
    (5000, 1800),   # 12
    (5600, 1800),   # 13 stop sign
    (6200, 1800),   # 14 corner
    (6200, 1200),   # 15
    (6200,  700),   # 16 BOATHOUSE
]

ROAD_W  = 80
HALF_RW = ROAD_W // 2
SEA_X   = 6540
WORLD_W = 7200
WORLD_H = 8200

DRIVE    = "drive"
CUTSCENE = "cutscene"
WALK     = "walk"

# ══════════════════════════════════════════════════════════════════════
#  3-D CAMERA  &  PROJECTION
# ══════════════════════════════════════════════════════════════════════
CAM_DIST   = 90
CAM_HEIGHT = 55
FOCAL      = 560
HOR_Y      = int(SH * 0.40)
FOG_S      = 280
FOG_E      = 1400

def get_cam(wx, wz, ang):
    r = math.radians(ang)
    fx, fz = math.sin(r), -math.cos(r)
    return (wx - fx*CAM_DIST, float(CAM_HEIGHT), wz - fz*CAM_DIST, ang)

def proj(wx, wy, wz, cam):
    """World (wx,wy,wz) → (sx,sy,scale,depth)  or None if behind camera."""
    cx, cy, cz, ang = cam
    r = math.radians(ang)
    fx, fz = math.sin(r), -math.cos(r)
    rx, rz = math.cos(r),  math.sin(r)
    dx, dy, dz = wx-cx, wy-cy, wz-cz
    lx = dx*rx + dz*rz
    ly = dy
    lz = dx*fx + dz*fz
    if lz < 2.0: return None
    s = FOCAL / lz
    return (SW//2 + int(lx*s), HOR_Y - int(ly*s), s, lz)

def fogc(col, d):
    if d <= FOG_S: return col
    t = min(0.88, (d-FOG_S)/(FOG_E-FOG_S))
    return tuple(int(c*(1-t)+f*t) for c,f in zip(col, FOG_C))

def sh(col, f):
    return tuple(min(255, max(0, int(c*f))) for c in col)

def gl(surf, col, sx, sy, r, alpha=120):
    if r < 1 or r > 80: return
    s = pygame.Surface((r*2+1, r*2+1), pygame.SRCALPHA)
    pygame.draw.circle(s, (*col[:3], alpha), (r, r), r)
    surf.blit(s, (sx-r, sy-r))

# ── Pre-rendered sky + ground background ──────────────────────────────────────
_bg = None
def build_bg():
    global _bg
    _bg = pygame.Surface((SW, SH))
    for y in range(HOR_Y+1):
        t = y/max(1,HOR_Y)
        c = tuple(int(SKY_TOP[i]*(1-t)+SKY_BOT[i]*t) for i in range(3))
        pygame.draw.line(_bg, c, (0,y), (SW-1,y))
    for y in range(HOR_Y, SH):
        t = (y-HOR_Y)/max(1,SH-HOR_Y)
        c = tuple(int(GND_NEAR[i]*(1-t)+GND_FAR[i]*t) for i in range(3))
        pygame.draw.line(_bg, c, (0,y), (SW-1,y))

# ══════════════════════════════════════════════════════════════════════
#  ROAD  (subdivided perspective-correct quads)
# ══════════════════════════════════════════════════════════════════════
def draw_road_3d(surf, cam):
    cx, cy, cz = cam[0], cam[1], cam[2]
    for i in range(len(WP)-1):
        wx0,wz0 = WP[i]; wx1,wz1 = WP[i+1]
        dx,dz = wx1-wx0, wz1-wz0
        L = math.hypot(dx,dz)
        if L < 1: continue
        ux,uz = dx/L, dz/L
        px,pz = -uz*HALF_RW, ux*HALF_RW
        if math.hypot((wx0+wx1)/2-cx,(wz0+wz1)/2-cz) > FOG_E+200: continue
        N = max(2, int(L//40))
        pl_=pr_=pm_=None; pd=FOG_E
        for k in range(N+1):
            t = k/N
            mx = wx0+ux*t*L; mz = wz0+uz*t*L
            pl=proj(mx+px,0,mz+pz,cam); pr=proj(mx-px,0,mz-pz,cam); pm=proj(mx,0,mz,cam)
            cl=(pl[0],pl[1]) if pl else None; cr=(pr[0],pr[1]) if pr else None
            cm=(pm[0],pm[1]) if pm else None; cd=pl[3] if pl else FOG_E
            if k>0 and pl_ and pr_ and cl and cr:
                ad=(pd+cd)*0.5
                pygame.draw.polygon(surf,fogc(ROAD_C,ad),[pl_,pr_,cr,cl])
                pygame.draw.line(surf,fogc(ROAD_EG,ad),pl_,cl,2)
                pygame.draw.line(surf,fogc(ROAD_EG,ad),pr_,cr,2)
                if k%2==1 and pm_ and cm:
                    pygame.draw.line(surf,fogc(ROAD_LN,ad),pm_,cm,2)
            pl_,pr_,pm_,pd = cl,cr,cm,cd

# ══════════════════════════════════════════════════════════════════════
#  3-D BOX  (shaded faces, depth-sorted)
# ══════════════════════════════════════════════════════════════════════
def draw_box_3d(surf, cam, wx, wz, w, dd, h, col, ang=0, base_y=0):
    """Draw a shaded 3-D box at world (wx, base_y, wz)."""
    r = math.radians(ang)
    fx,fz = math.sin(r),-math.cos(r); rx,rz = math.cos(r),math.sin(r)
    def c3(sx,sz,hy): return (wx+sx*rx+sz*fx, base_y+hy, wz+sx*rz+sz*fz)
    bl=c3(-w/2,-dd/2,0); br=c3(w/2,-dd/2,0); fl=c3(-w/2,dd/2,0); fr=c3(w/2,dd/2,0)
    tbl=c3(-w/2,-dd/2,h); tbr=c3(w/2,-dd/2,h); tfl=c3(-w/2,dd/2,h); tfr=c3(w/2,dd/2,h)
    cp=proj(wx,base_y+h/2,wz,cam)
    if cp is None: return None
    FACES=[("top",[tbl,tbr,tfr,tfl],1.0),("front",[fl,fr,tfr,tfl],0.80),
           ("back",[bl,br,tbr,tbl],0.60),("left",[bl,fl,tfl,tbl],0.70),("right",[br,fr,tfr,tbr],0.72)]
    dl=[]
    for nm,pts3,sf in FACES:
        sc=[]; dep=[]; ok=True
        for (a,b,c_) in pts3:
            p=proj(a,b,c_,cam)
            if p is None: ok=False; break
            sc.append((p[0],p[1])); dep.append(p[3])
        if not ok or not sc: continue
        da=sum(dep)/len(dep); fc=fogc(sh(col,sf),da)
        dl.append((da,fc,sc))
    dl.sort(key=lambda x:x[0],reverse=True)
    for _,fc,sc in dl:
        if len(sc)>=3:
            pygame.draw.polygon(surf,fc,sc)
            pygame.draw.polygon(surf,sh(fc,0.55),sc,1)
    return cp[3]

def draw_pole_3d(surf,cam,wx,wz,h,col,width=3):
    pb=proj(wx,0,wz,cam); pt=proj(wx,h,wz,cam)
    if not pb or not pt or pb[3]>FOG_E: return None
    d=pb[3]; w=max(1,int(width*min(2.0,100/max(1,d))))
    pygame.draw.line(surf,fogc(col,d),(pb[0],pb[1]),(pt[0],pt[1]),w)
    return d

# ══════════════════════════════════════════════════════════════════════
#  STREET LAMP  3-D
# ══════════════════════════════════════════════════════════════════════
LAMP_H = 62
def draw_lamp_3d(surf, cam, wx, wz):
    d = draw_pole_3d(surf,cam,wx,wz,LAMP_H,LAMP_C,3)
    if d is None or d>FOG_E: return d
    arm_p=proj(wx,LAMP_H,wz,cam); arm_e=proj(wx+14,LAMP_H+2,wz,cam)
    if arm_p and arm_e:
        ww=max(1,int(2*min(2.0,100/max(1,d))))
        pygame.draw.line(surf,fogc(LAMP_C,d),(arm_p[0],arm_p[1]),(arm_e[0],arm_e[1]),ww)
    ge=proj(wx+14,LAMP_H+5,wz,cam)
    if ge and d<FOG_E:
        gs=max(2,int(8*ge[2])); gc=fogc(GLOW_C,d)
        if 1<gs<50: gl(surf,gc,ge[0],ge[1],gs,160); pygame.draw.circle(surf,gc,(ge[0],ge[1]),max(1,gs//3))
    return d

# ══════════════════════════════════════════════════════════════════════
#  STOP SIGN  3-D
# ══════════════════════════════════════════════════════════════════════
STOP_H = 46
def draw_stopsign_3d(surf, cam, ss):
    wx,wz=ss.wx,ss.wy
    draw_pole_3d(surf,cam,wx,wz,STOP_H,LAMP_C,3)
    cp=proj(wx,STOP_H+12,wz,cam)
    if not cp or cp[3]>FOG_E: return
    r_px=max(4,int(13*cp[2])); d=cp[3]
    pygame.draw.circle(surf,fogc(RED_C,d),(cp[0],cp[1]),r_px)
    pygame.draw.circle(surf,fogc((255,255,255),d),(cp[0],cp[1]),r_px,max(1,r_px//5))
    if r_px>=8:
        t=F_TINY.render("STOP",True,fogc((255,255,255),d))
        sc=max(0.5,min(1.5,cp[2]*1.4))
        if sc!=1.0: t=pygame.transform.scale(t,(max(1,int(t.get_width()*sc)),max(1,int(t.get_height()*sc))))
        surf.blit(t,t.get_rect(center=(cp[0],cp[1])))

# ══════════════════════════════════════════════════════════════════════
#  TRAFFIC LIGHT  3-D
# ══════════════════════════════════════════════════════════════════════
TL_POLE_H = 50; TL_BOX_H = 40; TL_BOX_Y = TL_POLE_H
def draw_trafficlight_3d(surf, cam, tl):
    wx,wz=tl.wx,tl.wy
    draw_pole_3d(surf,cam,wx,wz,TL_POLE_H,LAMP_C,4)
    d=draw_box_3d(surf,cam,wx,wz,15,10,TL_BOX_H,(28,28,28),base_y=TL_BOX_Y)
    if d is None or d>FOG_E: return
    reds=TL_BOX_Y+TL_BOX_H-8; yels=TL_BOX_Y+TL_BOX_H//2; grns=TL_BOX_Y+8
    light_data=[(reds,RED_C,(55,18,18),tl.phase=="red"),
                (yels,YEL_C,(58,48,10),tl.phase=="yellow"),
                (grns,GREEN_C,(12,58,18),tl.phase=="green")]
    for (hy,con,cof,is_on) in light_data:
        lp=proj(wx,hy,wz,cam)
        if lp and lp[3]<FOG_E:
            r=max(2,int(6*lp[2])); col=fogc(con if is_on else cof,lp[3])
            pygame.draw.circle(surf,col,(lp[0],lp[1]),r)
            if is_on and r>2: gl(surf,col[:3],lp[0],lp[1],r*2,75)

# ══════════════════════════════════════════════════════════════════════
#  BOATHOUSE  3-D
# ══════════════════════════════════════════════════════════════════════
def draw_boathouse_3d(surf, cam, bh):
    wx,wz=bh.wx,bh.wy; BW,BD,BH=88,88,62
    d=draw_box_3d(surf,cam,wx,wz,BW,BD,BH,WOOD_C)
    if d is None or d>FOG_E+300: return
    # Gable roof
    def pt3(sx,sz,hy): return (wx+sx,hy,wz+sz)
    rh=BH+42
    rl=pt3(0,BD/2,rh); rb=pt3(0,-BD/2,rh)
    efl=pt3(-BW/2,BD/2,BH); efr=pt3(BW/2,BD/2,BH)
    ebl=pt3(-BW/2,-BD/2,BH); ebr=pt3(BW/2,-BD/2,BH)
    roof_faces=[([rl,rb,ebr,efr],0.72),([rl,rb,ebl,efl],0.62),([efl,efr,rl],0.80),([ebl,ebr,rb],0.55)]
    dl=[]
    for (fp,sf) in roof_faces:
        sc=[]; dep=[]; ok=True
        for pt in fp:
            p=proj(pt[0],pt[1],pt[2],cam)
            if not p: ok=False; break
            sc.append((p[0],p[1])); dep.append(p[3])
        if not ok or not sc: continue
        da=sum(dep)/len(dep); fc=fogc(sh(ROOF_C,sf),da)
        dl.append((da,fc,sc))
    dl.sort(key=lambda x:x[0],reverse=True)
    for _,fc,sc in dl:
        if len(sc)>=3: pygame.draw.polygon(surf,fc,sc); pygame.draw.polygon(surf,sh(fc,0.55),sc,1)
    # Door
    door=[pt3(-12,BD/2+1,0),pt3(12,BD/2+1,0),pt3(12,BD/2+1,34),pt3(-12,BD/2+1,34)]
    sc=[]; dep=[]; ok=True
    for pt in door:
        p=proj(pt[0],pt[1],pt[2],cam)
        if not p: ok=False; break
        sc.append((p[0],p[1])); dep.append(p[3])
    if ok and len(sc)>=3: pygame.draw.polygon(surf,fogc(WOOD2_C,sum(dep)/len(dep)),sc)
    # Sign
    sp=proj(wx,BH+10,wz,cam)
    if sp and sp[3]<FOG_E:
        sc2=max(0.3,min(1.2,sp[2]*0.7))
        t=F_SM.render("BOAT HOUSE",True,fogc((255,255,255),sp[3]))
        if sc2!=1.0: t=pygame.transform.scale(t,(max(1,int(t.get_width()*sc2)),max(1,int(t.get_height()*sc2))))
        surf.blit(t,t.get_rect(center=(sp[0],sp[1])))
    # Dock planks
    for k in range(-4,5):
        p0=proj(wx+k*9,0,wz+BD/2+5,cam); p1=proj(wx+k*9,0,wz+BD/2+55,cam)
        if p0 and p1 and p0[3]<FOG_E:
            pw=max(1,int(5*p0[2]))
            pygame.draw.line(surf,fogc(WOOD_C,p0[3]),(p0[0],p0[1]),(p1[0],p1[1]),pw)

# ══════════════════════════════════════════════════════════════════════
#  TREE  (billboard)
# ══════════════════════════════════════════════════════════════════════
def draw_tree_3d(surf, cam, wx, wz, rw, col):
    th=rw*0.8; draw_pole_3d(surf,cam,wx,wz,th,(78,50,20),3)
    cp=proj(wx,th+rw*0.5,wz,cam)
    if not cp or cp[3]>FOG_E: return
    rpx=max(3,int(rw*cp[2]))
    if rpx>200: return
    fc=fogc(col,cp[3]); lite=(min(255,col[0]+28),min(255,col[1]+28),min(255,col[2]+20))
    pygame.draw.circle(surf,fc,(cp[0],cp[1]),rpx)
    pygame.draw.circle(surf,fogc(lite,cp[3]),(cp[0]-rpx//4,cp[1]-rpx//3),rpx//2)

# ══════════════════════════════════════════════════════════════════════
#  AI CAR  3-D
# ══════════════════════════════════════════════════════════════════════
def draw_aicars_3d(surf, cam, ac):
    d=draw_box_3d(surf,cam,ac.wx,ac.wy,22,36,16,ac.col,ang=ac.angle)
    if d is None or d>FOG_E: return
    r=math.radians(ac.angle); fx,fz=math.sin(r),-math.cos(r); rx,rz=math.cos(r),math.sin(r)
    def c3(sx,sz,hy): return (ac.wx+sx*rx+sz*fx,hy,ac.wy+sx*rz+sz*fz)
    ws=[c3(-8,18,16),c3(8,18,16),c3(8,18,11),c3(-8,18,11)]
    sc=[]; ok=True; dep=[]
    for pt in ws:
        p=proj(pt[0],pt[1],pt[2],cam)
        if not p: ok=False; break
        sc.append((p[0],p[1])); dep.append(p[3])
    if ok and len(sc)>=3: pygame.draw.polygon(surf,fogc((120,180,230),sum(dep)/len(dep)),sc)

# ══════════════════════════════════════════════════════════════════════
#  PLAYER CAR  3-D  (detailed)
# ══════════════════════════════════════════════════════════════════════
def draw_playercar_3d(surf, cam, car):
    d=draw_box_3d(surf,cam,car.wx,car.wy,22,42,17,CAR_BLU,ang=car.angle)
    if d is None: return
    r=math.radians(car.angle); fx,fz=math.sin(r),-math.cos(r); rx,rz=math.cos(r),math.sin(r)
    def c3(sx,sz,hy): return (car.wx+sx*rx+sz*fx,hy,car.wy+sx*rz+sz*fz)
    # Windshield
    ws=[c3(-9,20,17),c3(9,20,17),c3(9,20,11),c3(-9,20,11)]
    sc=[]; ok=True; dep=[]
    for pt in ws:
        p=proj(pt[0],pt[1],pt[2],cam)
        if not p: ok=False; break
        sc.append((p[0],p[1])); dep.append(p[3])
    if ok and len(sc)>=3: pygame.draw.polygon(surf,fogc((140,200,255),sum(dep)/len(dep)),sc)
    # Rear window
    rw=[c3(-8,-20,14),c3(8,-20,14),c3(8,-20,10),c3(-8,-20,10)]
    sc=[]; ok=True; dep=[]
    for pt in rw:
        p=proj(pt[0],pt[1],pt[2],cam)
        if not p: ok=False; break
        sc.append((p[0],p[1])); dep.append(p[3])
    if ok and len(sc)>=3: pygame.draw.polygon(surf,fogc((110,170,220),sum(dep)/len(dep)),sc)
    # Tail lights
    for sx in [-8,8]:
        tp=proj(c3(sx,-21,4)[0],c3(sx,-21,4)[1],c3(sx,-21,4)[2],cam)
        if tp and tp[3]<FOG_E:
            rpx=max(2,int(5*tp[2]))
            pygame.draw.rect(surf,fogc(RED_C,tp[3]),(tp[0]-rpx,tp[1]-rpx//2,rpx*2,rpx))
    # Headlight glow
    if car.spd>0.5 and d<400:
        for sx in [-7,7]:
            hl=c3(sx,22,5); hp=proj(hl[0],hl[1],hl[2],cam)
            if hp: gl(surf,GLOW_C,hp[0],hp[1],max(4,int(18*hp[2])),70)
    # Blinkers
    if (car.bt//15)%2==0:
        for (is_on,sx) in [(car.bl,-12),(car.br,12)]:
            if is_on:
                b3=c3(sx,-20,6); bp=proj(b3[0],b3[1],b3[2],cam)
                if bp and bp[3]<FOG_E:
                    rpx=max(2,int(4*bp[2]))
                    pygame.draw.circle(surf,fogc(ORANGE_C,bp[3]),(bp[0],bp[1]),rpx)

# ══════════════════════════════════════════════════════════════════════
#  HUMAN  3-D  (billboard)
# ══════════════════════════════════════════════════════════════════════
def draw_human_3d(surf, cam, human, tick):
    wx,wz=human.wx,human.wy
    feet=proj(wx,0,wz,cam)
    if not feet or feet[3]>FOG_E+50: return
    d=feet[3]; sc=max(0.5,min(3.0,feet[2]))
    cj=fogc(JEANS_C,d); cs=fogc(SHIRT_C,d); csk=fogc(SKIN_C,d); ch=fogc(HAIR_C,d)
    bx,by=feet[0],feet[1]; wk=int(math.sin(tick*0.28)*3*sc); h_px=max(4,int(16*sc))
    pygame.draw.line(surf,cj,(bx,by),(bx-int(2*sc),by-h_px//2+wk),max(1,int(4*sc)))
    pygame.draw.line(surf,cj,(bx,by),(bx+int(2*sc),by-h_px//2-wk),max(1,int(4*sc)))
    pygame.draw.rect(surf,cs,(bx-int(4*sc),by-h_px,int(8*sc),h_px//2+1))
    pygame.draw.line(surf,csk,(bx-int(4*sc),by-h_px+int(2*sc)),(bx-int(7*sc),by-int(h_px*0.6)-wk),max(1,int(2*sc)))
    pygame.draw.line(surf,csk,(bx+int(4*sc),by-h_px+int(2*sc)),(bx+int(7*sc),by-int(h_px*0.6)+wk),max(1,int(2*sc)))
    hr=max(3,int(7*sc)); head=proj(wx,34,wz,cam)
    hx,hy=(head[0],head[1]) if head else (bx,by-h_px-hr)
    pygame.draw.circle(surf,csk,(hx,hy),hr)
    pygame.draw.arc(surf,ch,pygame.Rect(hx-hr,hy-hr,hr*2,hr+2),0,math.pi,max(1,hr//3))

# ══════════════════════════════════════════════════════════════════════
#  BLUE ARROWS  (on road surface, 3-D)
# ══════════════════════════════════════════════════════════════════════
def make_arrows():
    arrows=[]; SPACE=160
    for i in range(len(WP)-1):
        wx0,wz0=WP[i]; wx1,wz1=WP[i+1]
        dx,dz=wx1-wx0,wz1-wz0; L=math.hypot(dx,dz)
        if L<1: continue
        ux,uz=dx/L,dz/L; n=max(1,int(L//SPACE))
        for k in range(n):
            t=(k+0.5)/n
            arrows.append((wx0+ux*t*L,wz0+uz*t*L,ux,uz))
    return arrows

def draw_arrows_3d(surf, cam, arrows, tick):
    blink=(tick//20)%2==0
    for wx,wz,ux,uz in arrows:
        d=math.hypot(wx-cam[0],wz-cam[2])
        if d>600 or d<20: continue
        px,pz=-uz,ux; size=18
        tip=(wx+ux*size,0,wz+uz*size)
        ptl=(wx-ux*size*0.5+px*size*0.6,0,wz-uz*size*0.5+pz*size*0.6)
        ptr=(wx-ux*size*0.5-px*size*0.6,0,wz-uz*size*0.5-pz*size*0.6)
        tp=proj(tip[0],0,tip[2],cam); lp=proj(ptl[0],0,ptl[2],cam); rp=proj(ptr[0],0,ptr[2],cam)
        if tp and lp and rp and tp[3]<600:
            col=fogc(BLUE_C if blink else BLUE2_C,tp[3])
            pygame.draw.polygon(surf,col,[(tp[0],tp[1]),(lp[0],lp[1]),(rp[0],rp[1])])

# ══════════════════════════════════════════════════════════════════════
#  SEA / SAND  (3-D ground tiles near coast)
# ══════════════════════════════════════════════════════════════════════
def draw_sea_3d(surf, cam, wave_t):
    cx,cz=cam[0],cam[2]
    if cx<SEA_X-700: return
    TILE=120; z0=int(cz-700)//TILE*TILE; z1=z0+1400
    for tx in range(int(SEA_X)-80,int(SEA_X)+600,TILE):
        for tz in range(z0,z1,TILE):
            pts3=[(tx,0,tz),(tx+TILE,0,tz),(tx+TILE,0,tz+TILE),(tx,0,tz+TILE)]
            sc=[]; dep=[]; ok=True
            for pt in pts3:
                p=proj(pt[0],pt[1],pt[2],cam)
                if not p: ok=False; break
                sc.append((p[0],p[1])); dep.append(p[3])
            if not ok or not sc: continue
            da=sum(dep)/len(dep)
            wo=int(8*math.sin(wave_t*0.04+tx*0.012+tz*0.018))
            col=fogc(SAND_C,da) if tx<SEA_X else fogc(SEA_C if wo>0 else SEA2_C,da)
            pygame.draw.polygon(surf,col,sc)

# ══════════════════════════════════════════════════════════════════════
#  GAME CLASSES  (logic only – rendering done above)
# ══════════════════════════════════════════════════════════════════════
def angle_of(dx,dy): return math.degrees(math.atan2(dx,-dy))%360

def glass_box(surf,x,y,w,h,col=(0,0,0),alpha=160,radius=6):
    s=pygame.Surface((w,h),pygame.SRCALPHA)
    pygame.draw.rect(s,(*col,alpha),(0,0,w,h),border_radius=radius)
    surf.blit(s,(x,y))

class TrafficLight:
    PHASES=[("red",110),("green",90),("yellow",28)]
    def __init__(self,wp,side=1):
        x0,y0=WP[wp-1]; x1,y1=WP[wp]; dx,dy=x1-x0,y1-y0; L=math.hypot(dx,dy)
        px,py=(-dy/L,dx/L) if L>0 else (1.0,0.0)
        self.wx=x1+px*56*side; self.wy=y1+py*56*side
        self.pi=random.randint(0,2); self.timer=0; self._next()
    def _next(self): self.phase,dur=self.PHASES[self.pi%3]; self.timer=dur; self.pi+=1
    def update(self):
        self.timer-=1
        if self.timer<=0: self._next()
    @property
    def red(self): return self.phase=="red"

class StopSign:
    def __init__(self,wp,side=1):
        x0,y0=WP[wp-1]; x1,y1=WP[wp]; dx,dy=x1-x0,y1-y0; L=math.hypot(dx,dy)
        px,py=(-dy/L,dx/L) if L>0 else (1.0,0.0)
        self.wx=x1+px*54*side; self.wy=y1+py*54*side

class BoatHouse:
    RADIUS=72
    def __init__(self): self.wx,self.wy=WP[-1]
    def near(self,px,py): return math.hypot(px-self.wx,py-self.wy)<self.RADIUS

class AICar:
    COLS=[(185,28,28),(28,155,28),(172,118,18),(90,28,172),(188,92,18),(28,108,175),(175,88,155),(28,155,155)]
    def __init__(self,wp=0):
        self.wi=wp%(len(WP)-1); x0,y0=WP[self.wi]; x1,y1=WP[self.wi+1]; t=random.random()
        self.wx=x0+(x1-x0)*t; self.wy=y0+(y1-y0)*t
        self.angle=angle_of(x1-x0,y1-y0); self.col=random.choice(self.COLS); self.spd=2.0*random.uniform(0.75,1.25)
    def update(self,tlights):
        for tl in tlights:
            if tl.red and math.hypot(self.wx-tl.wx,self.wy-tl.wy)<90: return
        if self.wi>=len(WP)-2: self.wi=0
        tx,ty=WP[self.wi+1]; dx,dy=tx-self.wx,ty-self.wy; d=math.hypot(dx,dy)
        if d<12: self.wi=(self.wi+1)%(len(WP)-1)
        else: self.wx+=dx/d*self.spd; self.wy+=dy/d*self.spd; self.angle=angle_of(dx,dy)

class PlayerCar:
    MAX_F=4.4; MAX_R=1.6; ACC=0.055; BRK=0.11; FRIC=0.962; STEER=2.6
    def __init__(self):
        self.wx=float(WP[0][0]); self.wy=float(WP[0][1])
        self.angle=angle_of(WP[1][0]-WP[0][0],WP[1][1]-WP[0][1])
        self.spd=0.0; self.bl=False; self.br=False; self.bt=0
    def update(self,keys,tlights):
        self.bt+=1
        if keys[pygame.K_q]: self.bl=not self.bl; self.br=False
        if keys[pygame.K_e]: self.br=not self.br; self.bl=False
        turn=int(keys[pygame.K_RIGHT] or keys[pygame.K_d])-int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.angle=(self.angle+turn*self.STEER*min(1.0,abs(self.spd)/1.8))%360
        fwd=keys[pygame.K_UP] or keys[pygame.K_w]
        brk=keys[pygame.K_SPACE]; rev=keys[pygame.K_DOWN] or keys[pygame.K_s]
        at_red=any(tl.red and math.hypot(self.wx-tl.wx,self.wy-tl.wy)<105 for tl in tlights)
        if fwd and not at_red: self.spd=min(self.MAX_F,self.spd+self.ACC)
        elif brk: self.spd=max(0.0,self.spd-self.BRK) if self.spd>0 else max(-self.MAX_R,self.spd-self.ACC)
        elif rev: self.spd=max(-self.MAX_R,self.spd-self.ACC)
        else:
            self.spd*=self.FRIC
            if abs(self.spd)<0.01: self.spd=0.0
        rad=math.radians(self.angle)
        self.wx+=math.sin(rad)*self.spd; self.wy-=math.cos(rad)*self.spd

class Human:
    SPD=2.2
    def __init__(self,wx,wy,angle=0): self.wx=wx; self.wy=wy; self.angle=angle; self.t=0
    def update(self,keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.angle=(self.angle-3)%360
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.angle=(self.angle+3)%360
        rad=math.radians(self.angle)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.wx+=math.sin(rad)*self.SPD; self.wy-=math.cos(rad)*self.SPD; self.t+=1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.wx-=math.sin(rad)*self.SPD; self.wy+=math.cos(rad)*self.SPD; self.t+=1

# ── World builders ─────────────────────────────────────────────────────────────
def make_lamps():
    lamps=[]; SPACE=210; SIDE=50
    for i in range(len(WP)-1):
        wx0,wz0=WP[i]; wx1,wz1=WP[i+1]; dx,dz=wx1-wx0,wz1-wz0; L=math.hypot(dx,dz)
        if L<1: continue
        ux,uz=dx/L,dz/L; px,pz=-uz,ux; n=max(1,int(L//SPACE))
        for k in range(n):
            t=(k+0.4)/n; lx=wx0+ux*t*L; lz=wz0+uz*t*L; side=1 if k%2==0 else -1
            lamps.append((lx+px*SIDE*side,lz+pz*SIDE*side))
    return lamps

def make_trees(seed=7):
    rng=random.Random(seed); trees=[]; SPACE=115; SIDE=78
    for i in range(len(WP)-1):
        wx0,wz0=WP[i]; wx1,wz1=WP[i+1]; dx,dz=wx1-wx0,wz1-wz0; L=math.hypot(dx,dz)
        if L<1: continue
        ux,uz=dx/L,dz/L; px,pz=-uz,ux; n=max(1,int(L//SPACE))
        for k in range(n):
            t=(k+rng.random())/n; lx=wx0+ux*t*L; lz=wz0+uz*t*L; off=rng.uniform(SIDE,SIDE+65)
            for side in [-1,1]:
                if rng.random()<0.82:
                    tx=lx+px*off*side+rng.uniform(-18,18); tz=lz+pz*off*side+rng.uniform(-18,18)
                    r=rng.randint(13,27); col=(rng.randint(38,70),rng.randint(94,148),rng.randint(28,60))
                    trees.append((tx,tz,r,col))
    return trees

# ── Minimap ────────────────────────────────────────────────────────────────────
MW,MH=155,122; MX=SW-MW-8; MY=100
def draw_minimap(surf,car,human,bh):
    ms=pygame.Surface((MW,MH),pygame.SRCALPHA)
    pygame.draw.rect(ms,(0,0,0,168),(0,0,MW,MH),border_radius=7)
    def m(wx,wy): return (int(wx/WORLD_W*MW),int(wy/WORLD_H*MH))
    for i in range(len(WP)-1): pygame.draw.line(ms,(108,112,122),m(*WP[i]),m(*WP[i+1]),2)
    bx,by=m(bh.wx,bh.wy); pygame.draw.circle(ms,(80,160,255),(bx,by),4)
    if car: px_,py_=m(car.wx,car.wy); pygame.draw.circle(ms,(40,215,80),(px_,py_),5)
    if human: hx,hy=m(human.wx,human.wy); pygame.draw.circle(ms,(40,215,80),(hx,hy),4)
    pygame.draw.rect(ms,(172,178,205,185),(0,0,MW,MH),1,border_radius=7)
    ms.blit(F_TINY.render("MAP",True,(162,172,205)),(5,3)); surf.blit(ms,(MX,MY))

# ── HUD ────────────────────────────────────────────────────────────────────────
def draw_hud(surf,car,elapsed,dist_bh):
    glass_box(surf,10,10,148,56,(0,0,0),162)
    surf.blit(F_SM.render("SPEED",True,(128,155,205)),(18,14))
    surf.blit(F_MED.render(f"{abs(car.spd)*28:.0f} km/h",True,(255,255,255)),(18,30))
    mins=int(elapsed)//60; secs=int(elapsed)%60
    glass_box(surf,SW//2-60,10,120,38,(0,0,0),142)
    t_s=F_HUD.render(f"{mins:02d}:{secs:02d}",True,(200,220,255)); surf.blit(t_s,t_s.get_rect(center=(SW//2,29)))
    glass_box(surf,SW-168,10,158,56,(0,0,0),162)
    surf.blit(F_SM.render("TO BOATHOUSE",True,(80,170,255)),(SW-160,14))
    surf.blit(F_HUD.render(f"{max(0,int(dist_bh/4))} m",True,(255,255,255)),(SW-160,32))
    glass_box(surf,10,74,76,28,(0,0,0),142)
    L_on=car.bl and (car.bt//15)%2==0; R_on=car.br and (car.bt//15)%2==0
    pygame.draw.polygon(surf,ORANGE_C if L_on else (48,38,8),[(20,88),(32,80),(32,96)])
    pygame.draw.polygon(surf,ORANGE_C if R_on else (48,38,8),[(66,88),(54,80),(54,96)])
    glass_box(surf,10,108,52,32,(0,0,0),142)
    if car.spd<-0.05: g,gc="R",RED_C
    elif car.spd>0.05: g,gc="D",GREEN_C
    else: g,gc="N",(255,255,255)
    surf.blit(F_MED.render(g,True,gc),(18,110))
    ctrl=F_TINY.render("W/↑ Fwd  S/↓ Rev  A/D Steer  SPACE Brake  Q/E Blinkers",True,(145,155,178))
    glass_box(surf,SW//2-ctrl.get_width()//2-8,SH-26,ctrl.get_width()+16,20,(0,0,0),118)
    surf.blit(ctrl,(SW//2-ctrl.get_width()//2,SH-23))

# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════
def main():
    build_bg()
    arrows=make_arrows(); trees=make_trees(); lamps=make_lamps()
    bh=BoatHouse()
    tlights=[TrafficLight(4,1),TrafficLight(4,-1),TrafficLight(8,1),TrafficLight(8,-1)]
    ssigns=[StopSign(2,1),StopSign(2,-1),StopSign(13,1)]
    ai_cars=[AICar(random.randint(0,len(WP)-3)) for _ in range(10)]
    car=PlayerCar(); human=None; state=DRIVE
    elapsed=0.0; wave_t=0; tick=0; cut_t=0
    cam_ang=car.angle   # smoothed camera heading

    while True:
        clock.tick(FPS); tick+=1; wave_t+=1
        keys=pygame.key.get_pressed()
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE: pygame.quit(); sys.exit()

        # ── Update ───────────────────────────────────────────────────
        if state==DRIVE:
            elapsed+=1/FPS; car.update(keys,tlights)
            for tl in tlights: tl.update()
            for ac in ai_cars: ac.update(tlights)
            if bh.near(car.wx,car.wy) and abs(car.spd)<0.08: state=CUTSCENE; cut_t=FPS*2; car.spd=0.0
        elif state==CUTSCENE:
            car.spd=0.0; cut_t-=1
            if cut_t<=0: human=Human(car.wx+35,car.wy,car.angle); state=WALK
        elif state==WALK: human.update(keys)

        # ── Smooth camera ─────────────────────────────────────────────
        target_ang=car.angle if state in (DRIVE,CUTSCENE) else human.angle
        da=(target_ang-cam_ang+540)%360-180; cam_ang=(cam_ang+da*0.08)%360
        focus_wx=car.wx if state in (DRIVE,CUTSCENE) else human.wx
        focus_wz=car.wy if state in (DRIVE,CUTSCENE) else human.wy
        cam=get_cam(focus_wx,focus_wz,cam_ang)
        cx,cy,cz=cam[0],cam[1],cam[2]

        # ── Draw ─────────────────────────────────────────────────────
        screen.blit(_bg,(0,0))
        draw_road_3d(screen,cam)
        draw_sea_3d(screen,cam,wave_t)
        draw_arrows_3d(screen,cam,arrows,tick)

        # Depth-sorted objects
        objects=[]
        for (wx,wz) in lamps:
            d=math.hypot(wx-cx,wz-cz)
            if d<FOG_E+80: objects.append((d,lambda _wx=wx,_wz=wz:draw_lamp_3d(screen,cam,_wx,_wz)))
        for (wx,wz,r,col) in trees:
            d=math.hypot(wx-cx,wz-cz)
            if d<FOG_E: objects.append((d,lambda _wx=wx,_wz=wz,_r=r,_c=col:draw_tree_3d(screen,cam,_wx,_wz,_r,_c)))
        for ss in ssigns:
            d=math.hypot(ss.wx-cx,ss.wy-cz)
            if d<FOG_E: objects.append((d,lambda _ss=ss:draw_stopsign_3d(screen,cam,_ss)))
        for tl in tlights:
            d=math.hypot(tl.wx-cx,tl.wy-cz)
            if d<FOG_E: objects.append((d,lambda _tl=tl:draw_trafficlight_3d(screen,cam,_tl)))
        dbh=math.hypot(bh.wx-cx,bh.wy-cz)
        if dbh<FOG_E+300: objects.append((dbh,lambda:draw_boathouse_3d(screen,cam,bh)))
        for ac in ai_cars:
            d=math.hypot(ac.wx-cx,ac.wy-cz)
            if d<FOG_E: objects.append((d,lambda _ac=ac:draw_aicars_3d(screen,cam,_ac)))
        if state in (DRIVE,CUTSCENE):
            dc=math.hypot(car.wx-cx,car.wy-cz)
            objects.append((dc,lambda:draw_playercar_3d(screen,cam,car)))
        if state==WALK and human:
            dh=math.hypot(human.wx-cx,human.wy-cz)
            objects.append((dh,lambda:draw_human_3d(screen,cam,human,tick)))
        objects.sort(key=lambda x:x[0],reverse=True)
        for _,fn in objects: fn()

        # Cutscene
        if state==CUTSCENE:
            glass_box(screen,SW//2-220,SH//2-38,440,76,(0,0,0),195)
            m1=F_MED.render("Arrived at the Boat House!",True,(255,255,255))
            screen.blit(m1,m1.get_rect(center=(SW//2,SH//2-14)))
            m2=F_SM.render("Getting out of the car…",True,(155,210,255))
            screen.blit(m2,m2.get_rect(center=(SW//2,SH//2+18)))

        # HUD
        if state==DRIVE:
            draw_hud(screen,car,elapsed,math.hypot(car.wx-bh.wx,car.wy-bh.wy))
        elif state==WALK:
            glass_box(screen,10,10,265,36,(0,0,0),158)
            screen.blit(F_HUD.render("ON FOOT  —  Explore the dock!",True,CYAN_C),(18,18))
            ctrl=F_TINY.render("W/↑ Fwd   S/↓ Back   A/D Turn",True,(145,155,178))
            glass_box(screen,SW//2-ctrl.get_width()//2-8,SH-26,ctrl.get_width()+16,20,(0,0,0),118)
            screen.blit(ctrl,(SW//2-ctrl.get_width()//2,SH-23))

        draw_minimap(screen,car if state!=WALK else None,human if state==WALK else None,bh)
        pygame.display.flip()

if __name__=="__main__":
    main()
