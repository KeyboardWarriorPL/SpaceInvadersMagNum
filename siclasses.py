import pygame
import os
import random
random.seed()

#Game mechanics classes
class GameSystem:
    def __init__(self, fullscr=False, resol=(800,600)):
        self.CLOCK = pygame.time.Clock()
        self.FRAMERATE = 25
        self.RESOLUTION = resol
        if (fullscr):
            self.SCREEN = pygame.display.set_mode(resol, pygame.FULLSCREEN)
        else:
            self.SCREEN = pygame.display.set_mode(resol)
        self.GRID = MapGrid(resol, 10+5+2)
        self.GAMEOVER = False
        self.PLAYER = Player((resol[0]/2,self.GRID.Rows))
        self.BASES = [BreakableCover((bcx-BreakableCover.DefaultSize[0]/2,resol[1]-Player.DefaultSize[1]*3.5)) for bcx in [resol[0]/5,resol[0]/2,resol[0]*0.8]] if BreakableCover.DefaultSize!=None else []
        self.SCORE = 0
        self.HIGHSCORE = 0
        self._clusterstart = 1
        self.OPONNENTS = EnemyCluster(11, (1,2,2), (0,self._clusterstart))
        self.PROJECTILES = []
        self.MYSTERYCHANCE = Secret.DefaultChance
        self.MYSTERY = None
        self.BONUSES = []
        self.KEYMAP = KeyMapper([pygame.K_SPACE, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_RETURN, pygame.K_ESCAPE])
        self.IMAGES = {}
        self.load_images()

    def load_images(self):
        imagestuple = [(f, os.path.join('resources', f)) for f in os.listdir('resources') if os.path.isfile(os.path.join('resources', f))]
        for t in imagestuple:
            self.IMAGES[str(t[0])] = pygame.image.load(t[1])

    def new_cluster(self):
        self._clusterstart += 1
        if (self._clusterstart > self.GRID.Rows - 6):
            self._clusterstart = 1
        self.OPONNENTS = EnemyCluster(11, (1,2,2), (0,self._clusterstart))

    def refresh(self):
        if len(self.OPONNENTS)<=0:
            self.new_cluster()
        self._projectileTest()
        self._canfireTest()
        if self.MYSTERY!=None:
            self.MYSTERY.fly(self)
        self.OPONNENTS.invade(self)
        for i in self.BASES:
            i.update(self)

    def _canfireTest(self):
        if len(self.PROJECTILES) >= 4:
            self.PLAYER.CanFire = False
            self.OPONNENTS.CanFire = False
        else:
            self.PLAYER.CanFire = len([x for x in self.PROJECTILES if x.PlayerOwned]) < 1
            self.OPONNENTS.CanFire = len([x for x in self.PROJECTILES if not x.PlayerOwned]) < 3

    def _projectileTest(self):
        for p in self.PROJECTILES:
            if p.Y<=0 or p.Y>self.GRID.YBounds[1]:
                self.PROJECTILES.remove(p)
            if p not in self.PROJECTILES:
                continue
            p.update(self)
            self.OPONNENTS.kill(self, p)
            if (self.MYSTERY!=None and p.overlap(self.MYSTERY,self)):
                self.MYSTERY.destroy(self)
            if (p.overlap(self.PLAYER,self) and p.Harmful):
                self.PLAYER.kill(self)
                self.PROJECTILES.remove(p)

class MapGrid:
    def __init__(self, res, rows):
        self.Rows = rows
        self.XBounds = (1,res[0])
        self.YBounds = (40,res[1]-20)

    def projection(self, x, y):
        return (x, y * (self.YBounds[1]-self.YBounds[0])/self.Rows)

class KeyMapper:
    def __init__(self, keylist):
        self.Keys = keylist
        self._keysdown = []

    def overridden(self, gs, actions, keydown=False):
        pressed = pygame.key.get_pressed()
        for k in self.Keys:
            if pressed[k]:
                if not keydown:
                    if k in actions.keys():
                        actions[k](gs)
                if (k not in self._keysdown):
                    if keydown:
                        if k in actions.keys():
                            actions[k](gs)
                        self._keysdown.append(k)
                    if k==pygame.K_ESCAPE:
                        self._keysdown.append(k)
                        return True
            elif k in self._keysdown:
                self._keysdown.remove(k)
        return False

    def controller(self, gs):
        def right(g):
            g.PLAYER.X = (g.PLAYER.X+10 if g.GRID.XBounds[1]>g.PLAYER.X+g.PLAYER.Size[0] else g.PLAYER.X)
        def left(g):
            g.PLAYER.X = (g.PLAYER.X-10 if g.GRID.XBounds[0]<g.PLAYER.X else g.PLAYER.X)
        a = {**dict.fromkeys([pygame.K_SPACE, pygame.K_UP],(lambda g: g.PLAYER.fire(g))), pygame.K_LEFT:left, pygame.K_RIGHT:right}
        return self.overridden(gs, a)

