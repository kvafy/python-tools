'''
Author: David Chaloupka
Date:   18.8.2010 - 22.7.2012

Description
In the working directory deletes files that are bit duplicates. Matching is
performed first by size and then by MD5 hash. Useful for deleting duplicate
photos etc.

'''

import os
import os.path
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


VERBOSE = True # debug

# ziskani vsech souboru v adresari
dirContent = os.listdir(".")
files = [FileInfo(item) for item in dirContent if os.path.isfile(item)]
files.sort(key=lambda x: x.getPath())
# stable sort => zachova lexikograficke poradi predchoziho sortu
# itertools.groupby vyzaduje, aby byl seznam serazen dle "groupovaciho klice"
files.sort(key=lambda x: x.getSize())

# shlukovani souboru podle velikosti
groups = [list(group) for size, group in itertools.groupby(files, lambda f: f.getSize())]
duplicateGroups = [group for group in groups if len(group) > 1]
if VERBOSE:
    print("possible duplicates by file size:")
    if duplicateGroups:
        for group in duplicateGroups:
            print(" * " + ", ".join(map(lambda fileinfo: fileinfo.getPath(), group)))
    else:
        print(" - none")
    print()

# detekce duplikatu testovanim na rovnost v O(n^2)
# (slo by taky sesortit pomoci porovnani slozenym klicem (size, md5), kde
# by se hash pocital pouze pro soubory stejne velikosti v __lt__, ale
# souboru pravdepodobne nebude tolik, aby nas redukce na O(n*log n) trapila.
for group in duplicateGroups:
    while len(group) > 1:
        originalFile = group.pop(0)
        i = 0
        while i < len(group):
            iFile = group[i]
            if originalFile == iFile: # dle velikosti a md5 hashe
                try:
                    os.remove(iFile.getPath())
                    if VERBOSE:
                        print("deleted file \"%s\"" % iFile.getPath())
                except OSError as e:
                    print("can't delete \"%s\" (%s)" % (iFile.getPath(), str(e)))
                finally:
                    # vymazeme duplikat (jinak soubor zustava do dalsi
                    # iterace prvniho whilu)
                    group.pop(i)
            else:
                i += 1
