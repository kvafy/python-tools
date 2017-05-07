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
  """
  Pretifies a file name, including its extension.
  Example:
    "S01E07 The.one.where.rachel.finds.out_HDTV.x264.brip.AVI"
    to
    "01x07 The One Where Rachel Finds Out.avi"
  """

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


# Interactive actions the user can take prior to renaming the files.
# Action is a function with the following behavior:
#   - 1st parameter: file name mappings as list of
#                    (old_file_name, new_file_name) tuples
#   - 2nd parameter: user input as string
#   - returns: tuple (new_file_name_mappings, is_program_done boolean)

def action_bad_input(mappings, action_args):
  print("Unrecognized command '%s'" % action_args)
  return (mappings, False)

def action_edit_one_mapping(mappings, action_args):
  entry_number = int(action_args)
  if not (0 < entry_number <= len(mappings)):
    print("You entered invalid entry number '%d'" % entry_number)
  else:
    idx = entry_number - 1
    (current_name, new_name) = mappings[idx]
    # TODO pre-fill the prompt with the current new_name value.
    response = prompt("Enter new name of '%s': " % new_name)
    mappings[idx] = (current_name, response or new_name)
  return (mappings, False)

def action_quit(mappings, action_args):
  return (mappings, True)

def action_rename_files_and_exit(mappings, action_args):
  for (current, new) in mappings:
    if current != new:
      os.rename(current, new)
  return (mappings, True)

def action_skip_one_mapping(mappings, action_args):
  entry_number = int(action_args)
  if not (0 < entry_number <= len(mappings)):
    print("You entered invalid entry number '%d'" % entry_number)
  else:
    idx = entry_number - 1
    mappings = mappings[:idx] + mappings[idx + 1:]
  return (mappings, False)


def interactive_rename(rename_mappings):
  ACTIONS = [
      # Shown label  Regexp                 Reference to action function
      ("Rename",     r"r(?:ename)?()",      action_rename_files_and_exit),
      ("Quit",       r"q(?:uit)?()",        action_quit),
      ("Skip #",     r"s(?:kip)? (\d+)",    action_skip_one_mapping),
      # Commented out because Python does not support pre-filling the prompt.
      #("Edit #",     r"e(?:dit)? (\d+)",    action_edit_one_mapping),
  ]

  def lookup_action(user_input):
    for (_, action_re, action_fn) in ACTIONS:
      mo = re.fullmatch(action_re, user_input, re.IGNORECASE)
      if mo:
        action_args_str = mo.group(1)
        return (action_fn, action_args_str)
    else:
      return (action_bad_input, user_input)

  def print_rename_mappings(mappings):
    print("\nSuggested renames:\n")
    for idx in range(len(mappings)):
      (current, new) = mappings[idx]
      print(" %3d. '%s'\n  --> '%s'" % (idx + 1, current, new))

  actions_str = " / ".join(action_name for (action_name, _, _) in ACTIONS)
  prompt_str = "\nAction (%s)? " % actions_str

  # Print the current mapping, prompt user for action, and again...
  while True:
    print_rename_mappings(rename_mappings)

    user_response = prompt(prompt_str)
    (action_fn, action_arg) = lookup_action(user_response)
    (rename_mappings, is_done) = action_fn(rename_mappings, action_arg)

    if is_done:
      break


if __name__ == "__main__":
  files = sys.argv[1:]
  rename_mapping = [(f, prettify(f)) for f in files]
  interactive_rename(rename_mapping)
