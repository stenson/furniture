import argparse
import tempfile
import importlib
from importlib.machinery import SourceFileLoader
import os
import sys
import json
from furniture.animation import Animation

try:
    from fontTools.misc.cliTools import makeOutputFileName
except:
    print("fontTools not installed")
    pass

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
    parser.add_argument("-f", "--folder", type=str, default=None)
    parser.add_argument("-l", "--layer", type=str, default=None)
    parser.add_argument("-v", "--verbose", type=str2bool, default=True)
    parser.add_argument("-a", "--audio", type=str2bool, default=True)
    parser.add_argument("-c", "--compile", type=str, default=None)
    parser.add_argument("-so", "--stdout", type=str, default=None)
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

    if args.stdout:
        logpath = os.path.realpath(args.stdout)
        print(logpath)
        if not os.path.exists(logpath):
            with open(logpath, "w") as f:
                pass
        sys.stdout = open(logpath, "a")
        sys.stderr = open(logpath, "a")
    
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

        for layer in animation.layers:
            if animation.fmt != "ufo":
                subfolder = folder + "/" + layer
                if not os.path.exists(subfolder):
                    os.mkdir(subfolder)

        if args.action == "render":
            try:
                if animation.fmt == "ufo":
                    ufo_folder = folder + "/ufos"
                    if not os.path.exists(ufo_folder):
                        os.mkdir(ufo_folder)

                animation.render(indicesSlice=sl, folder=folder, log=args.verbose)
                if args.audio:
                    os.system("afplay /System/Library/Sounds/Pop.aiff ")
                
                if args.compile:
                    if animation.fmt == "ufo":
                        ttf_folder = folder + "/ttfs"
                        if not os.path.exists(ttf_folder):
                            os.mkdir(ttf_folder)
                        # needs to support layers
                        for layer in animation.layers:
                            ttf_name = makeOutputFileName(ttf_folder + "/" + animation.name + "_" + layer, extension=".ttf")
                            ufo_path = ufo_folder + "/" + animation.name + "_" + layer + ".ufo"
                            fontmake_cmd = f"fontmake --output-path {ttf_name} -o ttf -u {ufo_path}"
                            print(fontmake_cmd)
                            os.system(fontmake_cmd)
                        os.system("afplay /System/Library/Sounds/Bottle.aiff ")
                    else:
                        print("Compliation not supported")
                        os.system("afplay /System/Library/Sounds/Basso.aiff ")
            except Exception as e:
                import traceback
                traceback.print_exc()
                if args.audio:
                    os.system("afplay /System/Library/Sounds/Sosumi.aiff ")
        
        if args.action == "info":
            print("-----")
            info = dict(animation.__dict__)
            del info["fn"]
            print(json.dumps(info))

if __name__ == "__main__":
    import sys
    sys.exit(main())