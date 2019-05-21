from furniture.animation import Animation
from furniture.vfont import scaledFontVariations
#from drawBot import *

def draw(frame):
    bp = BezierPath()
    for layer, fontName, fillColor in [["default", "HobeauxRococeaux-Regular", (1, 0, 0.5)], ["bg", "HobeauxRococeaux-Background", (0, 0.5, 1)]]:
        if layer in frame.layers:
            fs = FormattedString(font=fontName, fontSize=1000)
            if frame.doneness > 0.66:
                fs.append("C")
            elif frame.doneness > 0.33:
                fs.append("B")
            else:
                fs.append("A")
            bp.text(fs, (100, -100))
            frame.bps[layer].fill = fillColor
            bp.drawToPen(frame.bps[layer].bp)

animation = Animation(draw, 60, dimensions=(1000, 1000), fmt="ufo", layers=["bg", "default"])
animation.storyboard(0, 59)