#!/usr/bin/python3
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import sys, pygame
import random
import numpy as np
import asyncio
import sys

sys.setrecursionlimit(100000)
pygame.init()

np.set_printoptions(threshold=sys.maxsize)

font = pygame.font.SysFont('freesansbold.ttf', 24)

img = font.render('XXXXX', True, (255, 255, 255), (0, 0, 0))
size = width, height = 640, 480 + img.get_rect().height
pygame.display.set_mode(size)

percent = 0.0

def updateStatus():
    global percent
    global hazardCount
    global font
    global img
    global lives

    s = f"Level: {hazardCount}      Covered:   {percent*100:.1f}  Lives: {lives}     "
    img = font.render(s, True, (255, 255, 255), (0, 0, 0))

def checkfield(g, x, y):
#    print(f"{x=}, {y=}")
    if g[x, y] == 0 or g[x, y] == 10:
        g[x, y] = 26
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if (i == 0 and j == 0) or x + i < 0 or x + i >= 80 or y + j < 0 or y + j >= 60:
                    continue
                checkfield(g, x + i, y + j)
        g[x, y] = 26

def reevaluate(g):
    global width
    global height
    global hazards

    for h in hazards:
        checkfield(g, h.x, h.y)
#    print(g)
#    sleep(10)
    g[np.where(g[:, :] == 0)] = 1
    g[np.where(g[:, :] >= 16)] = 0
    g[np.where(g[:, :] == 2)] = 1
    return float(np.count_nonzero(g == 1)) / (80 * 60)

class Hazard:
    def __init__(self):
        self.x, self.y = random.randint(1, 78), random.randint(1, 58)
        self.sx, self.sy = random.randint(0, 1), random.randint(0, 1)
        if self.sx == 0:
            self.sx = -1
        if self.sy == 0:
            self.sy = -1
        self.start()

    def start(self):
        self.task = asyncio.create_task(self.run())

    def step(self, game):
        global terminated
        global won
        global stepEvent
        global players

        nx = self.x + self.sx
        ny = self.y + self.sy
        if game[nx, ny] == 2 or players[0].x == nx and players[0].y == ny and game[players[0].x, players[0].y] == 0:
            terminated = True
            won = False
            stepEvent.set()
        if game[nx, ny] != 0:
            if game[self.x + self.sx, self.y] != 0:
                self.sx = -self.sx
            if game[self.x, self.y + self.sy] != 0:
                self.sy = -self.sy
            nx = self.x + self.sx
            ny = self.y + self.sy
        game[self.x, self.y] = 0
        if game[nx, ny] == 0:
            self.x = nx
            self.y = ny
        else:
            self.sx = -self.sx
            self.sy = -self.sy
        game[self.x, self.y] = 10
#        print(f"hazard {self.x=}, {self.y=}, {self.sx=}, {self.sy=}, {nx=}, {ny=}, {game[nx, ny]=}")

    async def run(self):
        global game
        global terminated
        global stepEvent

        while not terminated:
            await stepEvent.wait()
            stepEvent.clear()
            self.step(game)

    async def finish(self):
        await self.task

class Player:
    def __init__(self):
        self.x, self.y = 39, 0
        self.sx, self.sy = 0, 0
        self.task = asyncio.create_task(self.run())
        self.linedone = False

    def setSpeed(nsx, nsy):
        self.sx = nsx
        self.sy = nsy

    def step(self, game):
        global terminated
        global stepEvent 
        global percent
        global lives

        nx = self.x + self.sx
        ny = self.y + self.sy
        if nx < 0 or nx >= 80:
            self.sx = 0
            nx = self.x
        if ny < 0 or ny >= 60:
            self.sy = 0
            ny = self.y
        if game[self.x, self.y] == 0:
            game[self.x, self.y] = 2
            self.linedone = True
        if game[self.x, self.y] == 1 and self.linedone:
            self.linedone = False
            self.sx, self.sy = 0, 0
            nx, ny = self.x, self.y
            npercent = reevaluate(game)
            if npercent > 0.5 and percent <= 0.5:
                lives += 1
            percent = npercent
            updateStatus()
            if percent >= 0.75:
                terminated = True
                lives += 1
                stepEvent.set()
        self.x, self.y = nx, ny
#        print(f"player {self.x=}, {self.y=}")

    def keydown(self, key):
        speeds = { pygame.K_DOWN: (0, 1), pygame.K_UP: (0, -1), pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0) }
        if key in speeds.keys():
            self.sx = speeds[key][0]
            self.sy = speeds[key][1]
#            print(f"player {self.x=}, {self.y=}")

    async def run(self):
        global game
        global terminated
        global stepEvent

        while not terminated:
            await stepEvent.wait()
            stepEvent.clear()
            self.step(game)

    async def finish(self):
        await self.task

hazardCount = 1

def redraw():
    brick_size = 8
    global game
    
    colours = { 0: (0, 0, 0), 1: (255, 255, 255), 10: (255, 0, 0), 2: (128, 128, 0) }
    sf = pygame.display.get_surface()
    for x in range(80):
        for y in range(60):
            if game[x, y] != -1:
                pygame.draw.rect(sf, colours[game[x, y]], pygame.Rect(x * brick_size, y * brick_size, brick_size, brick_size))
    pygame.draw.rect(sf, (0, 255, 0), pygame.Rect(players[0].x * brick_size, players[0].y * brick_size, brick_size, brick_size)) 
    sf.blit(img, (0, 60 * brick_size + 1))
    pygame.display.flip()

async def main():
    global terminated
    global game
    global hazards
    global players
    global stepEvent
    global quit
    global percent
    global won
    global lives
    global hazardCount

    pygame.display.set_mode(size)
    pygame.display.set_caption('Xonix - a simple Python remake')

    stepEvent = asyncio.Event()

    if len(hazards) == 0:
        for i in range(hazardCount):
            hazards.append(Hazard())
    else:
        for i in range(hazardCount):
            hazards[i].start()

    players.append(Player())

    updateStatus()

    while not terminated:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                terminated = True
                quit = True
            elif e.type == pygame.KEYDOWN:
                players[0].keydown(e.key)
                if e.key == pygame.K_q:
                    terminated = True
                    quit = True
                if e.key == pygame.K_r:
                    terminated = True
                    won = False
                    lives = 0
                    hazardCount = 1
        stepEvent.set()
        redraw()
        await asyncio.sleep(0.01)

    for h in hazards:
        await h.finish()
    await players[0].finish()

    del players[0]
    if won or lives == 0:
        for i in range(hazardCount):
            del hazards[0]

quit = False

lives = 0

won = True

hazards = []

while not quit:
    terminated = False
    if won or lives == 0:
        game = np.zeros((80, 60), dtype='B')

        game[0, :] = [ 1 for i in range(60) ]
        game[79, :] = [ 1 for i in range(60) ]
        game[:, 0] = [ 1 for i in range(80) ]
        game[:, 59] = [ 1 for i in range(80) ]
        percent = 0
    elif not won:
        lives -= 1
        game[np.where(game[:, :] == 2)] = 0
        game[np.where(game[:, :] == 10)] = 0

    won = True

    stepEvent = None
    
    players = []
    
    asyncio.run(main())

    if won:
        hazardCount += 1