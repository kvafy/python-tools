#!/usr/bin/env python3

import argparse
import os
import os.path
import re

# ==========================
# = Intelligent ID3 Tagger =
# ==========================
# Specify a mask of the directory structure and/or of the filename to extract
# artist, album, year, song title etc. from.
# This script uses the eyeD3 utility to make the changes of ID3 tags.

# Typical usages:
#   ./iit.py --mask="%a/%A(%y)/%n - %t.mp3" *.mp3
#                 For songs such as .../Nightwish/Angels Fall First (1996)/01 - Elvenpath.mp3

# Changelog
#   TODO       Exception handling (os.error on the eyeD3 invocation, re.error on compile)
#   proposal   Maybe use os.Popen to better control over the process of eyeD3.
#   proposal   Enable kind of suffices for textual fields for changing the case
#              by converting the field by .capital() and .title() and a suffix
#              for the replacement of underscores ("_") by spaces.
#              Options:
#                 a) suffices %C, %T, %_
#                 b) suffices 'C, 'T, '_
#   2013/01/02 Utility created.

__author__ = "David Chaloupka"
__date__ = "2013/01/02"


NUMBER_REGEXP = " *[0-9]+ *"  # for numeric fields (track number, year)
TEXT_REGEXP = "[a-zA-Z0-9 .,'\"_?!()&-]+"  # for textual fields (artist, album, title)
RE_SPECIAL_CHARS = "*+?.()[]{}\\"


class IITException(Exception):
    """An exception for any error of this script."""
    pass


# filters (applied to filename and various extracted fields)
# ===========================================================================

def applyFilters(filters, str):
    ret = str
    for f in filters:
        ret = f(ret)
    return ret

def filterFileFullPath(file):
    return os.path.abspath(file)

def filterUndiacritics(s):
    translationTable = str.maketrans("áéěíýóöůúÁÉĚÍÝÓÖŮÚščřžťďňŠČŘŽŤĎŇ",
                                     "aeeiyoouuAEEIYOOUUscrztdnSCRZTDN")
    return s.translate(translationTable)

def filterTrans(oldC, newC):
    def innerFilter(s):
        return s.translate(str.maketrans(oldC, newC))
    return innerFilter

def filterStrip(s):
    return s.strip()

def filterCapitalWord(s):
    return s.title()

def filterFirstCapital(s):
    return s.capitalize()


# applied to a filename before further processing
filename_filters = [filterFileFullPath, filterUndiacritics]
# applied to extracted fields
field_filters = {
    "artist" : [filterTrans("_", " "), filterStrip],
    "album" :  [filterTrans("_", " "), filterStrip],
    "title" : [filterTrans("_", " "), filterStrip],
    "year" : [filterStrip],
    "track" : [filterStrip],
}



def parseCmdLine():
    parser = argparse.ArgumentParser(
        description="A utility to automatically tag MP3s according to the file " +
                    "path mask. For the tagging is used the utility eyeD3.",
        epilog="For example, mask " +
               "'%a/%A(%y)/%n - %t.mp3' works for files and directory structure " +
               "such as '.../Nightwish/Angels Fall First (1996)/01 - Elvenpath.mp3'."
        )
    parser.add_argument('files', metavar='mp3-file', type=str, nargs='+',
                        help='MP3 files whose ID3 tags are to be modified.')
    parser.add_argument('--mask', dest='mask', type=str, required=True,
                        help="The mask to extract the song information from. " +
                             "It may contain following expressions: " +
                             "%%a (artist), " +
                             "%%A (album), " +
                             "%%t (song title), " +
                             "%%y (album year), " +
                             "%%n (track number). "+
                             "Other than that, there may be any ordinary " +
                             "character including the directory path separator " +
                             "etc."
                        )
    parser.add_argument("--simulate", action="store_true", default=False,
                        help="Don't perform the tagging, just simulate the whole process.")
    return parser.parse_args()


def mask2Regexp(mask):
    """Return a compiled regexp from filename mask. The fields (?P<name>...)
       are used to capture the tag fields from path string.
    """
    defined_fields = set()
    def dispatchField(f):
        """Ensure that each field is defined at most once."""
        if f in defined_fields:
            raise IITException("the %s field is used more than once in mask" % f)
        defined_fields.add(f)
    result = ".*/"
    while mask:
        if mask.startswith("%a"): # artist
            dispatchField("artist")
            chars_consumed = 2
            result += "(?P<artist>%s)" % TEXT_REGEXP
        elif mask.startswith("%A"): # album
            dispatchField("album")
            chars_consumed = 2
            result += "(?P<album>%s)" % TEXT_REGEXP
        elif mask.startswith("%y"): # album year
            dispatchField("year")
            chars_consumed = 2
            result += "(?P<year>%s)" % NUMBER_REGEXP
        elif mask.startswith("%t"): # song title
            dispatchField("title")
            chars_consumed = 2
            result += "(?P<title>%s)" % TEXT_REGEXP
        elif mask.startswith("%n"): # track number
            dispatchField("track")
            chars_consumed = 2
            result += "(?P<track>%s)" % NUMBER_REGEXP
        elif mask.startswith("%"):
            raise IITException("unknown mask field \"%s\"" % mask[:2])
        elif mask.startswith("*"):
            chars_consumed = 1
            result += "[^%s]*" % os.sep
        else: # hard-coded character
            chars_consumed = 1
            if mask[0] in RE_SPECIAL_CHARS:  # need to be escaped
                result += "\\"
            result += mask[0]
        mask = mask[chars_consumed:]
    return re.compile(result)


def extractFields(string, regexp):
    """Return dictionary of field -> value."""
    matchobj = regexp.match(string)
    if matchobj:
        return matchobj.groupdict()
    else:
        raise IITException("unable to match filename \"%s\" with regexp \"%s\"" % (string, regexp.pattern))

def checkDependencies(deps):
    for depName, checkCommand in deps:
        if os.system(checkCommand) != 0:
            raise IITException("program \"%s\" is not installed." % depName)

def craftTaggingCommand(field_dict, file):
    cmd = "eyeD3"
    for field,value in field_dict.items():
        filtered_value = applyFilters(field_filters[field], value)
        cmd += " --%s=\"%s\"" % (field, filtered_value)
    cmd += " \"%s\"" % file
    return cmd


if __name__ == "__main__":
    config = parseCmdLine()
    try:
        checkDependencies([["eyeD3", "eyeD3 -h"]])
        extractionRegexp = mask2Regexp(config.mask)
        for filename in config.files:
            file_filtered = applyFilters(filename_filters, filename)
            fields_dict = extractFields(file_filtered, extractionRegexp)
            cmd = craftTaggingCommand(fields_dict, filename)
            if not config.simulate:
                os.system(cmd)
            else:
                print("simulating: %s" % cmd)
    except IITException as iitex:
        print("An error occured: " + str(iitex))
