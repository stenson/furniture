from furniture.animation import Animation
from furniture.vfont import scaledFontVariations
from drawBot import *

def draw(frame):
    bp = BezierPath()
    fs = FormattedString(font="Tweak-Display", fontSize=1000)
    scaledFontVariations(fs, DIST=frame.doneness)
    fs.append("abc")
    bp.text(fs, (100, 100))
    bp.drawToPen(frame.bps["default"].bp)

animation = Animation(draw, 60, dimensions=(1000, 1000), fmt="ufo")
animation.storyboard(0)