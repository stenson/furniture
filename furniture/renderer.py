import argparse
import tempfile
import importlib
from importlib.machinery import SourceFileLoader
import os
import sys
from furniture.animation import Animation


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def main():
    parser = argparse.ArgumentParser(
        prog="furniture-renderer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("file", type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument("-s", "--slice", type=str, default="")
    parser.add_argument("-pae", "--purgeAfterEffects", type=str2bool, default=False)
    parser.add_argument("-f", "--folder", type=str, default="frames")
    args = parser.parse_args()

    sl = slice(*map(lambda x: int(x.strip()) if x.strip() else None, args.slice.split(':')))

    lines = args.file.readlines()
    lines.insert(0, "from drawBot import *\n")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as temp:
        temp.write("".join(lines))
        temp.flush()
        mod = os.path.basename(temp.name)
        dirname = os.path.dirname(temp.name)
        src = SourceFileLoader(mod, temp.name).load_module()
        animation = None
        for k, obj in src.__dict__.items():
            if isinstance(obj, Animation):
                animation = obj
        
        if not animation:
            raise Exception("No furniture.animation.Animation object found in src file")
        
        # make the folder if it doesn’t exist
        animation.render(indicesSlice=sl, folder=args.folder, purgeAfterEffects=args.purgeAfterEffects)

        #sys.path.append(dirname)
        #importlib.import_module(mod)
        #print(mod, dirname)
        #p = Popen(["osascript", "-e", script])
        #stdout, stderr = p.communicate()
        #return p.returncode, stdout, stderr

if __name__ == "__main__":
    import sys
    sys.exit(main())