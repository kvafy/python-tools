#!/usr/bin/env python3

#
# Video file name pretifier.
# Takes file names holding episodes of a series and renames them to a nicer
# form (question of personal preferences).
#
# Synopsis: <script> FILES
#

import os
import re
import sys


def prettify(file_name):
  mo = re.fullmatch(r"(?P<name>.*)\.(?P<ext>[a-zA-Z0-9]+)", file_name)
  if not mo:
    # Skip files without extension.
    return file_name

  name, ext = mo.group("name"), mo.group("ext")

  # Normalize word delimiters to spaces.
  name = re.sub(r"[-_.]", " ", name)

  # Strip garbage suffix (eg. 1080p, HDTV, etc.).
  GARBAGE_SUFFIXES = [
    r"(720|1080)p",
    r"(5\.1|6)ch",
    r"Blue?Ray",
    r"h264",
    r"HDTV",
    r"(b|dvd|x)rip",
  ]
  garbage_start = r"\b(" + "|".join(GARBAGE_SUFFIXES) + r")\b"
  mo = re.fullmatch("(.*?)" + garbage_start + ".*", name, re.IGNORECASE)
  if mo:
    name = mo.group(1)

  # Translate s01e01 -> 01x01
  mo = re.fullmatch(
      r"(?P<prefix>.*)[sS](?P<season>\d+)[eE](?P<episode>\d+)(?P<suffix>.*)",
      name)
  if mo:
    season, episode = int(mo.group("season")), int(mo.group("episode"))
    sxe = ("%02d" % season) + "x" + ("%02d" % episode)
    name = mo.expand("\g<prefix>" + sxe +"\g<suffix>")

  # Capitalize.
  name = " ".join([word.capitalize() for word in re.split(r"\s+", name)])

  # Normalize whitespace.
  name = re.sub(r"\s{2,}", " ", name.strip())

  # Extension to lowercase
  ext = ext.lower()

  return name + "." + ext


def prompt(question):
  return input(question)


def rename_files(mappings):
  for (current, new) in mappings:
    if current != new:
      os.rename(current, new)



if __name__ == "__main__":
  files = args

  rename_mapping = [(f, prettify(f)) for f in files]

  while True:
    print("Suggested renames:")
    for (current, new) in rename_mapping:
      print("[%s]\n  --> [%s]" % (current, new))

    proceed = prompt("Proceed? (y/n) ").lower()
    if proceed == "y":
      rename_files(rename_mapping)
      break
    elif proceed == "n":
      break

    print("\n-----------------------------------------\n")
