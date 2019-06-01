import freetype
#print(freetype.__file__)

from collections import OrderedDict
from freetype.raw import *
from fontParts.fontshell import RGlyph
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.recordingPen import RecordingPen, replayRecording
from fontTools.ttLib import TTFont
from furniture.geometry import Rect
import uharfbuzz as hb


class HarfbuzzFrame():
    def __init__(self, info, position, frame):
        self.gid = info.codepoint
        self.info = info
        self.position = position
        self.frame = frame

    def __repr__(self):
        return f"HarfbuzzFrame: gid{self.gid}@{self.frame}"


class Harfbuzz():
    def __init__(self, font_path, upem=72):
        with open(font_path, 'rb') as fontfile:
            fontdata = fontfile.read()
        self.fontPath = font_path
        self.face = hb.Face(fontdata)
        self.font = hb.Font(self.face)
        self.upem = self.face.upem
        self.upem = upem
        self.font.scale = (self.upem, self.upem)
        hb.ot_font_set_funcs(self.font)

    def setText(self, axes=dict(), features=dict(kern=True, liga=True), tracking=0, txt=""):
        buf = hb.Buffer()
        buf.add_str(txt)
        buf.guess_segment_properties()
        self.font.set_variations(axes)
        hb.shape(self.font, buf, features)
        infos = buf.glyph_infos
        positions = buf.glyph_positions
        frames = []
        x = 0
        for info, pos in zip(infos, positions):
            gid = info.codepoint
            cluster = info.cluster
            x_advance = pos.x_advance
            x_offset = pos.x_offset
            y_offset = pos.y_offset
            frames.append(HarfbuzzFrame(info, pos, Rect((x, y_offset, x_advance, 100)))) # 100?
            x += x_advance + tracking
        return frames

def ft_move_to(a, pen):
    if len(pen.value) > 0:
        pen.closePath()
    pen.moveTo((a.x, a.y))

def ft_line_to(a, pen):
    pen.lineTo((a.x, a.y))

def ft_conic_to(a, b, pen):
    pen.qCurveTo((a.x, a.y), (b.x, b.y))

def ft_cubic_to(a, b, c, pen):
    pen.curveTo((a.x, a.y), (b.x, b.y), (c.x, c.y))

class FreetypeReader():
    def __init__(self, font_path, scale=1000): # should pass in the ttfont not make it
        self.fontPath = font_path
        self.font = freetype.Face(font_path)
        self.font.set_char_size(scale)
        self.scale = scale
        self.ttfont = TTFont(font_path)
        try:
            self.axesOrder = [a.axisTag for a in self.ttfont['fvar'].axes]
        except:
            self.axesOrder = []
    
    def setVariations(self, axes=dict()):
        if len(self.axesOrder) > 0:
            coords = []
            for name in self.axesOrder:
                coord = FT_Fixed(axes[name] << 16)
                coords.append(coord)
            ft_coords = (FT_Fixed * len(coords))(*coords)
            flags = freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP
            freetype.FT_Set_Var_Design_Coordinates(self.font._FT_Face, len(ft_coords), ft_coords)
    
    def setGlyph(self, glyph_id):
        self.glyph_id = glyph_id
        flags = freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP
        if isinstance(glyph_id, int):
            self.font.load_glyph(glyph_id, flags)
        else:
            self.font.load_char(glyph_id, flags)

    def drawOutlineToPen(self, pen, raiseCubics=True):
        outline = self.font.glyph.outline
        rp = RecordingPen()
        self.font.glyph.outline.decompose(rp, move_to=ft_move_to, line_to=ft_line_to, conic_to=ft_conic_to, cubic_to=ft_cubic_to)
        rp.closePath()
        replayRecording(rp.value, pen)
        return
    
    def drawTTOutlineToPen(self, pen):
        glyph_name = self.ttfont.getGlyphName(self.glyph_id)
        g = self.ttfont.getGlyphSet()[glyph_name]
        g.draw(pen)
        print("Glyph name", g)

