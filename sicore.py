import pygame
pygame.mixer.pre_init(44100, 16, 2, 4096)
pygame.init()
pygame.display.set_caption("MN's Space Invaders")

from os.path import isfile
from siclasses import *
system = GameSystem()
system._setupSizes()
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
    system.AUDIO.music()
    while not system.GAMEOVER:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: system.GAMEOVER = True
        if system.KEYMAP.controller(system):
            system.GAMEOVER = True
        system.refresh()
        system.newFrame()
        ui.ingame(system)
        pygame.display.flip()
        system.CLOCK.tick(system.FRAMERATE)
    system.AUDIO.stopmusic()
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

if __name__=='__main__':
    main()