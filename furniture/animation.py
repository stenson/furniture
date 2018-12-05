import sys
import drawBot as db
from furniture.geometry import Rect, Edge
import time
import os
import errno

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


class AnimationFrame():
    def __init__(self, draw_fn, i, length, curve=None, dimensions=(1024, 1024), fps=30):
        self.draw_fn = draw_fn
        self.i = i
        self.curve = curve
        self.dimensions = dimensions
        self.fps = fps
        self.length = length
        self.doneness = self.i / self.length
        self.time = self.i / self.fps
        self.x = round(self.length * curve((i/self.length)))
    
    def draw(self, saving=False, saveTo=None):
        if saving:
            db.newDrawing()
            self.saving = True
        else:
            self.saving = False

        db.newPage(*self.dimensions)
        self.draw_fn(self.i, Rect.page(), self)
    
        if saving:
            db.saveImage(f"{saveTo}/{self.i}.png")
            db.endDrawing()
        
        self.saving = False
    
    # legacy
    def get(self, attr):
        if hasattr(self, attr):
            return getattr(self, attr)
        else:
            return None


def draw_frame(fn, total_frames, i=0, curve=None, dimensions=(1024, 1024), doSave=False, saveTo=None, fps=30):
    if i > total_frames:
        return

    if doSave:
        print(f"drawing & saving: {i}")
    else:
        print(f"drawing: {i}")

    if doSave:
        db.newDrawing()

    db.newPage(*dimensions)
    
    env = dict(total=total_frames,
               saving=doSave,
               doneness=i/total_frames,
               time=i/fps,
               x=round(total_frames * curve((i/total_frames))))
    fn(i, Rect.page(), env)

    if doSave:
        db.saveImage(f"{saveTo}/{i}.png")
        db.endDrawing()


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def draw_frames(fn,
                total_frames,
                start=0,
                end=20,
                fps=30,
                curve=lambda y: y,
                storyboard=[],
                dimensions=(1024, 1024),
                doSave=False,
                saveTo=None):

    import argparse

    parser = argparse.ArgumentParser(
        prog="draw_frames",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-st", "--start", type=int, default=-1)
    parser.add_argument("-en", "--end", type=int, default=total_frames)
    parser.add_argument("-ds", "--save", type=str2bool, default=False)
    parser.add_argument("-fo", "--folder", type=str, default="frames")
    parser.add_argument("-co", "--compile", type=str2bool, default=False)
    parser.add_argument("-au", "--audio", type=str, default=None)

    args = parser.parse_args()

    if args.start >= 0:
        storyboard = []

    frames = range(args.start, args.end)

    if len(storyboard) > 0:
        print("STORYBOARDING")
        frames = storyboard

    for i in frames:
        frame = AnimationFrame(fn, i, total_frames, curve=curve, dimensions=dimensions, fps=fps)
        frame.draw(saving=args.save, saveTo=args.folder)
    
    if args.save:
        print("---\nDONE RENDER: {:05d}-{:05d}\n---\n".format(args.start, args.end))

    #if args.compile:
    #    time.sleep(1)
    #    t = str(int(time.time()))
    #    mp4name = mp4(args.folder, t=t, fps=fps, audio=args.audio)
    #    db.misc.executeExternalProcess(["open", mp4name])