import pygame
import sicore
from os.path import isfile
import sys

if (len(sys.argv)>1 and sys.argv[1]=='fullscreen'):
    sicore.fullscr = True
    sicore.system = sicore.GameSystem(sicore.fullscr)

class OptionShifter:
    DefaultFreezer = 2

    def __init__(self, opts):
        self.Pointer = 0
        self.Options = opts
        self.Freezer = 0

    def shiftdown(self):
        if self.Freezer==0:
            self.Pointer += 1
            if self.Pointer >= self.Options:
                self.Pointer = 0
        self.Freezer = (self.Freezer+1)%OptionShifter.DefaultFreezer

    def shiftup(self):
        if self.Freezer==0:
            self.Pointer -= 1
            if self.Pointer < 0:
                self.Pointer = self.Options-1
        self.Freezer = (self.Freezer+1)%OptionShifter.DefaultFreezer

class MenuSystem:
    DefaultSETTINGS = [['mysteries','rarely'], ['speed','standard'], ['bases','medium'], ['blank shots','no'], ['bonuses','yes']]

    def __init__(self):
        self.SITE = 0
        self.SETTING = -1
        self.SETDICT = [list(pair) for pair in MenuSystem.DefaultSETTINGS]
        self.MOPS = OptionShifter(4)
        self.COPS = OptionShifter(6)
        self._trank = [['yes', 'no'], ['none', 'small', 'medium', 'big'], ['low', 'standard', 'high'], ['never', 'rarely', 'quite often', 'often']]
        self._tvalue = [[True, False], [None, (40,20), (60,40), (80,60)], [0.7, 1, 2], [0, 0.005, 0.01, 0.02]]

    def _convertrank(self):
        copy = {}
        for i in range(0, len(self.SETDICT)):
            for xp in range(0, len(self._trank)):
                if self.SETDICT[i][1] in self._trank[xp]:
                    copy[str(self.SETDICT[i][0])] = self._tvalue[xp][self._trank[xp].index(self.SETDICT[i][1])]
        return copy

    def switchsite(self):
        self.SITE = self.MOPS.Pointer+1

    def switchsetting(self):
        self.SETTING = self.COPS.Pointer

    def setoption(self):
        if self.SETTING<0 or self.SETTING>=len(self.SETDICT):
            return
        for rk in self._trank:
            if self.SETDICT[self.SETTING][1] in rk:
                i = rk.index(self.SETDICT[self.SETTING][1])
                self.SETDICT[self.SETTING][1] = rk[(i+1)%len(rk)]
                break
        self.SETTING = -1

    def loadCustom(self):
        if MenuSystem.DefaultSETTINGS!=self.SETDICT:
            mods = self._convertrank()
            sicore.Secret.DefaultChance = mods['mysteries']
            sicore.EnemyCluster.SpeedTarget *= mods['speed']
            sicore.EnemyCluster.DefaultSpeed *= mods['speed']
            sicore.BreakableCover.DefaultSize = mods['bases']
            sicore.Projectile.AlwaysHarmful = not mods['blank shots']
            sicore.Secret.GivesBonuses = mods['bonuses']
            return True
        return False

def loadLeader():
    if isfile('leaderboard.txt'):
        with open('leaderboard.txt','r') as f:
            lb = f.readlines()
        vanila = [x for x in lb if (x[0]!='0' or len(x)==1)]
        cst = [x for x in lb if (x[0]=='0' and len(x)>1)]
        if len(lb)>0: return [int(i) for i in vanila],[int(i) for i in cst]
    else:
        return [],[]

def main():
    global localmsys
    localmsys = MenuSystem()
    kmap = [{pygame.K_UP:(lambda a:localmsys.MOPS.shiftup()), pygame.K_DOWN:(lambda a:localmsys.MOPS.shiftdown()), pygame.K_RETURN:(lambda a:localmsys.switchsite())},
        {pygame.K_UP:(lambda a:localmsys.COPS.shiftup()), pygame.K_DOWN:(lambda a:localmsys.COPS.shiftdown()), pygame.K_RETURN:(lambda a:localmsys.switchsetting())}]
    EXITING = False
    pulse = sicore.Pulsar()
    while not EXITING:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                EXITING = True
        sicore.system.SCREEN.fill((0,0,0))
        if sicore.system.KEYMAP.overridden(sicore.system, kmap[0 if localmsys.SITE==0 else 1], True):
            if localmsys.SITE==0: EXITING = True
            else: localmsys.SITE = 0
        if localmsys.SITE==0:
            drawmenu(localmsys.MOPS, 10*next(pulse))
        elif localmsys.SITE==1: 
            localmsys.SITE = 0
            sicore.main(localmsys.loadCustom())
        elif localmsys.SITE==2:
            drawleader()
        elif localmsys.SITE==3:
            drawcustomise(localmsys.COPS, localmsys.SETDICT)
            if localmsys.SETTING==5:
                localmsys.SITE = 0
                localmsys.COPS.Pointer = 0
                localmsys.SETTING = -1
            else:
                localmsys.setoption()
        elif localmsys.SITE==4:
            EXITING = True
        pygame.display.flip()
        sicore.system.CLOCK.tick(sicore.system.FRAMERATE)

