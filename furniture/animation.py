import sys
import time
import os
import json
import tempfile
import datetime
import drawBot as db
from subprocess import Popen, PIPE
from furniture.geometry import Rect, Edge


class AnimationFrame():
    def __init__(self, animation, i):
        self.animation = animation
        self.i = i
        self.doneness = self.i / self.animation.length
        self.time = self.i / self.animation.fps
        self.data = None

    def __repr__(self):
        return "<furniture.AnimationFrame {:04d}, {:04.2f}s, {:06.4f}%>".format(self.i, self.time, self.doneness)

    def draw(self, saving=False, saveTo=None, fmt="png"):
        if saving:
            db.newDrawing()
            self.saving = True
        else:
            self.saving = False

        db.newPage(*self.animation.dimensions)
        self.page = Rect.page()
        with db.savedState():
            self.animation.fn(self)
        if self.animation.burn:
            box = self.page.take(64, Edge.MinY).take(
                120, Edge.MaxX).offset(-24, 24)
            db.fontSize(20)
            db.lineHeight(20)
            db.font("Menlo-Bold")
            db.fill(0, 0.8)
            db.rect(*box.inset(-14, -14).offset(0, 2))
            db.fill(1)
            db.textBox("{:07.2f}\n{:04d}\n{:%H:%M:%S}".format(
                self.time, self.i, datetime.datetime.now()), box, align="center")

        if saving:
            db.saveImage(f"{saveTo}/{self.i}.{fmt}")
            db.endDrawing()

        self.saving = False


AFTER_EFFECTS_PURGE_JSX = """
//@target aftereffects
(function () {
    var comp = app.project.activeItem;
    comp.time = 0;
    $.sleep(20);
    app.purge(PurgeTarget.IMAGE_CACHES);
    alert("purged");
})();
"""


def purge_after_effects_memory():
    with tempfile.NamedTemporaryFile(mode="w") as temp:
        temp.write(AFTER_EFFECTS_PURGE_JSX)
        temp.flush()
        script = """
            tell application id "com.adobe.aftereffects" to activate DoScriptFile "{}"
        """.format(temp.name)
        p = Popen(["osascript", "-e", script])
        stdout, stderr = p.communicate()
        return p.returncode, stdout, stderr


class Animation():
    def __init__(self, fn, length=10, fps=30, dimensions=(1920, 1080), burn=False, audio=None, folder="frames", fmt="png", data=None):
        self.fn = fn
        self.length = length
        self.fps = fps
        self.dimensions = dimensions
        self.burn = burn
        self.fmt = fmt
        self.folder = folder
        self.audio = audio
        self.data = data

    def storyboard(self, data={}, frames=[0]):
        try:
            for i in frames:
                frame = AnimationFrame(self, i)
                print("(storyboard)", frame)
                frame.data = data
                frame.draw(saving=False, saveTo=None)
        except TypeError:
            i = frames
            frame = AnimationFrame(self, i)
            print("(storyboard)", frame)
            frame.data = data
            frame.draw(saving=False, saveTo=None)

    def render(self, start=0, end=None, data=None, purgeAfterEffects=False):
        if not data and self.data:
            try:
                with open(self.data, "r") as f:
                    data = json.loads(f.read())
            except FileNotFoundError:
                data = {}
        if end == None:
            end = self.length
        for i in range(start, end):
            frame = AnimationFrame(self, i)
            frame.data = data
            print("(render)", frame)
            frame.draw(saving=True, saveTo=self.folder, fmt=self.fmt)
        if purgeAfterEffects:
            print("furniture.animation >>> purging current After Effects memory...")
            purge_after_effects_memory()


if __name__ == "__main__":
    def draw(frame):
        pass
    animation = Animation(draw, length=10, fps=30, dimensions=(1000, 1000))
    animation.storyboard(frames=0)
    purge_after_effects_memory()
