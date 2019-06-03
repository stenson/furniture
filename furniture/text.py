import freetype
import freetype.raw

import math
from collections import OrderedDict
from freetype.raw import *
from booleanOperations.booleanGlyph import BooleanGlyph
from fontParts.fontshell import RGlyph
from fontTools.misc.transform import Transform
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.recordingPen import RecordingPen, replayRecording
from fontTools.misc.bezierTools import calcCubicArcLength, splitCubicAtT
from fontTools.ttLib import TTFont
from furniture.geometry import Rect
import uharfbuzz as hb
import unicodedata


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

    def setText(self, axes=dict(), features=dict(kern=True, liga=True), txt=""):
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
            frames.append(HarfbuzzFrame(info, pos, Rect((x+x_offset, y_offset, x_advance, 1000)))) # 100?
            x += x_advance
        return frames


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
            freetype.FT_Set_Var_Design_Coordinates(self.font._FT_Face, len(ft_coords), ft_coords)
    
    def setGlyph(self, glyph_id):
        self.glyph_id = glyph_id
        flags = freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP | freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING
        if isinstance(glyph_id, int):
            self.font.load_glyph(glyph_id, flags)
        else:
            self.font.load_char(glyph_id, flags)

    def drawOutlineToPen(self, pen, raiseCubics=True):
        outline = self.font.glyph.outline
        rp = RecordingPen()
        self.font.glyph.outline.decompose(rp, move_to=FreetypeReader.moveTo, line_to=FreetypeReader.lineTo, conic_to=FreetypeReader.conicTo, cubic_to=FreetypeReader.cubicTo)
        if len(rp.value) > 0:
            rp.closePath()
        replayRecording(rp.value, pen)
        return
    
    def drawTTOutlineToPen(self, pen):
        glyph_name = self.ttfont.getGlyphName(self.glyph_id)
        g = self.ttfont.getGlyphSet()[glyph_name]
        try:
            g.draw(pen)
        except TypeError:
            print("could not draw TT outline")
            
    
    def moveTo(a, pen):
        if len(pen.value) > 0:
            pen.closePath()
        pen.moveTo((a.x, a.y))

    def lineTo(a, pen):
        pen.lineTo((a.x, a.y))

    def conicTo(a, b, pen):
        if False:
            pen.qCurveTo((a.x, a.y), (b.x, b.y))
        else:
            c0 = pen.value[-1][-1][-1]
            c1 = (c0[0] + (2/3)*(a.x - c0[0]), c0[1] + (2/3)*(a.y - c0[1]))
            c2 = (b.x + (2/3)*(a.x - b.x), b.y + (2/3)*(a.y - b.y))
            c3 = (b.x, b.y)
            pen.curveTo(c1, c2, c3)
            #pen.lineTo(c3)

    def cubicTo(a, b, c, pen):
        pen.curveTo((a.x, a.y), (b.x, b.y), (c.x, c.y))


class CurveCutter():    
    def __init__(self, g, inc=0.0015):
        self.pen = RecordingPen()
        g.draw(self.pen)
        self.inc = inc
        self.length = self.calcCurveLength()
    
    def calcCurveLength(self):
        length = 0
        for i, (t, pts) in enumerate(self.pen.value):
            if t == "curveTo":
                p1, p2, p3 = pts
                p0 = self.pen.value[i-1][-1][-1]
                length += calcCubicArcLength(p0, p1, p2, p3)
            elif t == "lineTo":
                pass # todo
        return length

    def subsegment(self, start=None, end=None):
        inc = self.inc
        length = self.length
        ended = False
        _length = 0
        out = []
        for i, (t, pts) in enumerate(self.pen.value):
            if t == "curveTo":
                p1, p2, p3 = pts
                p0 = self.pen.value[i-1][-1][-1]
                length_arc = calcCubicArcLength(p0, p1, p2, p3)
                if _length + length_arc < end:
                    _length += length_arc
                else:
                    t = inc
                    tries = 0
                    while not ended:
                        a, b = splitCubicAtT(p0, p1, p2, p3, t)
                        length_a = calcCubicArcLength(*a)
                        if _length + length_a > end:
                            ended = True
                            out.append(("curveTo", a[1:]))
                        else:
                            t += inc
                            tries += 1
            if t == "lineTo":
                pass # TODO
            if not ended:
                out.append((t, pts))
    
        if out[-1][0] != "endPath":
            out.append(("endPath",[]))
        return out

    def subsegmentPoint(self, start=0, end=1):
        inc = self.inc
        subsegment = self.subsegment(start=start, end=end)
        try:
            t, (a, b, c) = subsegment[-2]
            tangent = math.degrees(math.atan2(c[1] - b[1], c[0] - b[0]) + math.pi*.5)
            return c, tangent
        except ValueError:
            return None, None

