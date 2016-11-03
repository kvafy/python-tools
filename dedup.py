'''
Author: David Chaloupka
Date:   18.8.2010 - 3.11.2016

Description
Finds duplicate files in the working directory and its subdirectories and
interactively decides what to do with them.
Matching of duplicates is performed first by file size and then by MD5 hash.
'''

import os
import os.path
import sys
import re
import itertools
import hashlib


class FileInfo:
    def __init__(self, path):
        self._path = path
        self._size = os.path.getsize(self._path)
        self._md5 = None

    def getSize(self):
        return self._size
    def getPath(self):
        return self._path
    def getMD5(self):
        if self._md5 is None:
            self._computeMD5()
        return self._md5

    def _computeMD5(self):
        m = hashlib.md5()
        f = None
        try:
            self._md5 = "error"
            f = open(self._path, "rb")
            buffer = f.read(1024)
            while buffer:
                m.update(buffer)
                buffer = f.read(1024)
            self._md5 = m.hexdigest()
        except IOError:
            self._md5 = "error"
        finally:
            f and f.close()

    def __eq__(self, item):
        return (self._size == item._size
                and self.getMD5() == item.getMD5()
                and self.getMD5() != "error"
                #and FileInfo.bitcmp(self.getPath(), item.getPath()) == 0
                )

    def __repr__(self):
        return "'%s' (%d B, md5: %s)" % (self._path, self._size, str(self._md5))

    @staticmethod
    def bitcmp(file1, file2):
        f1, f2 = None, None
        try:
            f1 = open(file1, "rb")
            f2 = open(file2, "rb")
            b1, b2 = f1.read(1), f2.read(1)
            while b1 and b2:
                if b1 != b2:
                    return 1
                b1, b2 = f1.read(1), f2.read(1)
            if b1 == b2:
                return 0
            else:
                return 1
        except IOError:
            return 1
        finally:
            f1 and f1.close()
            f2 and f2.close()


def listAllFiles(rootDir):
    entries = [os.path.join(rootDir, e) for e in os.listdir(rootDir)]
    files = [FileInfo(item) for item in entries if os.path.isfile(item)]
    for subdir in [item for item in entries if os.path.isdir(item)]:
        files.extend(listAllFiles(subdir))
    return files

def groupsWithDuplicates(files):
    # first group by file size...
    # sort required by itertools.groupby
    files.sort(key=lambda f: f.getSize())
    equiSizeGroups = [list(group) for _, group in itertools.groupby(files, lambda f: f.getSize())]
    equiSizeGroups = [g for g in equiSizeGroups if len(g) > 1]

    # ...then group based on md5
    duplicateGroups = []
    for equiSizeGroup in equiSizeGroups:
        equiSizeGroup.sort(key=lambda f: f.getMD5())
        equiMD5Groups = [list(group) for _, group in itertools.groupby(equiSizeGroup, lambda f: f.getMD5())]
        equiMD5Groups = [g for g in equiMD5Groups if len(g) > 1]
        duplicateGroups.extend(equiMD5Groups)

    return duplicateGroups

def openFile(file):
    if sys.platform == "linux":
        os.system("xdg-open '%s' > /dev/null 2>&1" % file)
    elif sys.platform == "win32":
        os.system("open '%s'" % file)
    elif sys.platform == "darwin":
        os.system("start '%s'" % file)
    else:
        raise Error("Unknown Operating system '%s'" % sys.platform)

if __name__ == "__main__":
    files = listAllFiles(".")
    groups = groupsWithDuplicates(files)
    # show groups with biggest size first
    groups.sort(key=lambda g: g[0].getSize(), reverse=True)

    print("Found %d groups of identical files." % len(groups))

    for group in groups:
        resolved = False
        while not resolved:
            print()
            print("Resolve following files:")
            for i in range(len(group)):
                print("  %d) %s" % (i+1, group[i]))
            print()

            action = input("Action? (Preserve #, Open, Next) ")
            if action in ["n", "next"]:
                resolved = True
            elif action in ["o", "open"]:
                openFile(os.path.normpath(group[i].getPath()))
            elif re.match(r"p(preserve)? \d+", action):
                iPreserve = int(re.match(r"p(preserve)? (\d+)", action).group(2)) - 1
                for toDelete in [group[i] for i in range(len(group)) if i != iPreserve]:
                    try:
                        os.remove(toDelete.getPath())
                    except OSError as e:
                        print("Error: can't delete \"%s\" (%s)" % (toDelete.getPath(), str(e)))
                resolved = True
            else:
                print("Unrecognized action '%s', try again" % action)
