#!/usr/bin/env python3
# -*- coding: utf-8 -*-


################################################################################
#                                                                              #
# Author: David Chaloupka                                                      #
# Name: FileRenamer                                                            #
#                                                                              #
# Development start: 6.8.2009                                                  #
# Last modification: 19.6.2010                                                 #
# Requires:          Python 3.0                                                #
#                                                                              #
#                                                                              #
# Desription:                                                                  #
# ----------                                                                   #
# Program pro hromadné přejmenování souborů, zejména pak titulků k seriálům    #
# ap. Funguje tak, že "promítne" (viz. Definitions) jména souborů daných       #
# source specific pattern na odpovídající soubor vyhovují destination          #
# specific pattern.                                                            #
#                                                                              #
#                                                                              #
# Usage (Užití):                                                               #
# -------------                                                                #
# ./fr.py [-s salt] sourceSpecificPattern destinationSpecificPattern           #
# ./fr.py [--salt salt] sourceSpecificPattern destinationSpecificPattern       #
#                                                                              #
# Příklad:                                                                     #
# ./fr.py -s ".cze" "<s:\d>x<ep:\d{2}>" "s0<s:\d>e<ep:\d{2}>"                  #
# promítne jméno souboru "4x10 - The Fight.avi" na soubor "himym_s04e10.srt",  #
# takže "himym_s04e10.srt" přejmenuje na "4x10 - The Fight.cze.srt". Obdobné   #
# přejmenování provede pro všechny další odpovídající si dvojice v adresáři.   #
#                                                                              #
#                                                                              #
# Definitions:                                                                 #
# -----------                                                                  #
# promítnutí = Chceme-li promítnout název souboru x na soubor y za použití     #
#              salt, znamená to, že po promítnutí se bude soubor y jmenovat    #
#              stejně jako soubor x; zachována zůstane pouze koncovka souboru  #
#              a bezprostředně před ní bude přidána salt.                      #
#              Příklad: promítnutí zdroje "1x04 - Bachelor party.avi" na cíl   #
#              "nameIDontLike.srt" se salt=".cze" znamená, že cílový soubor    #
#              "nameIDontLike.srt" je podle zdroje přejmenován na              #
#              "1x04 - Bachelor party.cze.srt"                                 #
#                                                                              #
# Specific pattern = Jedná se o formu regulérního výrazu, ve kterém            #
#              specifikujeme jména polí, která se mají sobě rovnat. Jinak      #
#              obsahuje cokoli kolem, což má formát regulárního výrazu.        #
#              Označuje-li regexp ve specific pattern group výhradně číslo     #
#              (tj. "\d", "\d*", "\d{2,3}"...), vyhodnocuje se rovnost groups  #
#              jako rovnost čísel; jinak se rovnost vyhodnocuje jako u řetězců.#
#              Formální tvar specific pattern group:                           #
#                "<", SPECIFIC_PATTERN_GROUPNAME, ":", regexp, ">"             #
#                - SPECIFIC_PATTERN_GROUPNAME je identifikátor pole            #
#                - FileRenamer.SPECIFIC_PATTERN_GROUPNAME_LEGAL_CHARACTERS     #
#                  jsou znaky dovolené pro SPECIFIC_PATTERN_GROUPNAME          #
#                - regexp je regulérní výraz, kterému má group odpovídat       #
#              Příklad:                                                        #
#                "s0<number1:\d>e<number2:\d{2}>", "s<season:\d+>e<ep:\d+>"    #
#                jsou specific pattern pro soubor "friends.s02e18.cz.srt".     #
#                                                                              #
# CHANGELOG                                                                    #
# 19.6.2010 - soubory, jejichž název by se nezměnil, nejsou při projekci       #
#             uvažovány                                                        #
#                                                                              #
################################################################################



import os
import sys
import re




