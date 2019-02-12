
def scale_to_axis(axis, value, insetMin=0, insetMax=0):
    """
    Scales a value between 0 and 1 to the range of an axis,
    where an 'axis' is just a dict with values for the keys
    minValue and maxValue (i.e. what’s returned from drawBot’s
    `listFontVariations` call, for a given axis)

    `insetMin` and `insetMax` let you specify a narrower range
    than the minValue/maxValue, though you can also accomplish
    that by construct a dict(minValue=?,maxValue=?) with arbitrary
    values
    """
    minv = axis.get("minValue", 0) + insetMin
    maxv = axis.get("maxValue", 1000) - insetMax
    scaled = (value * (maxv - minv)) + minv
    return max(minv+1, min(maxv-1, scaled))  # avoid actual min/max