#Graphics classes
class Drawable:
    def __init__(self, pos, size, clr, g=False, img=None):
        self.X = pos[0]
        self.Y = pos[1]
        self.Size = size
        self.Paint = clr
        self.Image = img
        self._grid = g

    def overlap(self, other, gs):
        sfcrds = gs.GRID.projection(self.X, self.Y) if self._grid else (self.X, self.Y)
        otcrds = gs.GRID.projection(other.X, other.Y) if other._grid else (other.X, other.Y)
        chck = lambda selfx,selfsize,otherx,othersize: (otherx+othersize>selfx and otherx<selfx+selfsize)
        if chck(sfcrds[0], self.Size[0], otcrds[0], other.Size[0]):
            return chck(sfcrds[1], self.Size[1], otcrds[1], other.Size[1])
        return False

    def move(self, step = (10,0)):
        self.X += step[0]
        self.Y += step[1]
        
    def draw(self, gs):
        if self.Image!=None and self.Image in gs.IMAGES.keys():
            tmpimg = pygame.transform.scale(gs.IMAGES[self.Image], self.Size)
            tmpimg.fill(self.Paint, special_flags=pygame.BLEND_MULT)
            if self._grid:
                coords = gs.GRID.projection(self.X, self.Y)
                gs.SCREEN.blit(tmpimg, (coords[0], coords[1]))
            else:
                gs.SCREEN.blit(tmpimg, (self.X, self.Y))
        else:
            tmprect = None
            if self._grid:
                coords = gs.GRID.projection(self.X, self.Y)
                tmprect = pygame.Rect(coords[0],coords[1],self.Size[0],self.Size[1])
            else:
                tmprect = pygame.Rect(self.X,self.Y,self.Size[0],self.Size[1])
            pygame.draw.rect(gs.SCREEN, self.Paint, tmprect)

