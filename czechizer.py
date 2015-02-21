#!/usr/bin/env python3

# Author: David Chaloupka
# Date: 2013-03-18
# Description: Purpose of this utility is to auto-detect character encoding
#              of a czech text file and to encode given files in-place to
#              utf-8. Useful for movie subtitle files.


import argparse
import os
import sys


feature_chars = "áÁčČďĎéÉěĚíÍóÓřŘšŠťŤúÚůýÝžŽ" # what characters are special in czech
possible_encodings = ("cp1250", "utf-8", "iso-8859-2")
target_encoding = "utf-8"


def detect_encodings(filenames):
    return [(filename, detect_encoding(filename)) for filename in args.files]

def detect_encoding(filename):
    """For given file return name of the most probable encoding or None."""
    def count_occurences(needle_list, haystack):
        return sum([haystack.count(needle) for needle in needle_list])
        
    handle = None
    try:
        handle = open(filename, "rb")
        content = handle.read()
        hit_counts = [(None, 0)]
        for enc_name in possible_encodings:
            enc_feature_chars = [c.encode(enc_name) for c in feature_chars]
            enc_hits = count_occurences(enc_feature_chars, content)
            hit_counts.append((enc_name, enc_hits))
        hit_counts.sort(reverse=True, key=lambda pair: pair[1]) # stable sort (for no hits "unknown" stays first)
        return hit_counts[0][0]
    except IOError as ioerr:
        return None
    finally:
        handle and handle.close()

def convert_file_encoding(filename, enc_from, enc_to):
    """Try to convert given file in-place from given encoding to given encoding. Return boolean indicating success."""
    handle = None
    try:
        handle = open(filename, "rb+")
        content_raw = handle.read()
        content_str = content_raw.decode(enc_from)
        content_raw_new = content_str.encode(enc_to)
        handle.seek(0, os.SEEK_SET)
        handle.write(content_raw_new)
        return True
    except (IOError, UnicodeError):
        return False
    finally:
        handle and handle.close()


if __name__ == "__main__":
    # process command line
    parser = argparse.ArgumentParser(description=('Convert czech text files from whatever encoding to %s.' % target_encoding))
    parser.add_argument('files', metavar='file', type=str, nargs='+',
                       help='files to convert')
    parser.add_argument('-d', dest='detect', action='store_const',
                       const=True, default=False,
                       help='just detect encodings of given files')
    parser.add_argument('-c', dest='convert', action='store_const',
                       const=True, default=False,
                       help='convert given files to the target encoding')
    args = parser.parse_args()
    
    
    
    # get into action
    if not args.detect and not args.convert:
        print("Error: no action specified (see help)")
        sys.exit(1)
    elif args.detect:
        filename_column_width = max(map(len, args.files))
        format_string = "    %" + str(filename_column_width) + "s    %s"
        print(format_string % ("Filename", "Detected encodings"))
        for filename, encoding in detect_encodings(args.files):
            print(format_string % (filename, encoding))
    elif args.convert:
        filename_column_width = max(map(len, args.files))
        format_string = "    %" + str(filename_column_width) + "s    %s"
        print(format_string % ("Filename", "Conversion status"))
        for file_name, file_enc in detect_encodings(args.files):
            if not file_enc:
                status = "error: encoding not detected"
            elif file_enc == target_encoding:
                status = "already in %s" % target_encoding
            else:
                status = convert_file_encoding(file_name, file_enc, target_encoding) and "OK" or "error: conversion failed"
            print(format_string % (file_name, status))
