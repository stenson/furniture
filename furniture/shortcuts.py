import sys
import os
import importlib
try:
    from drawBot import savedState
    import drawBot as db
except:
    pass


def add_importable(path):
    """
    Add a path to the beginning of sys.path
    """
    sys.path.insert(0, os.path.expanduser(path))


def reimport(module):
    """
    Import a module from a string, and also reload it;
    also, return it
    """
    m = importlib.import_module(module)
    importlib.reload(m)
    return m


class PreparedStateManager():
    def __init__(self, style):
        self.style = style

    def __enter__(self):
        db.save()
        for k, v in self.style.items():
            db.fill(None)
            db.stroke(None)
            db.strokeWidth(1)
            getattr(db, k)(*v)
        return self

    def __exit__(self, type, value, traceback):
        db.restore()


def preparedState(**kwargs):
    """
    Pass drawBot presentation functions as dict entries
    for terser `with savedState` calls
    """
    return PreparedStateManager(kwargs)


if __name__ == "__main__":
    db.newDrawing()
    with preparedState(fill=(0, 1, 0)):
        db.fill(None)
        db.stroke(None)
        db.strokeWidth(1)
        db.rect(0, 0, 100, 100)
    db.saveImage("~/Desktop/preparedstate.png")
    db.endDrawing()

    add_importable("~/Type/grafutils")
    print(reimport("furniture.animation"))