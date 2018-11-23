import pygame
pygame.init()
pygame.display.set_caption("MN's Space Invaders")

from os.path import isfile
from siclasses import *
system = GameSystem()
ui = UserInterface(64)
fullscr = False

def main(custom=False):
    global system
    global ui
    global fullscr
    system = GameSystem(fullscr)
    ui = UserInterface(64)
    if isfile('leaderboard.txt'):
        with open('leaderboard.txt','r') as f:
            lb = f.readlines()
        if len(lb)>0: system.HIGHSCORE = max([int(i) for i in lb])
    else:
        lb = []
    while not system.GAMEOVER:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: system.GAMEOVER = True
        system.SCREEN.fill((0,0,0))
        if system.KEYMAP.controller(system):
            system.GAMEOVER = True
        system.refresh()
        newFrame()
        ui.ingame(system)
        pygame.display.flip()
        system.CLOCK.tick(system.FRAMERATE)
    EXITING = False
    lb.append(("0" if custom else "")+str(system.SCORE)+"\n")
    with open('leaderboard.txt','w') as f:
        f.writelines(lb)
    while not EXITING:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: EXITING = True
        if system.KEYMAP.overridden(system, {'a':'a'}):
            EXITING = True
        ui.gameover(system)
        pygame.display.flip()
        system.CLOCK.tick(system.FRAMERATE)

def newFrame():
    system.PLAYER.draw(system)
    system.OPONNENTS.draw(system)
    if system.MYSTERY!=None:
        system.MYSTERY.draw(system)
    for i in system.PROJECTILES:
        i.draw(system)
    for i in system.BASES:
        i.draw(system)

if __name__=='__main__':
    main()