import argparse
import tempfile
import importlib
from importlib.machinery import SourceFileLoader
import os
import sys
import json
from furniture.animation import Animation


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg


def main():
    parser = argparse.ArgumentParser(
        prog="furniture-renderer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("action", type=str)
    parser.add_argument("file", type=lambda x: is_valid_file(parser, x), metavar="FILE")
    parser.add_argument("-s", "--slice", type=str, default="")
    parser.add_argument("-pae", "--purgeAfterEffects", type=str2bool, default=False)
    parser.add_argument("-f", "--folder", type=str, default=None)
    parser.add_argument("-l", "--layer", type=str, default=None)
    parser.add_argument("-v", "--verbose", type=str2bool, default=False)
    args = parser.parse_args()

    sl = slice(*map(lambda x: int(x.strip()) if x.strip() else None, args.slice.split(':')))

    src_prefix = os.path.basename(args.file).replace(".py", "")
    src_dirname = os.path.realpath(os.path.dirname(args.file))
    src_path = os.path.realpath(args.file)
    folder = args.folder
    if folder == None:
        folder = f"{src_dirname}/{src_prefix}_frames"
        if not os.path.exists(folder):
            os.mkdir(folder)
    else:
        folder = os.path.realpath(folder)
        if not os.path.exists(folder):
            os.mkdir(folder)

    with open(args.file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # act like the app
    lines.insert(0, "from drawBot import *\n")
    lines.insert(1, "__file__ = '{}'\n".format(src_path))
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", encoding="utf-8") as temp:
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

        if args.action == "render":
            animation.render(indicesSlice=sl, folder=folder, purgeAfterEffects=args.purgeAfterEffects, log=args.verbose)
        
        print("-----")
        info = dict(animation.__dict__)
        del info["fn"]
        print(json.dumps(info))

if __name__ == "__main__":
    import sys
    sys.exit(main())