class StyledString():
    def __init__(self,
            text="",
            fontFile=None,
            fontSize=12,
            tracking=0,
            variations=dict(),
            features=dict()):
        self.text = text
        self.fontFile = os.path.expanduser(fontFile)
        self.harfbuzz = Harfbuzz(self.fontFile, upem=1000)
        self.ttfont = TTFont(self.fontFile)
        self.fontSize = fontSize
        self.tracking = tracking
        self.features = {**dict(kern=True, liga=True), **features}
        self.path = None
        
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
    
    def vowelMark(self, u):
        return "KASRA" in u or "FATHA" in u or "DAMMA" in u or "TATWEEL" in u or "SUKUN" in u
    
    def trackFrames(self, frames):
        t = self.tracking*1/self.scale()
        t = self.tracking
        x_off = 0
        has_kashida = False
        try:
            self.ttfont.getGlyphID("uni0640")
            has_kashida = True
        except KeyError:
            has_kashida = False
        if not has_kashida:
            for idx, f in enumerate(frames):
                f.frame = f.frame.offset(x_off, 0)
                x_off += t
        else:
            glyph_names = []
            for frame in frames:
                glyph_name = self.ttfont.getGlyphName(frame.gid)
                code = glyph_name.replace("uni", "")
                try:
                    glyph_names.append(unicodedata.name(chr(int(code, 16))))
                except:
                    glyph_names.append(code)
            for idx, frame in enumerate(frames):
                frame.frame = frame.frame.offset(x_off, 0)
                try:
                    u = glyph_names[idx]
                    if self.vowelMark(u):
                        continue
                    u_1 = glyph_names[idx+1]
                    if self.vowelMark(u_1):
                        u_1 = glyph_names[idx+2]
                    if "MEDIAL" in u_1 or "INITIAL" in u_1:
                        f = 1.6
                        if "MEEM" in u_1 or "LAM" in u_1:
                            f = 2.7
                        x_off += t*f
                except IndexError:
                    pass
        return frames
    
    def adjustFramesForPath(self, frames):
        self.tangents = []
        self.limit = len(frames)
        if self.path:
            for idx, f in enumerate(frames):
                ow = f.frame.x+f.frame.w/2
                if ow > self.cutter.length:
                    self.limit = min(idx, self.limit)
                else:
                    p, t = self.cutter.subsegmentPoint(end=ow)
                    f.frame.x = p[0]
                    f.frame.y = f.frame.y + p[1]
                    self.tangents.append(t)
        return frames[0:self.limit]
    
    def getGlyphFrames(self):
        frames = self.harfbuzz.setText(axes=self.variations, features=self.features, txt=self.text)
        for f in frames:
            f.frame = f.frame.scale(self.scale())
        return self.adjustFramesForPath(self.trackFrames(frames))
    
    def width(self): # size?
        return self.getGlyphFrames()[-1].frame.point("SE").x * self.scale()
    
    def scale(self):
        return self.fontSize / 1000
    
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
    
    def addPath(self, path):
        self.path = path
        self.cutter = CurveCutter(path)
    
    def formattedString(self):
        feas = dict(self.features)
        del feas["kern"]
        return FormattedString(self.text, font=self.fontFile, fontSize=self.fontSize, lineHeight=self.fontSize+2, tracking=self.tracking, fontVariations=self.variations, openTypeFeatures=feas)
    
    def drawToPen(self, out_pen, useTTFont=False):
        fr = FreetypeReader(self.fontFile, scale=1000)
        fr.setVariations(self.variations)
        # self.harfbuzz.setFeatures ???
        self._frames = self.getGlyphFrames()
        for idx, frame in enumerate(self._frames):
            fr.setGlyph(frame.gid)
            s = self.scale()
            t = Transform()
            t = t.scale(s)
            t = t.translate(frame.frame.x/self.scale(), frame.frame.y/self.scale())
            if self.path:
                tangent = self.tangents[idx]
                t = t.rotate(math.radians(tangent-90))
                t = t.translate(-frame.frame.w*0.5/self.scale())
            tp = TransformPen(out_pen, (t[0], t[1], t[2], t[3], t[4], t[5]))
            
            #tp_rotate = TransformPen(out_pen, (0, 1, -1, 0, 0, 0))
            #tp_scale = TransformPen(tp_rotate, (s, 0, 0, s, 0, 0))
            #tp_transform = TransformPen(tp_scale, (1, 0, 0, 1, frame.frame.x/self.scale(), frame.frame.y/self.scale()))
            if useTTFont:
                fr.drawTTOutlineToPen(tp_transform)
            else:
                fr.drawOutlineToPen(tp, raiseCubics=True)
    
    def asGlyph(self, removeOverlap=True):
        bg = BooleanGlyph()
        self.drawToPen(bg.getPen())
        if removeOverlap:
            return bg.removeOverlap()
        else:
            return bg
    
    def drawBotDraw(self, removeOverlap=True):
        try:
            import drawBot as db
            g = self.asGlyph(removeOverlap=removeOverlap)
            bp = db.BezierPath()
            g.draw(bp)
            drawPath(bp)
        except ImportError:
            print("Could not import DrawBot")
    