class UserInterface:
    def __init__(self, fsize):
        self.DefaultFont = pygame.font.SysFont(None, fsize)
        self.Fonts = []

    def addsysfont(self, fsize):
        self.Fonts.append(pygame.font.SysFont(None, fsize))

    def newtext(self, val, aa=False, clr=(255,255,255), font=None):
        if font==None:
            txt = self.DefaultFont.render(val, aa, clr)
        else:
            txt = self.Fonts[font].render(val, aa, clr)
        return txt

    def showtext(self, gs, txt, pos):
        gs.SCREEN.blit(txt, pos)

    def ingame(self, gs):
        txt = self.newtext("High-score "+str(gs.HIGHSCORE), False, (240,240,240))
        self.showtext(gs, txt, (10, 10))
        txt = self.newtext(str(gs.SCORE), False, (0,240,0))
        self.showtext(gs, txt, (gs.RESOLUTION[0]-10-txt.get_width(), 10))
        for i in range(0,gs.PLAYER.Lives):
            pygame.draw.rect(gs.SCREEN, (0,230,0), pygame.Rect(gs.RESOLUTION[0]-i*25-30,txt.get_height()+10,20,20))
    
    def gameover(self, gs):
        txt = self.newtext("GAME OVER", True, (240,0,0))
        self.showtext(gs, txt, ((gs.RESOLUTION[0]//2)-txt.get_width()//2,(gs.RESOLUTION[0]//2)-txt.get_height()//2))

def Pulsar(tempo=0.04):
    ms = 0.0
    dc = 1
    while True:
        yield ms
        ms += tempo*dc
        if ms>=1: dc = -1.0
        elif ms<=-1: dc = 1.0

class Animation:
    def __init__(self, interface, gs, frames=60):
        self.Text = None
        self.Image = None
        self.Pulsation = Pulsar()
        self.UInterface = interface
        self.GSystem = gs
        self.Frames = frames
        self._passed = 0

    def __iter__(self):
        return self

    def __next__(self):
        if (self._passed>=self.Frames):
            raise StopIteration
        else:
            p = (next(self.Pulsation)+1)/2
            if self.Text!=None:
                self.Text = (self.Text[0], self.Text[1], (self.Text[2][0]*p, self.Text[2][1]*p, self.Text[2][2]*p))
                self.UInterface.newtext(*self.Text)
            if self.Image!=None and self.Image in self.GSystem.IMAGES.keys():
                self.GSystem.SCREEN.blit()
            self._passed += 1
            return (self.Text, self.Image)

class EventPauser:
    def __init__(self, anim):
        self.Animation = anim

    def start(self, gs):
        for frame in self.Animation:
            pygame.display.flip()
            gs.CLOCK.tick(gs.FRAMERATE)

#Missiles classes
class Projectile(Drawable):
    DefaultSize = (4,12)
    DefaultColor = (200,0,0)
    AlwaysHarmful = True
    
    def __init__(self, start, plo=False):
        self.PlayerOwned = plo
        self.Speed = 300
        self.Strength = 1
        self.Harmful = True
        super().__init__(start, Projectile.DefaultSize, Projectile.DefaultColor)

    def update(self, gs):
        if self.PlayerOwned:
            self.Y -= self.Speed / gs.FRAMERATE
        else:
            self.Y += self.Speed / gs.FRAMERATE

    def splash(self): #TO DO man!
        return []

class MissileFast(Projectile):
    def __init__(self, start):
        super().__init__(start, False)
        self.Speed *= 1.5

class MissileHeavy(Projectile):
    def __init__(self, start):
        super().__init__(start, False)
        self.Speed *= 1.5
        self.Strength *= 2

#Player classes
class Player(Drawable):
    DefaultSize = (30,30)
    DefaultColor = (20,150,20)
    DefaultImage = 'turret.png'

    def __init__(self, pos):
        self.Lives = 3
        self.CanFire = True
        super().__init__(pos, Player.DefaultSize, Player.DefaultColor, True, Player.DefaultImage)

    def fire(self, gs):
        if self.CanFire:
            coords = gs.GRID.projection(self.X, self.Y)
            pro = Projectile((coords[0] + self.Size[1]/2, coords[1]-1), True)
            pro.Paint = self.Paint
            gs.PROJECTILES.append(pro)
            self.CanFire = False

    def kill(self, gs):
        self.Lives -= 1
        if self.Lives <= 0:
            gs.GAMEOVER = True

class BreakableCover:
    DefaultSize = (60,40)
    DefaultColor = (20,150,20)

    def __init__(self, pos):
        pos = (pos[0], pos[1]-BreakableCover.DefaultSize[1]/2)
        self._position = pos
        self._bricksize = (6,6)
        self.Bricks = [Drawable((x+pos[0],y+pos[1]),self._bricksize,BreakableCover.DefaultColor) for x in range(0,BreakableCover.DefaultSize[0],self._bricksize[0]) for y in range(0,BreakableCover.DefaultSize[1],self._bricksize[1])]

    def __len__(self):
        return len(self.Bricks)

    def update(self, gs):
        for b in self.Bricks:
            omit = False
            for pts in gs.PROJECTILES:
                if pts.overlap(b, gs):
                    self.Bricks.remove(b)
                    gs.PROJECTILES.remove(pts)
                    omit = True
            if omit or gs.OPONNENTS.limit()[3]<gs.GRID.Rows/2:
                continue
            for op in gs.OPONNENTS.Enemies:
                if op.overlap(b, gs):
                    self.Bricks.remove(b)

    def draw(self, gs):
        for b in self.Bricks:
            b.draw(gs)

#ENEMIES CLASSES
class EnemyCluster:
    SpeedTarget = 20
    DefaultSpeed = 0.5
    Coefficient = 16

    def __init__(self, columns, cluster, pos):
        self.CanFire = True
        self.FireChance = 0.03
        self.Enemies = [Genius((x*60,y)) for x in range(0,columns) for y in range(0,cluster[0])]+[Clever((x*60,y)) for x in range(0,columns) for y in range(cluster[0],cluster[0]+cluster[1])]+[Stupid((x*60,y)) for x in range(0,columns) for y in range(cluster[0]+cluster[1],cluster[0]+cluster[1]+cluster[2])]
        self._amount = len(self.Enemies)
        self._direction = 1
        self.Speed = EnemyCluster.DefaultSpeed
        self.move(pos)

    def __len__(self):
        return len(self.Enemies)

    def getSpeed(self):
        return (((self._amount - len(self) + 1) / self._amount)**EnemyCluster.Coefficient) * EnemyCluster.SpeedTarget + self.Speed

    def move(self, step = (10,0)):
        for e in self.Enemies:
            e.move(step)

    def draw(self, gs):
        for e in self.Enemies:
            e.draw(gs)

    def limit(self):
        if len(self)>0:
            l = [e.X for e in self.Enemies]
            t = [e.Y for e in self.Enemies]
            return (min(l), max(l), min(t), max(t))
        else:
            return (0,0,0,0)

    def fire(self, gs):
        if self.CanFire and random.random()<self.FireChance and len(self)>0:
            al = random.choice(self.Enemies)
            al.fire(gs)

    def kill(self, gs, shot):
        for e in self.Enemies:
            if shot.PlayerOwned:
                if shot.overlap(e,gs):
                    if random.random()<gs.MYSTERYCHANCE and gs.MYSTERY==None:
                        gs.MYSTERY = Secret((40,1))
                    e.destroy(gs)
                    if shot in gs.PROJECTILES: gs.PROJECTILES.remove(shot)
            elif not Projectile.AlwaysHarmful:
                if shot.overlap(e,gs): shot.Harmful = False

    def invade(self, gs):
        if len(self)<=0:
            return
        limv = self.limit()
        if limv[1]+self.Enemies[0].Size[0]>gs.GRID.XBounds[1]:
            self._direction = -1
            self.move((0,1))
        elif limv[0]<gs.GRID.XBounds[0]:
            self._direction = 1
            self.move((0,1))
        if limv[3]>=gs.GRID.Rows: gs.GAMEOVER = True
        self.move((self.getSpeed()*self._direction,0))
        self.fire(gs)

class Alien(Drawable):
    DefaultSize = (30,30)
    DefaultColor = (250,200,200)

    def __init__(self, points, pos):
        self.Reward = points
        super().__init__(pos, Alien.DefaultSize, Alien.DefaultColor, True)

    def fire(self, gs):
        coords = gs.GRID.projection(self.X, self.Y)
        protype = random.choice([Projectile, MissileFast, MissileHeavy])
        gs.PROJECTILES.append(protype((coords[0]+self.Size[0]/2, coords[1]+1+self.Size[1])))

    def destroy(self, gs):
        gs.SCORE += self.Reward
        gs.OPONNENTS.Enemies.remove(self)

class Stupid(Alien):
    DefaultImage = 'stupid.png'

    def __init__(self, pos):
        super().__init__(10, pos)
        self.Image = Stupid.DefaultImage

class Clever(Alien):
    DefaultImage = 'clever.png'

    def __init__(self, pos):
        super().__init__(20, pos)
        self.Image = Clever.DefaultImage

class Genius(Alien):
    DefaultImage = 'genius.png'

    def __init__(self, pos):
        super().__init__(30, pos)
        self.Image = Genius.DefaultImage

#BONUS system
class Secret(Drawable):
    DefaultSize = (30,30)
    DefaultColor = (220,220,220)
    DefaultChance = 0.005
    GivesBonuses = True
    DefaultImage = 'secret.png'

    def __init__(self, pos, rws=[50,100,150]):
        self.Rewards = rws
        self.Speed = random.random() * 9 + 1
        self._direction = 1
        super().__init__(pos, Secret.DefaultSize, Secret.DefaultColor, True, Secret.DefaultImage)

    def fly(self, gs):
        if self.Size[0]+self.X>gs.GRID.XBounds[1]:
            self._direction = -1
        elif self.X<gs.GRID.XBounds[0]:
            self._direction = 1
        self.move((self._direction*self.Speed,0))

    def destroy(self, gs):
        if len(gs.BONUSES)>0:
            random.choice(gs.BONUSES).activate()
        else:
            gs.SCORE += random.choice(self.Rewards)
        gs.MYSTERY = None
    
class Bonus:
    def __init__(self):
        print('ni ma! ha ha')