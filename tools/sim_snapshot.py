"""Run a badge25 app in the simulator headlessly and save screenshots.

usage: python tools/sim_snapshot.py <app_dir> <out_dir> [-C system_root (default: ./system)] [--keys "30:a,60:up"] [--shots 20,90] [--frames 120]
  --keys   frame:key pairs to press (a b c up down h)  — key is held for 5 frames
  --shots  frame numbers at which to save a screenshot
"""
import argparse, os, sys
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(HERE, "..", "vendor", "home", "badge25", "simulator")
sys.path.insert(0, os.path.abspath(SIM))
import pygame
import badge_simulator as bs

p = argparse.ArgumentParser()
p.add_argument("app"); p.add_argument("out")
p.add_argument("--keys", default=""); p.add_argument("--shots", default="30")
p.add_argument("--frames", type=int, default=0)
p.add_argument("-C", dest="root", default=os.path.join(HERE, "..", "system"))
a = p.parse_args()
keymap = {"a": pygame.K_a, "b": pygame.K_b, "c": pygame.K_c, "up": pygame.K_UP,
          "down": pygame.K_DOWN, "h": pygame.K_h}
presses = {}
for item in filter(None, a.keys.split(",")):
    f, k = item.split(":"); presses[int(f)] = keymap[k]
shots = sorted(int(s) for s in a.shots.split(","))
last = a.frames or (max(shots + list(presses)) + 5)
os.makedirs(a.out, exist_ok=True)

orig = bs.IO.update
state = {"frame": 0}
def patched(self):
    f = state["frame"]
    if f in presses:
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=presses[f]))
    for pf, k in presses.items():
        if f == pf + 5:
            pygame.event.post(pygame.event.Event(pygame.KEYUP, key=k))
    orig(self)
    if f in shots:
        bs.screen.take_screenshot()
    if f >= last:
        pygame.quit(); sys.exit(0)
    state["frame"] = f + 1
bs.IO.update = patched
sys.argv = ["badge_simulator.py", a.app, "-C", os.path.abspath(a.root), "--screenshots", os.path.abspath(a.out)]
bs.main()