if __name__ == "__main__":
    import os
    import time
    from defcon import Glyph
    
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
            fontSize=50,
            variations=dict(wdth=1.0, wght=0.9),
            features=dict(ss01=False),
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
            fill(random(), 0.5, 1, 1)
            fill(1)
            drawBezier(ss.asGlyph(removeOverlap=False))
            translate(30, ss.fontSize-5)
            if False: # also draw a coretext string?
                fill(random(), 0.5, 1, 0.15)
                bp = BezierPath()
                bp.text(ss.formattedString(), (0, 0))
                bp.translate(4, -74)
                drawPath(bp)
    
    def test_styled_string(t, f):
        newPage(1500, 400)
        fill(0.95)
        rect(*Rect.page())
        #translate(200, 200)
        if False:
            with savedState():
                scale(4)
                translate(-10, -7)
                image("~/Desktop/palt.png", (0, -300))
        translate(50, 150)
        ss = StyledString(t,
            fontFile=f,
            fontSize=200,
            features=dict(palt=True),
            tracking=0)
        
        stroke(0, 1, 0.5, 0.5)
        strokeWidth(10)
        fill(1)
        ss.drawBotDraw()
        #ss.drawBezier()
        with savedState():
            for f in ss._frames:
                fill(None)
                strokeWidth(1)
                stroke(1, 0.5, 0, 0.5)
                rect(*f.frame.inset(0, 0))
        if False:
            bp = BezierPath()
            ss.drawToPen(bp, useTTFont=True)
            fill(None)
            stroke(0, 0.5, 1, 0.5)
            strokeWidth(4)
            #bp.removeOverlap()
            drawPath(bp)
        if True: # also draw a coretext string?
            fill(None)
            stroke(1, 0, 0.5)
            strokeWidth(1)
            bp = BezierPath()
            bp.text(ss.formattedString(), (0, 0))
            #bp.removeOverlap()
            drawPath(bp)
    
    if False:
        test_styled_fitting()
    
    if True:
        t = "ٱلْـحَـمْـدُ للهِ‎"
        #t = "الحمراء"
        #t = "رَقَمِيّ"
        #t = "ن"
        f = "~/Type/fonts/fonts/BrandoArabic-Black.otf"
        #f = "~/Type/fonts/fonts/29LTAzal-Display.ttf"
        #test_styled_string(t, f)
    
        t = "Beastly"
        f = f"{fp}/Beastly-72Point.otf"
        test_styled_string(t, f)
    
        #t = "フィルター"
        #f = "~/Library/Application Support/Adobe/CoreSync/plugins/livetype/.r/.35716.otf"
        #test_styled_string(t, f)
    
    if True:
        newPage(1000, 1000)
        g = RGlyph()
        gp = g.getPen()
        gp.moveTo((100, 100))
        gp.curveTo((540, 250), (430, 750), (900, 900))
        gp.endPath()
        bp = BezierPath()
        g.draw(bp)
        fill(None)
        stroke(1, 0, 0.5, 0.1)
        strokeWidth(10)
        drawPath(bp)
        ss = StyledString("hello world, what’s happening?",
            fontFile="~/Library/Fonts/NikolaiV0.2-BoldCondensed.otf",
            fontSize=100,
            features=dict(palt=True),
            variations=dict(wdth=0.43, wght=0.1),
            tracking=14)
        ss.addPath(g)
        fill(0, 0.5, 1)
        stroke(None)
        ss.drawBotDraw()