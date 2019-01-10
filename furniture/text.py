import CoreText
import AppKit
from fontTools.ttLib import TTFont
from drawBot.context.baseContext import BaseContext


class WordContext(BaseContext):
    def visibleAndClippedText(self, txt, box, align="left", hyphenation=True):
        path, origin = self._getPathForFrameSetter(box)
        attrString = self.attributedString(txt, align=align)
        if hyphenation:
            hyphenIndexes = [i for i, c in enumerate(
                attrString.string()) if c == "-"]
            attrString = self.hyphenateAttributedString(attrString, path)
        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
        visibleRange = CoreText.CTFrameGetVisibleStringRange(box)
        clip = visibleRange.length
        if hyphenation:
            subString = attrString.string()[:clip]
            for i in hyphenIndexes:
                if i < clip:
                    clip += 1
                else:
                    break
            clip -= subString.count("-")
        return txt[:clip], txt[clip:]


def split_visible(txt, box, align="left", hyphenation=True):  # does align do anything?
    return WordContext().visibleAndClippedText(txt, box, align, hyphenation)


def glyph_identifiers(txt, font, fontSize):
    context = BaseContext()
    context.font(font, fontSize)
    path, (x, y) = context._getPathForFrameSetter((0, 0, 1200, 1200))
    attributedString = context.attributedString(txt, "left")
    setter = CoreText.CTFramesetterCreateWithAttributedString(attributedString)
    frame = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
    ctLines = CoreText.CTFrameGetLines(frame)
    origins = CoreText.CTFrameGetLineOrigins(frame, (0, len(ctLines)), None)

    glyphIDs = []
    for i, (originX, originY) in enumerate(origins):
        ctLine = ctLines[i]
        ctRuns = CoreText.CTLineGetGlyphRuns(ctLine)
        for ctRun in ctRuns:
            glyphCount = CoreText.CTRunGetGlyphCount(ctRun)
            for i in range(glyphCount):
                glyph = CoreText.CTRunGetGlyphs(ctRun, (i, 1), None)[0]
                if glyph:
                    glyphIDs.append(glyph)
    return glyphIDs