class StyledString():
    def __init__(self,
            text="",
            fontFile=None,
            fontSize=12,
            tracking=0,
            variations=dict(),
            features=dict()):
        self.text = text
        self.fontFile = fontFile
        self.harfbuzz = Harfbuzz(fontFile, upem=1000)
        self.ttfont = TTFont(self.fontFile)
        self.fontSize = fontSize
        self.tracking = tracking
        self.features = {**dict(kern=True, liga=True), **features}
        
        self.axes = OrderedDict()
        self.variations = dict()
        try:
            for axis in self.ttfont['fvar'].axes:
                self.axes[axis.axisTag] = axis
                self.variations[axis.axisTag] = axis.defaultValue
            for k, v in self.normalizeVariations(variations).items():
                self.variations[k] = v
        except:
            pass
    
    def normalizeVariations(self, variations):
        for k, v in variations.items():
            try:
                axis = self.axes[k]
            except KeyError:
                raise Exception("Invalid axis", self.fontFile, k)
            if v == "min":
                variations[k] = int(axis.minValue)
            elif v == "max":
                variations[k] = int(axis.maxValue)
            elif v == "default":
                variations[k] = int(axis.defaultValue)
            elif isinstance(v, float) and v <= 1.0:
                variations[k] = int((axis.maxValue-axis.minValue)*v + axis.minValue)
            else:
                if v < axis.minValue or v > axis.maxValue:
                    raise Exception("Invalid font variation",
                        self.fontFile,
                        self.axes[k].axisTag,
                        v)
        return variations
    
    def getGlyphFrames(self):
        return self.harfbuzz.setText(axes=self.variations, features=self.features, txt=self.text, tracking=self.tracking*(1000/self.fontSize))
    
    def width(self): # size?
        return self.getGlyphFrames()[-1].frame.point("SE").x * (self.fontSize/1000)
    
    def fit(self, width, trackingLimit=0, variationLimits=dict()):
        self.normalizeVariations(variationLimits)
        _vars = self.variations
        current_width = self.width()
        self.tries = 0
        if current_width > width: # need to shrink
            while self.tries < 1000 and current_width > width:
                if self.tracking > trackingLimit:
                    self.tracking -= 0.25
                else:
                    for k, v in variationLimits.items():
                        if self.variations[k] > variationLimits[k]:
                            self.variations[k] -= 1
                            break
                self.tries += 1
                current_width = self.width()
        elif current_width < width: # need to expand
            pass
        else:
            return
    
    def formattedString(self):
        feas = dict(self.features)
        del feas["kern"]
        return FormattedString(self.text, font=self.fontFile, fontSize=self.fontSize, lineHeight=self.fontSize+2, tracking=self.tracking, fontVariations=self.variations, openTypeFeatures=feas)
    
    def drawToPen(self, out_pen):
        fr = FreetypeReader(self.fontFile, scale=1000)
        fr.setVariations(self.variations)
        # self.harfbuzz.setFeatures ???
        for frame in self.getGlyphFrames():
            fr.setGlyph(frame.gid)
            fill(0, 0.5, 1, 0.5)
            s = self.fontSize/1000
            if False:
                tp_scale = TransformPen(out_pen, (s, 0, 0, s, 0, 0))
                tp_transform = TransformPen(tp_scale, (1, 0, 0, 1, frame.frame.x, frame.frame.y))
                fr.drawOutlineToPen(tp_transform, raiseCubics=True)
            else:
                fr.drawOutlineToPen(out_pen, raiseCubics=True)
                bp = BezierPath()
                fr.drawTTOutlineToPen(bp)
                drawPath(bp)
                #drawBezierSkeleton(bp)