class FileRenamer:

    # povolené znaky pro název specific pattern group
    SPECIFIC_PATTERN_GROUPNAME_LEGAL_CHARACTERS = "[A-Za-z0-9_-]"
    # regexp pro matchování groups ve specific pattern
    _SPECIFIC_PATTERN_GROUP_MATCHER = re.compile("<(?P<id>" + SPECIFIC_PATTERN_GROUPNAME_LEGAL_CHARACTERS + "+):(?P<re>[^>]+)>")
    


    def projectNames(sourceSpecificPattern, destinationSpecificPattern, salt=""):
        '''
        V aktuálním adresáři provede promítnutí jmen souborů. Platí, že
        názvy souborů odpovídající sourceSpecificPattern budou promítnuty
        na soubory odpovídající destinationSpecificPattern, kde v příslušné
        dvojici se musí rovnat části se stejným SPECIFIC_PATTERN_NAME.
        Vyhazuje re.error pri nespravnem regularnim vyrazu.
        '''
        
        # načteme obsah adresáře a jména souborů roztřídíme podle toho, zda odpovídají source/destination specific pattern
        fileList = os.listdir(".")

        sourceFileList = []
        destinationFileList = []

        sourceMatcher = re.compile(FileRenamer._specificPatternToRE(sourceSpecificPattern))
        destinationMatcher = re.compile(FileRenamer._specificPatternToRE(destinationSpecificPattern))

        for fileName in fileList:
            if sourceMatcher.match(fileName):
                sourceFileList.append(fileName)
            elif destinationMatcher.match(fileName):
                destinationFileList.append(fileName)

        # vyhledáme odpovídající si páry v source a destination file listech
        
        # identifikátory proměnných polí ve specific pattern
        # (bereme pouze názvy vyskytujících se v obou patterns)
        groupsSource = FileRenamer._getSpecificPatternGroups(sourceSpecificPattern)
        groupsDestination = FileRenamer._getSpecificPatternGroups(destinationSpecificPattern)

        if set(groupsSource) ^ set(groupsDestination):
            print("warning: in source and destination patterns aren't the same names")
        specificPatternGroups = list( set(groupsSource) & set(groupsDestination) )


        # páry souborů, které k sobě podle jejich specific patterns groups patří
        matchedPairs = []

        for sourceFile in sourceFileList:
            sourceFileMatchObj = sourceMatcher.match(sourceFile)
            # porovnání všech souborů se všemi
            for destinationFile in destinationFileList:
                destinationFileMatchObj = destinationMatcher.match(destinationFile)
                
                # rovnají se všude všechny groups?
                for patternGroup in specificPatternGroups:
                    srcGroup = sourceFileMatchObj.group(patternGroup)
                    dstGroup = destinationFileMatchObj.group(patternGroup)                    
                    try:
                        # groups, které jsou výhradně číselné porovnáváme jako čísla, jinak porovnáváme řetězcově
                        if srcGroup == dstGroup or int(srcGroup) == int(dstGroup):
                            pass
                        else:
                            break # groups se nerovnají jako řetězce a ani jako čísla
                    except ValueError: # groups nejsou číselné
                        break
                # dvojice souborů k sobě patří (nebyl nalezen konflikt v žádné group (= poli))
                else:
                    matchedPairs.append((sourceFile, destinationFile))
                    destinationFileList.remove(destinationFile)
        
        if len(matchedPairs) == 0:
            print("No matching pairs of files were found.")
            return

        # vypsání párů a dotázání se uživatele zda si přeje pokračovat
        FileRenamer._printProjectedNames(matchedPairs, salt)
        choice = input("\n\nDo you want to proceed with renaming? (y/n): ")
        if choice.lower() not in ("y", "yes"):
            return
        
        # přejmenování souborů
        fails = 0
        for (source, oldDestinationName) in matchedPairs:
            newDestinationName = FileRenamer._getProjectedName(source, oldDestinationName, salt)
            print("renaming \"%s\"" % oldDestinationName)
            print("  to \"%s\"" % newDestinationName)
            try:
                os.rename(oldDestinationName, newDestinationName)
            except OSError:
                fails += 1

        print("\nRenaming done! (%d of %d files renamed succesfully)" % (len(matchedPairs)-fails, len(matchedPairs)))



    def _getProjectedName(sourceFile, destinationFile, salt):
        '''
        Vrátí jméno, které bude mít destinationFile po promítnutí přes
        sourceFile. salt je koncovka přidávaná bezprostředně před příponu
        výsledného souboru (např. ".cze").
        '''
        ret = ""

        # odstraníme koncovku source souboru
        if sourceFile.rfind(".") != -1:
            ret = sourceFile[:sourceFile.rfind(".")]
        else:
            raise ParameterException("sourceFile %s has no file extension" % sourceFile)

        if salt:
            ret += salt

        # zachováme koncovku destinationFile
        if destinationFile.rfind(".") != -1:
            ret += destinationFile[destinationFile.rfind("."):]

        return ret




    
    def _printProjectedNames(pairs, salt):
        '''
        Vypíše jak budou soubory přejmenovány. Pairs je iterable párů
        (sourceFile, destinationOriginalFile), kde sourceFile je původní
        název souboru, který se promítne na destinationOriginalFile.
        '''
        print("Following files match together:")
        for (a, b) in pairs:
            print("\"%s\"" % a)
            print(" - old: \"%s\"" % b)
            print(" - new: \"%s\"" % FileRenamer._getProjectedName(a, b, salt))
    


    def _specificPatternToRE(pattern):
        '''
        Specific pattern převádí na regexp a tento vrací. Pojmenování
        polí ve specific pattern se promítne do pojmenování skupin ve
        výsledném regexpu.

        Příklad:
        >>> pattern = "<season:\\d>x<episode:\\d{2}>"
        >>> return_value = _specificPatternToRE(pattern)
        >>> return_value
        >>> "(?P<season>\\d)x(?P<episode>\\d{2})"
        ...
        >>> re.match(return_value, "himym 3x15 - Goat.srt").group("episode")
        >>> 15
        '''
        result = ""

        while pattern != "":
            matchObj = FileRenamer._SPECIFIC_PATTERN_GROUP_MATCHER.search(pattern)

            # v pattern máme konstantní část specific pattern, kterou beze změny zkopírujeme
            if not matchObj or matchObj.start() != 0:
                if matchObj: numberOfCharsToCopy = matchObj.start()
                else: numberOfCharsToCopy = len(pattern)

                result += pattern[:numberOfCharsToCopy]
                pattern = pattern[numberOfCharsToCopy:]

            # zpracováváme regexp část specific pattern
            if matchObj:
                if not matchObj.group("id"):
                    raise ArgumentException("specific pattern group has no groupname (pattern: %s)" % matchObj.group(0))
                if not matchObj.group("re"):
                    raise ArgumentException("specific pattern group has no regexp (pattern: %s)" % matchObj.group(0))
                result += "(?P<" + matchObj.group("id") + ">" + matchObj.group("re") + ")"
                pattern = pattern[len(matchObj.group(0)):]
        return "^.*" + result + ".*$"



    def _getSpecificPatternGroups(pattern):
        '''
        Z dané specific pattern vyextrahuje jména proměnných polí a vrátí je
        jako list stringů.
        '''
        ret = []

        while pattern != "":
            matchObj = FileRenamer._SPECIFIC_PATTERN_GROUP_MATCHER.search(pattern)
            if matchObj:
                ret.append(matchObj.group("id"))
                pattern = pattern[matchObj.end():]
            else:
                pattern = ""

        return ret
                




