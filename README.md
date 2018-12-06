# furniture

Typesetting and layout utilities for drawing and animating in drawBot.

## Why does this exist?

Because doing animations in drawBot is awesome, but also requires a lot of boilerplate and — when you make a long animation — can be slow and memory-intensive since the rendered frames are kept in memory in preparation for the video compilation at the end. So instead of rendering all your frames within a single drawBot context, using furniture.animation you can set up the animation in such a way that it can be rendered frame-by-frame from the command-line. This is much faster than rendering all your frames within the app, and also means you can render frames in parallel on multiple cores of your machine. (Well, not yet, I'm working on that, although you can already do it manually just by opening multiple terminal windows, i.e. by breaking your animation rendering into small chunks, i.e. `python example.py --start=0 --end=50` then `python example.py --start=50` in another (not including an `--end`) means it'll just render all the frames to the end.

Also, I just really love slicing & dicing rectangles with the style of code that `furniture.geometry` provides. (More on that below.)

## Features

- `furniture.geometry` provides a simple `Rect` structure for slicing & dicing rectangles quickly and easily (loosely based on the use of `CGGeometry` in AppKit programming)
- `furniture.animation` provides a simpel `Animation` object for parameterizing animations via a single frame-wise callbacks that operate in a stateless fashion (meaning any frame of your drawing can be rendered at any time). That is, you build an `Animation` object by giving it a `draw` function, which in your code would look like `def draw(frame):` and within that function you get the context `frame` object (an `AnimationFrame`) that has properties like `frame.i` (index of the current frame), as well as `frame.doneness` (a 0-1 float that gives the "doneness" of the animation as a function of its length, which is an argument provided to the original `Animation` constructor) — see `example.py` for an example, or below:

```
from furniture.animation import Animation
from drawBot import *

def draw(frame):
    fill(random(), random(), random())
    rect(*frame.page.take(frame.doneness, "minx"))

animation = Animation(draw, length=100, fps=23.976, burn=True)
animation.storyboard(0, 1, 50)
```

If you run that code in drawBot itself, you'll see the frames specified in `.storyboard`, i.e. frames 0, 1, and 50. If you run that code from the command line, i.e. `python example.py --start=0 --folder=frames`, this will render pngs of every one of your frames into a folder called `frames`.
