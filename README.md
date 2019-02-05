# furniture

Layout, animation, and typesetting utilities for drawing and animating in drawBot.

Basically just code I reuse every time I make an animation (or anything) with drawBot.

## Why does this exist?

### furniture.animations

Doing animations in drawBot is awesome, but it also requires a lot of boilerplate and — when you make a long animation — the render process can be slow and memory-intensive (since the rendered frames are kept in memory in preparation for the video compilation at the end). So instead of rendering all your frames within a single drawBot context, using furniture.animation you can set up the animation in such a way that it can be rendered frame-by-frame from the command-line. This is much faster than rendering all your frames within the app, and also means you can render frames in parallel on multiple cores of your machine. (Well, only sort-of at the moment, it requires running multiple Python processes.)

**_Caveat_** If you know of a better/alternative library for this, please let me know!

### furniture.geometry

I really love slicing & dicing rectangles with the style of code that `furniture.geometry` provides. (More on that below, but really it's just some functions for dividing/insetting/offsetting simple rectangles that can be used directly with drawBot primitives, because the `Rectangle` class implements iterable access. Incidentally, I've since found that this code is quite similar to the `arrayTools` module in `fontTools.misc`, which you can see here, and can be used on `Rectangle` objects: https://github.com/fonttools/fonttools/blob/master/Lib/fontTools/misc/arrayTools.py

## Features

- `furniture.geometry` provides a simple `Rect` structure for slicing & dicing rectangles quickly and easily (loosely based on the use of `CGGeometry` in AppKit programming)
- `furniture.animation` provides a simple `Animation` object for parameterizing animations via a single frame-wise callback that operates in a stateless fashion (meaning any frame of your drawing can be rendered at any time). That is, you build an `Animation` object by giving it a `draw` function, which in your code would look like `def draw(frame):` and within that function you get the context `frame` object (an `AnimationFrame`) that has properties like `frame.i` (index of the current frame), as well as `frame.doneness` (a 0-1 float that gives the "doneness" of the animation as a function of its length, which is an argument provided to the original `Animation` constructor) — see `example.py` for an example, or below:

```
from furniture.animation import Animation
from drawBot import *

def draw(frame):
    fill(random(), random(), random())
    rect(*frame.page.take(frame.doneness, "minx"))

animation = Animation(draw, length=100, fps=23.976, fmt="pdf", burn=True, file=__file__)
animation.storyboard({}, 0, 1, 50)
```

The `burn=True` there just adds a little ~seconds / frame index / render date~ box in the lower right-hand corner of the video, for easier debugging if you need to nudge things around once you’ve viewed them in After Effects.

If you run that code in drawBot itself, you'll see the frames specified in `.storyboard`, i.e. frames 0, 1, and 50. If you run that code from a headless Python process, i.e. `import animationfile.py; animationfile.animation.render(start=0);`, this will render pdfs of every one of your frames into a folder called `frames`.

## Viewing animation output

Though the written frames can be `ffmpeg`'d into a video, I've found that possibly the best way to get a quick and easy preview of your rendered work is to grab a copy of Adobe After Effects (free if you have a CC subscription), then start a project and **import** (⌘i) the first image in your rendered frames folder (i.e. `0000.pdf`) into your project, making sure to select "Image Sequence" from the cryptic "Options" option in the import dialog. Once you've imported this "image sequence," you can drag it to to the timeline area and it will create a sequence for you with all the correct settings. Then you can create a composition from that sequence, and, when you've rendered new frames, you can purge the After Effects memory (via Edit > Purge > All Memory) and — voila! — you’ve got a previewable/steppable animation.

**Why render PDF and not PNG?** I've noticed some artifacting in variable fonts when cutting png image directly from DrawBot with certain fonts, but the same artifacts are not present in PDFs, and remain invisible even when After Effects renders PDFs down to mp4s via the Adobe Media Encoder pipeline.

**Caveat!** It's easy to get the frame rate for the imported image sequence incorrect, since the default frame rate for all imported sequences is set in Premiere's `Preferences -> Media -> Indeterminate Media Timebase` and After Effects’ `Preferences -> Import -> Sequence Footage -> frames per second`. Since I'm often combining images and video shot at 23.976, I keep my "indeterminate media timebase" at 23.976, though if you're doing video-free animations, you can use a saner fps, like 24 or 30, or something slower for a funkier feel.