#############################################################################
#######################               UI               ######################
#############################################################################

sourceSpecificPattern = ""
destinationSpecificPattern = ""
salt = ""


# zpracování parametrů příkazové řádky

print()
argc = len(sys.argv)
if argc not in (2, 3, 5):
    print("error: incorect parameters")
    exit(2)

if argc == 2:
    if sys.argv[1] not in ("-h", "--help"):
        print("error: incorect parameter \"%s\"" % sys.argv[1])
        exit(2)
    else:
        print("FileRenamer")
        print("(c) David Chaloupka")
        print()
        print("usage: ./fr.py [-s|--salt salt] sourceSpecificPattern destinationSpecificPattern")
        print("example: ./fr.py -s \".cze\" \"<season:\d>x<episode:\d{2}>\" \"s0<season:\d>e<episode:\d{2}>\"")
        print()
        print("For more extensive help read begining of source file fr.py.")
        exit(0)
elif argc == 5:
    if sys.argv[1] not in ("-s", "--salt"):
        print("error: incorect parameter \"%s\"" % sys.argv[1])
        exit(2)
    salt = sys.argv[2]

sourceSpecificPattern = sys.argv[-2]
destinationSpecificPattern = sys.argv[-1]


# tisk vstupních parametrů, prostředí
print("FileRenamer")
print("(c) David Chaloupka")
print()
print("working directory:            %s" % os.getcwd())
print("source specific pattern:      %s" % sourceSpecificPattern)
print("destination specific pattern: %s" % destinationSpecificPattern)
print("salt:                         %s" % salt)
print("-" * 76)
print(end="\n\n")

# samotné promítnutí
try:
    FileRenamer.projectNames(sourceSpecificPattern, destinationSpecificPattern, salt)
except re.error:
    print("Error: invalid regular expression.")
print()

