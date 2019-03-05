
def scale_to_axis(axis, value, insetMin=1, insetMax=1):
    """
    Scales a value between 0 and 1 to the range of an axis,
    where an 'axis' is just a dict with values for the keys
    minValue and maxValue (i.e. what’s returned from drawBot’s
    `listFontVariations` call, for a given axis)

    `insetMin` and `insetMax` let you specify an offset from the true
    min/max, in order to avoid a bug in the Apple font variation code;
    this defaults to 1 which is the most standard
    """
    minv = axis.get("minValue", 0)
    maxv = axis.get("maxValue", 1000)
    scaled = (value * (maxv - minv)) + minv
    return max(minv + insetMin, min(maxv - insetMax, scaled))


def scaledFontVariations(fs, **kwargs):
    for axis, value in kwargs.items():
        axis_dict = fs.listFontVariations().get(axis)
        scaled = scale_to_axis(axis_dict, value)
        fs.fontVariations(**{axis:scaled})
    return scaled