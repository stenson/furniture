import sys
import time
import os
import json
import argparse
import datetime
import drawBot as db
from furniture.geometry import Rect, Edge


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def parseargs():
    parser = argparse.ArgumentParser(
        prog="furniture.animation.Animation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-st", "--start", type=int, default=-1)
    parser.add_argument("-en", "--end", type=int, default=None)
    #parser.add_argument("-ds", "--save", type=str2bool, default=False)
    parser.add_argument("-fo", "--folder", type=str, default="frames")
    #parser.add_argument("-co", "--compile", type=str2bool, default=False)
    #parser.add_argument("-au", "--audio", type=str, default=None)

    return parser.parse_args()


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


class AnimationFrame():
    def __init__(self, animation, i):
        self.animation = animation
        self.i = i
        self.doneness = self.i / self.animation.length
        self.time = self.i / self.animation.fps
        self.data = None

    def __repr__(self):
        return "<furniture.AnimationFrame {:04d}, {:04.2f}s, {:06.4f}%>".format(self.i, self.time, self.doneness)

    def draw(self, saving=False, saveTo=None):
        if saving:
            db.newDrawing()
            self.saving = True
        else:
            self.saving = False

        db.newPage(*self.animation.dimensions)
        self.page = Rect.page()
        self.animation.fn(self)
        if self.animation.burn:
            box = self.page.take(64, Edge.MinY).take(
                120, Edge.MaxX).offset(-24, 24)
            db.fontSize(24)
            db.lineHeight(18)
            db.font("CovikSansMono-Black")
            db.fallbackFont("Menlo-Bold")
            db.fill(0, 0.8)
            db.rect(*box.inset(-14, -14).offset(0, 2))
            db.fill(1)
            db.textBox("{:07.2f}\n{:04d}\n{:%H:%M:%S}".format(
                self.time, self.i, datetime.datetime.now()), box, align="center")

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


class Animation():
    def __init__(self, fn, length=10, fps=30, dimensions=(1920, 1080), burn=False, audio=None, folder=None, file=None):
        self.fn = fn
        self.length = length
        self.fps = fps
        self.dimensions = dimensions
        self.burn = burn
        #self.args = parseargs()
        if not file:
            raise Exception(
                "Please pass file=__file__ in constructor arguments")
        else:
            self.file = file
            self.root = os.path.dirname(os.path.realpath(file))
            self.folder = self.root + "/" + folder
            self.audio = self.root + "/" + audio

    def _storyboard(self, data, *frames):
        for i in frames:
            frame = AnimationFrame(self, i)
            print("(storyboard)", frame)
            frame.data = data
            frame.draw(saving=False, saveTo=None)

    def render(self, start=-1, end=None, data=None):
        if not data:
            try:
                with open(self.root + "/text.json", "r") as f:
                    data = json.loads(f.read())
            except FileExistsError:
                print("no text.json found")
                data = {}
        if start == -1:
            print("--start must be set")
        else:
            if end == None:
                end = self.length
            for i in range(start, end):
                frame = AnimationFrame(self, i)
                frame.data = data
                print("(render)", frame)
                frame.draw(saving=True, saveTo=self.folder)

    def storyboard(self, data, *frames):
        # if self.args.start == -1:
        self._storyboard(data, *frames)
        # else:
        #    self.render(**vars(self.args))
