# for cache-busting within drawBot
#import furniture.animation
#import importlib
#importlib.reload(furniture.animation)

from furniture.animation import Animation
from drawBot import *

def draw(frame):
    fill(random(), random(), random())
    rect(*frame.page.take(frame.doneness, "minx"))

animation = Animation(draw, length=100, fps=23.976, burn=True)
animation.storyboard(0, 1, 50)