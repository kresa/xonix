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
size = width, height = 640, 480

pygame.display.set_mode(size)

def checkfield(g, x, y, val):
    if g[x, y] == 0:
#        print(f"enter checkfield {x=}, {y=}, {g[x, y]=}")
        if val == 26:
            val = 10
        if val == 10:
            g[x, y] = 26
        else:
            g[x, y] = 16
        rv = val
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if (i == 0 and j == 0) or x + i < 0 or x + i >= 80 or y + j < 0 or y + j >= 60:
                    continue
                r = checkfield(g, x + i, y + j, rv)
                if r == 10 or r == 26:
                    rv = 10
        if rv == 10:
            g[x, y] = 26
        else:
            g[x, y] = 1
#        print(f"checkfield {x=}, {y=}, {rv=}")
        return rv
    else:
#        print(f"return checkfield {x=}, {y=}, {g[x, y]=}")
        return g[x, y]

def reevaluate(g):
    global width
    global height

    for x in range(80):
        for y in range(60):
            checkfield(g, x, y, 0)
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
        self.task = asyncio.create_task(self.run())

    def step(self, game):
        global terminated
        global won
        global stepEvent
        global players

        nx = self.x + self.sx
        ny = self.y + self.sy
        if game[nx, ny] == 2 or players[0].x == nx and players[0].y == ny:
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
            if reevaluate(game) >= 0.75:
                terminated = True
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
    pygame.display.flip()

async def main():
    global terminated
    global game
    global hazards
    global players
    global stepEvent
    global quit

    pygame.display.set_mode(size)
    pygame.display.set_caption('Xonix - a simple Python remake')

    stepEvent = asyncio.Event()

    for i in range(hazardCount):
        hazards.append(Hazard())

    players.append(Player())


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
        stepEvent.set()
        redraw()
        await asyncio.sleep(0.01)

    for h in hazards:
        await h.finish()
    await players[0].finish()

    del players[0]
    for i in range(hazardCount):
        del hazards[0]

quit = False

while not quit:
    terminated = False
    won = True
    game = np.zeros((80, 60), dtype='B')

    game[0, :] = [ 1 for i in range(60) ]
    game[79, :] = [ 1 for i in range(60) ]
    game[:, 0] = [ 1 for i in range(80) ]
    game[:, 59] = [ 1 for i in range(80) ]

    stepEvent = None
    
    hazards = []

    players = []
    
    asyncio.run(main())
    if won:
        hazardCount += 1