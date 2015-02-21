#!/usr/bin/env python3
# -*- coding: utf-8 -*-

############################################################################
# Author: David Chaloupka
# Date:   10.6.2010 - 6.8.2010
# Description: Removes diacritics from names of files and directories.
# Requirements:
#   * Python 3
############################################################################



import sys
import os
import optparse

# translacni tabulka
__translationTable = str.maketrans("áéěíýóöůúÁÉĚÍÝÓÖŮÚščřžťďňŠČŘŽŤĎŇ", "aeeiyoouuAEEIYOOUUscrztdnSCRZTDN")


def undiacritics(iterableOfStrings):
    '''V kazdem retezci nahradi non-ASCII znaky jejich ASCII ekvivalenty.'''
    return list(map(lambda x: x.translate(__translationTable), iterableOfStrings))


if __name__ == "__main__":
    description = ("Tool to batch-rename files whose names contain czech"
            "national character(s) to their plain ASCII equivalents.")
    # zpracovani parametru
    parser = optparse.OptionParser(description=description)
    parser.add_option("-n", "--non-interactive", action="store_true",
            default=False, help="assume \"yes\" answer everywhere")
    parser.add_option("-d", "--directory", metavar="DIR",
            help="directory to work in (default is current working"
            "directory)")
    options, args = parser.parse_args()

    # mame zadany adresar, ve kterem se ma pracovat => prepneme se
    if options.directory:
        try:
            os.chdir(sys.argv[1]) # prepneme se do pozadovaneho adresare
        except os.error as e:
            print("Error: given directory not found.")
            print("")
            sys.exit(1)

    # nacteme obsah pracovniho adresare
    contentOriginal = os.listdir(".")
    contentNew = undiacritics(contentOriginal)
    # soubory, ktere je treba prejmenovat ve tvaru dvojic (puvodni jmeno, nove jmeno)
    renamePairs = list(filter(lambda x: x[0] != x[1], zip(contentOriginal, contentNew)))

    if(len(renamePairs) > 0):
        # vypiseme nalezene dvojice
        print("found %d candidate(s) to rename:" % len(renamePairs))
        counter = 1
        for old,new in renamePairs:
            print("[%d]: \"%s\"  --->  \"%s\"" % (counter, old, new))
            counter += 1
        print("")
        # dotaz zda opravdu prejmenovat dane soubory
        # (v neinteraktivnim rezimu se nezepta)
        choice = options.non_interactive and "y" or "<no-value>"
        while choice.lower() not in ("y", "n"):
            choice = input("Proceed with renaming? (y/n): ")
        if choice.lower() == "y":
            # prejmenovani danych souboru
            counter = 1 # poradove cislo souboru
            successCount = 0
            for old,new in renamePairs:
                try:
                    print("renaming [%d]: \"%s\"  --->  \"%s\"" % (counter, old, new))
                    os.rename(old, new)
                    successCount += 1
                    print("   - OK")
                except os.error as e:
                    print("   - error (%s)" % str(e))
                counter += 1
            print("")
            print("renamed %d of %d file(s)" % (successCount, len(renamePairs)))
            print("")

    else:
        print("found no files to rename")
        print("")

    sys.exit(0)