def drawleader():
    scores = loadLeader()
    selected = (250,250,250)
    title = (30,240,30)
    UI = sicore.UserInterface(42)
    UI.addsysfont(90)
    elems = []
    tmp = UI.newtext('Leaderboards', font=0, clr=title)
    w = sicore.system.GRID.XBounds[1]/4
    ww = sicore.system.GRID.XBounds[1]*0.75
    h = tmp.get_height()+20
    elems.append( (tmp, (w*2-tmp.get_width()/2,h)) )
    h += 40
    noncustom = sorted(scores[0], reverse=True)
    onlycustom = sorted(scores[1], reverse=True)
    tmp = UI.newtext("Vanilla:", clr=selected)
    h += tmp.get_height()+2
    elems.append( (tmp, (w-tmp.get_width()/2,h)) )
    tmp = UI.newtext("Custom:", clr=selected)
    elems.append( (tmp, (ww-tmp.get_width()/2,h)) )
    hh = float(h)
    if len(onlycustom)<=0:
        tmp = UI.newtext("No high-scores yet", clr=selected)
        h += tmp.get_height()+2
        elems.append( (tmp, (ww-tmp.get_width()/2,h)) )
    for i in range(0,len(onlycustom)):
        tmp = UI.newtext(str(i+1)+' : '+str(onlycustom[i]), clr=selected)
        h += tmp.get_height()+2
        elems.append( (tmp, (ww-tmp.get_width()/2,h)) )
    h = hh
    if len(noncustom)<=0:
        tmp = UI.newtext("No high-scores yet", clr=selected)
        h += tmp.get_height()+2
        elems.append( (tmp, (w-tmp.get_width()/2,h)) )
    for i in range(0,len(noncustom)):
        tmp = UI.newtext(str(i+1)+' : '+str(noncustom[i]), clr=selected)
        h += tmp.get_height()+2
        elems.append( (tmp, (w-tmp.get_width()/2,h)) )
    for e in elems:
        UI.showtext(sicore.system, e[0], e[1])

def drawcustomise(ops, setdc):
    selected = (250,250,250)
    unselected = (140,140,140)
    title = (30,240,30)
    opts = [unselected]*(len(setdc)+1)
    opts[ops.Pointer] = selected
    UI = sicore.UserInterface(62)
    UI.addsysfont(90)
    elems = []
    tmp = UI.newtext('MagNum Custom', font=0, clr=title)
    w = sicore.system.GRID.XBounds[1]/4
    ww = sicore.system.GRID.XBounds[1]*0.75
    h = tmp.get_height()+20
    elems.append( (tmp, (w*2-tmp.get_width()/2,h)) )
    h += 30
    row = 0
    for sd in setdc:
        tmp = UI.newtext(sd[0], clr=opts[row])
        h += tmp.get_height()+20
        elems.append( (tmp, (w-tmp.get_width()/2,h)) )
        tmp = UI.newtext(sd[1], clr=opts[row])
        elems.append( (tmp, (ww-tmp.get_width()/2,h)) )
        row += 1
    tmp = UI.newtext('back', clr=opts[row])
    h += tmp.get_height()+20
    elems.append( (tmp, (w*2-tmp.get_width()/2,h)) )
    for e in elems:
        UI.showtext(sicore.system, e[0], e[1])

def drawmenu(ops, pulse):
    selected = (250,250,250)
    unselected = (140,140,140)
    title = (30,240,30)
    opts = [unselected]*4
    opts[ops.Pointer] = selected
    UI = sicore.UserInterface(72)
    UI.addsysfont(90)
    elems = []
    tmp = UI.newtext('SPACEINVADERS', font=0, clr=title)
    w = sicore.system.GRID.XBounds[1]/2
    h = tmp.get_height()+20
    elems.append( (tmp, (w-tmp.get_width()/2,h+pulse)) )
    tmp = UI.newtext('MagNum', font=0, clr=title)
    h += tmp.get_height()+5
    elems.append( (tmp, (w-tmp.get_width()/2,h+pulse)) )
    h += 30
    row = 0
    for t in ['play','leaderboards','customise','exit']:
        tmp = UI.newtext(t, clr=opts[row])
        h += tmp.get_height()+20
        elems.append( (tmp, (w-tmp.get_width()/2,h)) )
        row += 1
    for e in elems:
        UI.showtext(sicore.system, e[0], e[1])

if __name__=="__main__":
    main()