if __name__ == "__main__":
    import os
    import time
    from defcon import Glyph
    from grafutils.beziers.utils import drawBezier, drawBezierSkeleton
    
    fp = os.path.expanduser("~/Library/Fonts")
    faces = [
        [f"{fp}/ObviouslyVariable.ttf", dict(wdth=250, wght=200)],
        [f"{fp}/Cheee_Variable.ttf", dict(temp=250, grvt=200, yest=250)],
        [f"{fp}/VulfMonoLightItalicVariable.ttf", dict(wdth=500)],
    ]
    
    def test_timing():
        txt = "Hello"
        font_size = 72
        for font_path, axes in faces:
            print("FONT", font_path)
            print("VARIATIONS", axes)
            t1 = time.process_time()
            hbs = Harfbuzz(font_path, upem=font_size)
            frames = hbs.setText(axes=axes, txt=txt)
            w1 = frames[-1].frame.point("SE").x
            l1 = time.process_time() - t1
            t2 = time.process_time()
            fs = FormattedString(txt, font=font_path, fontSize=font_size, fontVariations=axes)
            w2 = fs.size()[0]
            l2 = time.process_time() - t2
            print("DIFF: w={:.2f}, t={:.2f}".format(w1 - w2, l2 / l1))
            print("----------")
    
    def test_styled_fitting():
        fill(0)
        rect(*Rect.page())
        
        ss = StyledString("COMPRESSION".upper(),
            fontFile=f"{fp}/ObviouslyVariable.ttf",
            fontSize=55,
            variations=dict(wdth=1.0, wght=0.2),
            features=dict(ss01=True),
            tracking=30)
        count = 22
        translate(0, 6)
        for x in range(count):
            w = 100+(pow(1-x/count, 2))*900
            if False:
                print("BEFORE wdth", ss.variations.get("wdth"),
                    "width", ss.width(), ss.tracking)
            ss.fit(w, variationLimits=dict(wdth="min"))
            if False:
                print("AFTER wdth", ss.variations.get("wdth"),
                    "width", ss.width(), ss.tracking, ss.tries)
            g = Glyph()
            ss.drawToPen(g.getPen())
            fill(random(), 0.5, 1, 1)
            drawBezier(g)
            translate(0, ss.fontSize-10)
            if False: # also draw a coretext string?
                fill(random(), 0.5, 1, 0.15)
                bp = BezierPath()
                bp.text(ss.formattedString(), (0, 0))
                bp.translate(4, -74)
                drawPath(bp)
    
    def test_styled_string(t, f):
        size(2000, 900)
        #translate(200, 200)
        #with savedState():
        #    image("~/Desktop/hb.png", (0, 0))
        translate(35, 124)
        ss = StyledString(t.upper(),
            fontFile=f,
            fontSize=1000,
            tracking=0)
        g = Glyph()
        ss.drawToPen(g.getPen())
        fill(0, 0.5, 1, 0.5)
        #translate(34, 125)
        #drawBezier(g)
        drawBezierSkeleton(g, labels=True)
        if False: # also draw a coretext string?
            fill(None)
            stroke(1, 0, 0.5, 0.25)
            strokeWidth(2)
            bp = BezierPath()
            bp.text(ss.formattedString(), (0, 0))
            bp.removeOverlap()
            bp.translate(0, 10)
            #bp.translate(4, -74)
            #drawBezierSkeleton(bp, labels=True)
            drawPath(bp)
    
    #test_styled_fitting()
    
    t = "ٱلْـحَـمْـدُ للهِ‎"
    t = "نستعلیق"
    #t = "ن"
    #t = "﮲"
    f = f"{fp}/AwamiNastaliq-Regular.ttf"
    f = f"{fp}/29LTArapix.otf"
    f = "/Users/robertstenson/Library/Application Support/.FCache/.R-5-17198-18-jaivlwiaijqk-jtiks.otf"
    f = "/Users/robertstenson/Type/fonts/fonts/29LTAzal-Display.ttf"
    
    t = "I"
    f = "/Users/robertstenson/Library/Fonts/Beastly-72Point.otf"
    test_styled_string(t, f)