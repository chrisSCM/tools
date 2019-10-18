import argparse
import re
from pathlib import Path

desc = ("Extract plain strings (to be translated) to a "
        "language file and replace strings in the sources.")
parser = argparse.ArgumentParser(description=desc)
# parser.add_argument('filetype', help='type of files to handle')
# -> this is only good for PHP right now...
parser.add_argument('folder', help='folder containing source files')
parser.add_argument(
    'origlang',
    help='language file containing the original coding language'
)

args = parser.parse_args()

# ft = args.filetype
ft = "php"
f = Path(args.folder)
lf = Path(args.origlang)


def parse_fields(fields):
    parsed = []
    for f in fields:
        f = f.strip()
        parsed.append(f.replace("'", "").replace('"', ''))
    t = (parsed[1], parsed[0])
    return t


lang = {}
lang_text = lf.read_text()
for line in lang_text.split("\n"):
    if line.startswith('define'):
        line = line.replace('define(', '').replace(');', '')
        fields = line.split(',')
        (key, val) = parse_fields(fields)
        # Handle duplicates...but this won't take care of multiple values ;-)
        #  This mark will be easy to remove afterwards, when cleaning up
        #  the language file.
        if key in lang.keys():
            key = f"{key} (2)"
        lang[key] = val


print(f"Parsing {ft}-files in folder '{f}'!")

# This is the pattern from hell :-)
# It doesn't work too bad, though.
# (And it's made for the French language!)
pattern = (
    ">[\n]*"
    "("
    "[àâäèéêëîïôœùûüÿçÀÂÄÈÉÊËÎÏÔŒÙÛÜŸÇa-zA-Z\s]*"
    "&*[a-zA-Z]*;*"
    "[àâäèéêëîïôœùûüÿçÀÂÄÈÉÊËÎÏÔŒÙÛÜŸÇa-zA-Z\s]*"
    "&*[a-zA-Z]*;*"
    "[àâäèéêëîïôœùûüÿçÀÂÄÈÉÊËÎÏÔŒÙÛÜŸÇa-zA-Z\s]*"
    "&*[a-zA-Z]*;*"
    "\s*:*\s*"
    ")"
    "[\n]*"
    "<"
)

simple_text = re.compile(pattern)

FOLDER_DONE = "FOLDER_DONE"
FOLDER_IGNORE = "FOLDER_IGNORE"

g = f"**/*.{ft}"
for p in sorted(f.glob(g)):
    i = 1
    if p.is_file():
        if (
            len(list(p.parent.glob(FOLDER_DONE))) > 0 or
            len(list(p.parent.glob(FOLDER_IGNORE))) > 0
        ):
            print(f"Folder {p.parent}\nalready done or to be ignored!")
            continue
        fn = p.stem
        print(f"{ft} found! -> {p}")
        text = p.read_text()
        match_list = simple_text.findall(text)
        clean_list = []
        for m in match_list:
            s = m.strip()
            if s != '' and s != "\n":
                clean_list.append(s)

        for s in sorted(clean_list, key=len, reverse=True):
            # print(s)
            key = None
            try:
                key = lang[s]
            except KeyError as e:
                pass
            if key is None:
                # Add to language file!
                key = f"_{fn.upper()}{str(i).zfill(3)}"
                lang[s] = key
                # print(f"Add key '{key}' to lang with value '{s}'")
                i += 1
            code_snippet = f"<?={key}?>"
            print(f"Replace '{s}' in file with '{code_snippet}'")
            text = text.replace(s, code_snippet)
        new_file = Path(f"{p}.new")
        new_file.write_text(text)


def touch_done_file(folder):
    done_file = folder / FOLDER_DONE
    done_file.touch()


# Create the "done" file in the given folders and subfolders.
touch_done_file(f)
# Loop again to create "done" files!
for p in f.glob("**"):
    if p.is_dir():
        # Create a file to mark the folder as "done".
        touch_done_file(p)


def by_value(item):
    return item[1]


# Build new language file
lf_new = Path(f"{lf}.new")
new_text = "<?php\n"
for k, v in sorted(lang.items(), key=by_value):
    new_text += f"define(\"{v}\", \"{k}\");\n"
new_text += "?>"
lf_new.write_text(new_text)
