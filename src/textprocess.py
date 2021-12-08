import common
from common import TranslationFile
import re
from math import ceil
from uwu import uwuify

args = common.Args().parse()
if args.getArg("-h"):
    common.usage("[-t <story|home|race>] [-g <group>] [-id <id>] [-src <json file>] [-ll <line length>]",
                 "At least 1 arg is required.",
                 "-src overwrites other options.")

TARGET_TYPE = args.getArg("-t", "story").lower()
TARGET_GROUP = args.getArg("-g", None)
TARGET_ID = args.getArg("-id", None)
TARGET_FILE = args.getArg("-src", None)
VERBOSE = args.getArg("-V", False)
UWU = args.getArg("-uwu", False)

LINE_LENGTH = int(args.getArg("-ll", 44)) #Roughly 42-46 for most training story dialogue, 63-65 for wide screen stories (events etc)
NEWLINES = args.getArg("-nl", False)

if not TARGET_FILE and not TARGET_GROUP and not TARGET_ID: raise SystemExit("At least 1 arg is required.")

def process(file: TranslationFile, text: str, options: dict):
    if "noNewlines" in options and options['noNewlines']:
        text = cleannewLines(file, text)
    if "lineLen" in options:
        text = adjustLength(file, text, options['lineLen'] or LINE_LENGTH, targetLines = (options['targetLines'] if "targetLines" in options else 3))
    if "replace" in options:
        text = replace(text)
    if "uwu" in options and options["uwu"]:
        text = uwuify(text)
    return text

def cleannewLines(file: TranslationFile, text: str):
    return re.sub(r"\\n" if file.getType() == "race" else "\r?\n", " ", text)

def adjustLength(file: TranslationFile, text: str, lineLen: int = 0, numLines: int = 0, targetLines: int = 0):
    if len(text) < lineLen:
        if VERBOSE: print("Short text line, skipping: ", text)
        return text

    if lineLen > 0:
        #check if it's ok already
        lines = text.splitlines()
        tooLong = [line for line in lines if len(line) > lineLen]
        if not tooLong:
            if VERBOSE: print("Text passes length check, skipping: ", text)
            return text

        #adjust if not
        text = cleannewLines(file, text)
        # python regexes kinda suck
        lines = re.findall(f"(?:(?<= )|(?<=^)).{{1,{lineLen}}}(?= |$)|(?<= ).+$", text)
        nLines = len(lines)
        if nLines > 1 and len(lines[-1]) < min(lineLen, len(text)) / nLines:
            if VERBOSE: print("Last line is short, balancing on line number: ", lines)
            return adjustLength(file, text, numLines = nLines, targetLines = targetLines)

    elif numLines > 0:
        lineLen = ceil(len(text) / numLines)
        lines = re.findall(f"(?:(?<= )|(?<=^)).{{{lineLen},}}?(?= |$)|(?:(?<= )|(?<=^)).+$", text)

    if targetLines > 0 and len(lines) > targetLines:
        print(f"Exceeded target lines ({targetLines}) in {file.name} at: ", lines)
    return "\\n".join(lines) if file.getType() == "race" else "\n".join(lines)

def replace(text: str):
    data = common.readJson("src/data/replacer.json")
    for sub in data:
        text = re.sub(sub['re'], sub['repl'], text)
    return text

def main():
    if TARGET_FILE:
        files = [TARGET_FILE]
    else:
        files = common.searchFiles(TARGET_TYPE, TARGET_GROUP, TARGET_ID)

    print(f"Processing {len(files)} files...")
    for file in files:
        file = common.TranslationFile(file)
        for block in file.getTextBlocks():
            if not "enText" in block or len(block['enText']) == 0: continue
            block['enText'] = process(file, block['enText'], {"lineLen": LINE_LENGTH, "replace": True, "noNewlines": NEWLINES, "uwu": UWU})
        file.save()
    print("Files processed.")

if __name__ == '__main__':
    main()