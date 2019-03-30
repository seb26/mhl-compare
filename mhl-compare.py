#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (c) Sebastian Reategui 2019, all rights reserved
# MIT License

import sys
import os
import argparse
import codecs
from datetime import datetime

import xmltodict
import humanize
from dateutil.tz import tzutc
from dateutil import parser as dateutilParser
from termcolor import colored
from lib.dictdiffer import DictDiffer

# Program defaults
HASH_TYPE_PREFERRED = 'xxhash64be'
HASH_TYPES_ACCEPTABLE = [ 'xxhash64be', 'xxhash64', 'xxhash', 'md5', 'sha1' ]

LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_VERBOSE = False  # By default, don't show detail about which files changed

LOG_COLOR_MHL_A = 'green'
LOG_COLOR_MHL_B = 'yellow'
LOG_COLOR_WARNING = 'red'
LOG_COLOR_INFORMATION = 'cyan'
LOG_COLOR_BOLD = [ 'bold' ]

if getattr( sys, 'frozen', False ):
    LOG_APPTYPE = 'CLI'
else:
    LOG_APPTYPE = 'Python'

LOG_VERSION = '0.3'
LOG_AUTHOR_AND_LICENSE = '(Author: Sebastian Reategui) (MIT License)'
LOG_STARTUP_LINE = 'mhl-compare (v{}) ({}) {}'.format(
    LOG_VERSION, LOG_APPTYPE, LOG_AUTHOR_AND_LICENSE)

print('--------------')
print(LOG_STARTUP_LINE)


def showDate(dt):
    if not isinstance(dt, datetime):
        # If for some reason, a datetime object isn't passed,
        # just return whatever was given to you
        return dt
    else:
        return dt.strftime(LOG_TIME_FORMAT)


def showSize(numBytes):
    if numBytes < 1024:
        return str(numBytes) + " bytes"
    else:
        return humanize.naturalsize(numBytes, binary=True) + " ({} bytes)".format(numBytes)


def logDetail(*args, **kwargs):
    if LOG_VERBOSE:
        print(*args, **kwargs, end='\n')
    return


def color(text, color, **kwargs):
    # Only print in colour if inside a terminal
    # Don't print colour codes if they go out to a file or other
    if os.isatty(1):
        return colored(text, color, **kwargs)
    else:
        return text


def hashConvertEndian(hashString):
    # Converts any given BE or LE hash, as a string
    # And returns the opposite byte order
    return codecs.encode(codecs.decode(hashString, 'hex')[::-1], 'hex').decode()


class MHL:
    def __init__(self, listObj, filepath):
        self.filepath = filepath
        self.mhlIdentifier = filepath
        self.hashes = {}
        self.duplicates = set()

        self.hashlist_version = listObj['hashlist']['@version']

        if 'creatorinfo' in listObj['hashlist']:
            self.creatorinfo = listObj['hashlist']['creatorinfo']
        else:
            self.creatorinfo = None

        if 'hash' not in listObj['hashlist']:
            # No hash entries listed
            print('There were no files found listed in this MHL file:\n    {}\nAlternatively, there was a formatting issue in the file.'.format(self.filepath))
            sys.exit(0)

        hashTree = listObj['hashlist']['hash']
        if isinstance( hashTree, list ):
            # More than one hash, so it's already in a list format
            list_of_hashes = hashTree
        elif isinstance( hashTree, dict ):
            # Else, it's just one hash, put it inside a list so we can iterate
            list_of_hashes = [ hashTree ]
        else:
            raise Exception("Couldn't find any valid hashes. Here, I was expecting to be given a list of dicts, or a dict itself.")

        HashDuplicateSuffix = 1
        for item in list_of_hashes:
            object = Hash(item, self.mhlIdentifier)

            if object.identifier in self.hashes.keys():
                # Defined already
                self.duplicates.add(object.identifier)
                object.isDuplicate = True
                object.identifier = object.identifier + '_' + str(HashDuplicateSuffix)
                HashDuplicateSuffix += 1

            self.hashes[object.identifier] = object

    def __iter__(self):
        return iter(self.hashes)

    def findHash(self, desired):
        if desired in self.hashes.keys():
            return self.hashes[desired]
        else:
            return HashNonexistent()

    def findHashByAttribute(self, attribute, value):
        for hash in self.hashes.values():
            # Search that object for its attribute
            search = getattr(hash, attribute, False)
            if value == search:
                # If it matches the value, give them back the object to work with
                return hash
            else:
                # Otherwise keep searching
                continue
        # And give them nothing if you legitimately have no search results
        return HashNonexistent()

    def findByOtherHash(self, hashType, hashValue):
        for hash in self.hashes.values():
            if not hash.recordedHashes:
                continue
            for k, v in hash.recordedHashes.items():
                if k == hashType:
                    if v == hashValue:
                        return hash
                    else:
                        # Found the same hash type but it's not a matching value
                        # Keep searching
                        break
                else:
                    continue
        return HashNonexistent()

    def count(self):
        return len(self.hashes)

    def totalSize(self):
        sum = 0
        for h in self.hashes.values():
            sum += h.size
        return showSize(sum)


class Hash(MHL):
    def __init__(self, xmlObject, mhlIdentifier):
        self.parentMHL = mhlIdentifier

        # Debug: print('xml',xmlObject, type(xmlObject))

        if xmlObject['file']:
            self.recordedHashes = {}
            self.isDuplicate = False

            # Path operations
            self.filepath = xmlObject['file']
            path = os.path.split( self.filepath )
            if path[0]:
                # If inside a folder
                self.directory = path[0]
            else:
                # If not, indicate clearly that it is at the root
                self.directory = "/"
            self.filename = path[1]
        else:
            # For some reason, the <hash> entry is missing a <file> attribute
            # Probably should throw an error and let the user know their MHL is malformed
            self.filepath = False
        self.size = int( xmlObject['size'] )
        self.sizeHuman = showSize(self.size)

        xmlObjectKeys = xmlObject.keys()

        # Try do the date parsing, hopefully without errors
        modDate = dateutilParser.parse( xmlObject['lastmodificationdate'] )
        if modDate.tzinfo is None:
            self.lastmodificationdate = modDate.replace(tzinfo=tzutc())
        else:
            self.lastmodificationdate = modDate

        if 'creationdate' in xmlObjectKeys:
            self.creationdate = dateutilParser.parse( xmlObject['creationdate'] )
        if 'hashdate' in xmlObjectKeys:
            self.hashdate = dateutilParser.parse( xmlObject['hashdate'] )

        # Now, we search for acceptable hash types
        # And because our preferred hash is first in the list, it gets assigned as the identifier
        identifierAlreadyFound = False
        for ht in HASH_TYPES_ACCEPTABLE:
            if ht in xmlObjectKeys:
                # Record all acceptable hashes
                self.recordedHashes[ht] = xmlObject[ht].lower()

                if ht == 'xxhash64' and 'xxhash64be' not in self.recordedHashes:
                    # Then the hash is LE
                    # Convert it immediately to xxhash64be
                    BE = hashConvertEndian( xmlObject[ht] )
                    # Make the BE the identifier
                    identifier = BE
                    identifierType = 'xxhash64be'

                    # But also add the BE to recordedHashes
                    self.recordedHashes['xxhash64be'] = BE
                else:
                    identifier = xmlObject[ht].lower()
                    identifierType = ht

                # But also grab an identifier at the same time
                if identifierAlreadyFound:
                    continue
                else:
                    self.identifier = identifier
                    self.identifierType = identifierType
                    identifierAlreadyFound = True

    def __eq__(self, comparison):
        if self.identifier == comparison.identifier:
            return True
        else:
            return False

    def __ne__(self, comparison):
        if self.identifier == comparison.identifier:
            return False
        else:
            return True

    def __hash__(self):
        return hash( self.identifier )

    def __str__(self):
        # By default, print the Identifier
        return self.identifier

    def __lt__(self, other):
        # Aid in sorting by filepath
        return self.filepath < other.filepath


class HashNonexistent:
    def __getattr__(self, attribute):
        return None

    def __setattr__(self, attribute):
        return None


class Comparison:
    def __init__(self, mhlA, mhlB):
        self.A = mhlA
        self.B = mhlB

        setA = { xmlObject for xmlObject in self.A.hashes.values() }
        setB = { xmlObject for xmlObject in self.B.hashes.values() }

        deltaA = setA - setB
        deltaB = setB - setA
        setA_filtered = setA - deltaA
        setB_filtered = setB - deltaB

        self.deltaA = sorted(deltaA)
        self.deltaB = sorted(deltaB)

        common = zip(setA_filtered, setB_filtered)
        self.common = sorted(common)

        # Define the categories of outcomes.
        count_values = [
            'PERFECT',  # Match hash and all filesystem attributes
            'MINOR',  # Match hash but one or more filesystem attributes are different
            'HASH_TYPE_DIFFERENT',  # Hash type is different, cannot be compared
            'HASH_CHANGED',  # Hash is different, indicating a file change
            'MISSING',  # Exists only in one list or the other
            'DUPLICATE',  # When there are multiple files listed with exactly the same hash
            'IMPOSSIBLE'  # For anomalies (like hash the same but size different)
            ]
        # Create a place to store these numbers as we go along.
        self.COUNT = {}
        for v in count_values:
            self.COUNT[v] = 0

    def checkCommon(self):

        for hashA, hashB in self.common:
            beenCounted = False

            diff = DictDiffer( hashA.__dict__, hashB.__dict__ )
            dAdded = diff.added()
            dRemoved = diff.removed()
            dChanged = diff.changed()
            dUnchanged = diff.unchanged()

            if { 'filename', 'directory', 'size', 'lastmodificationdate' }.issubset(dUnchanged):
                # If neither of these variables have changed, then we have a clean match.
                # Report it and move on.
                if not beenCounted:
                    self.COUNT['PERFECT'] += 1
                    beenCounted = True
                continue

            if 'filename' in dChanged:
                if not beenCounted:
                    self.COUNT['MINOR'] += 1
                    beenCounted = True
                logDetail( '  ' + color( hashA.filename, 'green', attrs=LOG_COLOR_BOLD ) )
                logDetail( '      Filename: different (1st):', color( hashA.filename, LOG_COLOR_MHL_A ) )
                logDetail( '                          (2nd):', color( hashB.filename, LOG_COLOR_MHL_B ) )
            else:
                logDetail( '  ' + color( hashA.filename, None, attrs=LOG_COLOR_BOLD ) )
            if 'directory' in dChanged:
                if not beenCounted:
                    self.COUNT['MINOR'] += 1
                    beenCounted = True
                logDetail( '      Path: different (1st):', color( hashA.directory, LOG_COLOR_MHL_A ) )
                logDetail( '                      (2nd):', color( hashB.directory, LOG_COLOR_MHL_B ) )
            else:
                logDetail( '      Path: identical: ' + hashA.directory )

            # Straight up print the hash, don't check it.
            # At this stage, it's not possible for the hash to be different.
            # A check has already been performed for the pair to even be included in this group.
            logDetail( '      Hash: identical: {} ({})'.format( hashA.identifier, hashA.identifierType ) )

            if 'size' in dChanged:
                # It is an anomaly if the size has changed, but not the hash.
                # Report it as impossible, but also print it to the user anyway.
                if not beenCounted:
                    self.COUNT['IMPOSSIBLE'] += 1
                    beenCounted = True
                logDetail( '      Size: different (1st):', color( hashA.sizeHuman, LOG_COLOR_MHL_A ) )
                logDetail( '                      (2nd):', color( hashB.sizeHuman, LOG_COLOR_MHL_B ) )
            else:
                logDetail( '      ' + 'Size: identical: ' + hashA.sizeHuman )

            if 'lastmodificationdate' in dChanged:
                if not beenCounted:
                    self.COUNT['MINOR'] += 1
                    beenCounted = True
                logDetail(
                    '      Modified date: different (1st):',
                    color( hashA.lastmodificationdate, LOG_COLOR_MHL_A )
                 )
                logDetail(
                    '                               (2nd):',
                    color( hashB.lastmodificationdate, LOG_COLOR_MHL_B )
                )

            # Briefly explain to the user what attributes were added/removed
            if len(dAdded) > 0:
                dAddedList = ', '.join( str(i) for i in dAdded )
                logDetail(
                    '      These attributes exist in 1st only:',
                    color(dAddedList, LOG_COLOR_MHL_A )
                )
            if len(dRemoved) > 0:
                dRemovedList = ', '.join( str(i) for i in dRemoved )
                logDetail(
                    '      These attributes exist in 2nd only:',
                    color(dRemovedList, LOG_COLOR_MHL_B )
                )

    def checkDelta(self, letter):
        if letter == 'A':
            delta = self.deltaA
            # Refer to the opposite MHL to access and perform searches on it
            oppositeMHL = self.B

            listLetter = 'A'
            listLabel = '1st'
            listLabelOpposite = '2nd'
            listColor = LOG_COLOR_MHL_A
            listColorOpposite = LOG_COLOR_MHL_B
        elif letter == 'B':
            delta = self.deltaB
            oppositeMHL = self.A

            listLetter = 'B'
            listLabel = '2nd'
            listLabelOpposite = '1st'
            listColor = LOG_COLOR_MHL_B
            listColorOpposite = LOG_COLOR_MHL_A
        else:
            raise Exception("INTERNAL: Couldn't check deltas, none were specified. Specify one")
            return

        # Quickly clean Nonexistent objects out if they exist
        deltaClean = [ h for h in delta if not isinstance(h, HashNonexistent) ]
        deltaClean.sort()

        for hash in deltaClean:

            # Debug
            # print(color('DEBUG >>>', 'yellow'), hash.identifier, color(hash.filename, 'green'))
            # print('rh', hash.recordedHashes)

            foundHashPossible = None
            beenCounted = False  # If this hash has been counted yet

            # Look for a match by other hash
            for otherHashType, otherHashValue in hash.recordedHashes.items():
                if otherHashType == hash.identifierType:
                    pass  # to next hash in the list

                hashPossible = oppositeMHL.findByOtherHash( otherHashType, otherHashValue )
                if isinstance(hashPossible, HashNonexistent):
                    # No result found, move on
                    foundHashPossible = False
                    pass
                else:
                    # Found it
                    # And because we found it by another hash...
                    # Let's update the IDENTIFIER. Risky?
                    hash.identifier = otherHashValue
                    hash.identifierType = otherHashType
                    hashPossible.identifier = otherHashValue
                    hashPossible.identifierType = otherHashType
                    foundHashPossible = True
                    break

            if foundHashPossible is False:
                # Searched but no matches by other hash.
                # Look for a match by filename
                hashPossible = oppositeMHL.findHashByAttribute( 'filename', hash.filename )

                if isinstance(hashPossible, HashNonexistent):
                    # Definitely missing. No other matches by name or hash.
                    foundHashPossible = False
                else:
                    foundHashPossible = True

            if foundHashPossible is True:
                # Compare the hash and the possible hash.
                diff = DictDiffer(hash.__dict__, hashPossible.__dict__)
                dAdded = diff.added()
                dRemoved = diff.removed()
                dUnchanged = diff.unchanged()
                dChanged = diff.changed()

                # First print a filename so everything fits underneath it.
                logDetail( '  ' + color( hash.filename, None, attrs=LOG_COLOR_BOLD ) )

                # Then begin testing.
                if hash.identifierType == hashPossible.identifierType:
                    # Hash type is the same
                    if hash.identifier == hashPossible.identifier:
                        # And so are the hashes

                        # But check if it's a duplicate first
                        if hash.isDuplicate is True:
                            logDetail('      This file is a duplicate. Another file exists in this MHL with the same hash.')
                            if not beenCounted:
                                self.COUNT['DUPLICATE'] += 1
                                beenCounted = True
                            logDetail(
                                '      Hash ({}):'.format(listLabel),
                                colored(hash.identifier + ' ({})'.format(hash.identifierType), listColor)
                            )
                        else:
                            if not beenCounted:
                                self.COUNT['PERFECT'] += 1
                                beenCounted = True
                            logDetail('      Hash: identical.')
                    else:
                        # But the hashes are different. File has changed?
                        if not beenCounted:
                            self.COUNT['HASH_CHANGED'] += 1
                            beenCounted = True
                        logDetail( color('      Hash: These hashes are different from each other. It is likely the files were different between the time the MHLs were generated.', LOG_COLOR_WARNING ) )
                else:
                    # Hash type is not the same. Unlikely to be comparable.
                    if not beenCounted:
                        self.COUNT['HASH_TYPE_DIFFERENT'] += 1
                        beenCounted = True
                    logDetail(color("      Hash: These hashes are of different types. It's not possible to compare them.", LOG_COLOR_INFORMATION))

                if hash.isDuplicate is False:
                    logDetail(
                        '      Hash ({}):'.format(listLabel),
                        color(
                            '{} ({})'.format(hash.identifier, hash.identifierType), listColor
                        )
                    )
                    logDetail(
                        '      Hash ({}):'.format(listLabelOpposite),
                        color(
                            '{} ({})'.format(hashPossible.identifier, hashPossible.identifierType),
                            listColorOpposite
                        )
                    )

                if { 'filename', 'directory', 'size', 'lastmodificationdate' }.issubset(dUnchanged):
                    # If neither of these variables have changed, then we almost have a clean match.
                    # EVEN THOUGH we used a slightly different preferred hash.
                    if not beenCounted:
                        self.COUNT['PERFECT'] += 1
                        beenCounted = True
                    continue
                else:

                    if 'filename' in dChanged:
                        if not beenCounted:
                            self.COUNT['MINOR'] += 1
                            beenCounted = True
                        logDetail( '      Filename: different (1st):', color( hash.filename, LOG_COLOR_MHL_A ) )
                        logDetail( '                          (2nd):', color( hashPossible.filename, LOG_COLOR_MHL_B ) )
                    else:
                        # If the filename is the same, it has already been declared closer to the top.
                        pass

                    if 'directory' in dChanged:
                        if not beenCounted:
                            self.COUNT['MINOR'] += 1
                            beenCounted = True
                        logDetail( '      Path: different (1st):', color( hash.directory, LOG_COLOR_MHL_A ) )
                        logDetail( '                      (2nd):', color( hashPossible.directory, LOG_COLOR_MHL_B ) )
                    else:
                        logDetail( '      Path: identical:', hash.directory )

                    if 'size' in dChanged:
                        # It is an anomaly if the size has changed, but not the hash.
                        # Report it as impossible, but also print it to the user anyway.
                        if not beenCounted:
                            self.COUNT['IMPOSSIBLE'] += 1
                            beenCounted = True
                        logDetail( '      Size: different (1st):', color( hash.sizeHuman, LOG_COLOR_MHL_A ) )
                        logDetail( '                      (2nd):', color( hashPossible.sizeHuman, LOG_COLOR_MHL_B ) )
                    else:
                        logDetail( '      ' + 'Size: identical: ' + hashPossible.sizeHuman )

                    if 'lastmodificationdate' in dChanged:
                        if not beenCounted:
                            self.COUNT['MINOR'] += 1
                            beenCounted = True

                        hModDate = showDate(hash.lastmodificationdate)
                        hPModDate = showDate(hashPossible.lastmodificationdate)

                        logDetail( '      Modified date: different (1st):', color( hModDate, LOG_COLOR_MHL_A ) )
                        logDetail( '                               (2nd):', color( hPModDate, LOG_COLOR_MHL_B ) )

                    # Briefly explain to the user what attributes were added/removed
                    if len(dAdded) > 0:
                        dAddedList = ', '.join( str(i) for i in dAdded )
                        logDetail(
                            '      These attributes exist in 1st only:',
                            color(dAddedList, LOG_COLOR_MHL_A )
                        )
                    if len(dRemoved) > 0:
                        dRemovedList = ', '.join( str(i) for i in dRemoved )
                        logDetail(
                            '      These attributes exist in 2nd only:',
                            color(dRemovedList, LOG_COLOR_MHL_B )
                        )

                    pass

            if foundHashPossible is False:
                # Begin to print the results
                self.COUNT['MISSING'] += 1
                logDetail('  ' + color(hash.filename, listColor, attrs=LOG_COLOR_BOLD))
                logDetail(
                    '  This file only exists in',
                    color(listLabel + ' MHL', listColor) + '.'
                )
                logDetail( '      ' + 'Path:', hash.directory )
                logDetail( '      ' + 'Size:', hash.sizeHuman )
                logDetail( '      ' + 'Hash:', hash.identifier, '({})'.format(hash.identifierType ) )

    def printInfo(self):
        count_files_A = str( self.A.count() ) + " files"
        count_files_B = str( self.B.count() ) + " files"

        print('')
        if LOG_VERBOSE:
            print('Summary:')
        print('1st MHL file:', color(self.A.filepath, LOG_COLOR_MHL_A) )
        print('             ', color(count_files_A, LOG_COLOR_MHL_A) )
        print('             ', color(self.A.totalSize(), LOG_COLOR_MHL_A) )
        print('2nd MHL file:', color(self.B.filepath, LOG_COLOR_MHL_B) )
        print('             ', color(count_files_B, LOG_COLOR_MHL_B) )
        print('             ', color(self.B.totalSize(), LOG_COLOR_MHL_B) )
        return

    def printCount(self):
        outcomes = {
            'PERFECT': {
                'desc': 'matched perfectly'
                },
            'MINOR': {
                'desc': 'matched, but with differences in name, directory or modification date'
                },
            'HASH_TYPE_DIFFERENT': {
                'desc': 'had incomparable hash types and could not be compared',
                'color': LOG_COLOR_INFORMATION
                },
            'HASH_CHANGED': {
                'desc': 'had different hashes. The files were likely different at the time the MHLs were generated',
                'desc_singular': 'had different hashes. The file was likely different at the time the MHLs were generated',
                'color': LOG_COLOR_WARNING
                },
            'MISSING': {
                'desc': 'were present only in one MHL or the other',
                'desc_singular': 'was present only in one MHL or the other'
                },
            'IMPOSSIBLE': {
                'desc': 'anomaly -- MHL was likely modified or something unusual happened'
                },
            'DUPLICATE': {
                'desc': 'were duplicates, as they had the same hash as other files',
                'desc_singular': 'was a duplicate, as it had the same hash as another file'
                },
            'NO_FILES_IN_COMMON': {
                'desc': 'There were no files in common between these two MHLs.'
                }
            }
        for label in outcomes.values():
            # If a singular description ('was' vs. 'were') is not defined, just use the regular description.
            if 'desc_singular' not in label.keys():
                label['desc_singular'] = label['desc']
            # If a color is not defined, don't use any.
            if 'color' not in label.keys():
                label['color'] = None

        print('')
        print('Observations:')

        # Quick check to see if both MHLs are completely and utterly different
        # If all counts are zero, except missing, then there really was nothing in common.
        sumCountsGenuine = sum( self.COUNT.values() ) - self.COUNT['MISSING']
        if not sumCountsGenuine > 0:
            print('    ' + color('There were NO files in common between these two MHL files.', LOG_COLOR_INFORMATION) )
        for category, count in self.COUNT.items():
            line_color = outcomes[category]['color']
            if count == 0:
                # Don't mention empty categories, not relevant
                continue
            elif count == 1:
                count_words = str(count) + " file"
                label_type = 'desc_singular'
            else:
                count_words = str(count) + " files"
                label_type = 'desc'

            print( color(
                "    " + count_words + " " + outcomes[category][label_type],
                line_color)
            )
        if not LOG_VERBOSE:
            print('')
            print('    Run the check again with --info to view details.')

        # print( self.COUNT )
        return


#####


parser = argparse.ArgumentParser()
parser.add_argument( "PATH_A", help="path to list A", type=str)
parser.add_argument( "PATH_B", help="path to list B", type=str)
parser.add_argument(
    "-v", "--verbose", "--info",
    help="gives greater detail on all files affected",
    action="store_true"
)
args = parser.parse_args()


if args.PATH_A and args.PATH_B:
    pass
else:
    raise Exception('Two files need to be included when you run the command')

foundA = os.path.isfile(args.PATH_A)
foundB = os.path.isfile(args.PATH_B)

if foundA is True and foundB is True:
    file_path_A = args.PATH_A
    file_path_B = args.PATH_B
else:
    not_found_string = ''
    if foundA is False:
        not_found_string += "    " + args.PATH_A + "\n"
    if foundB is False:
        not_found_string += "    " + args.PATH_B + "\n"
    raise FileNotFoundError('Could not find these MHL file(s). Check the path for typos?\n' + not_found_string)

if args.verbose:
    LOG_VERBOSE = True


#####


fA = open(file_path_A, 'r')
fB = open(file_path_B, 'r')
PARSE_FILE_A = xmltodict.parse( fA.read(), dict_constructor=dict )
PARSE_FILE_B = xmltodict.parse( fB.read(), dict_constructor=dict )
fA.close()
fB.close()

MHL_FILE_A = MHL(PARSE_FILE_A, file_path_A)
MHL_FILE_B = MHL(PARSE_FILE_B, file_path_B)

compare = Comparison(MHL_FILE_A, MHL_FILE_B)
compare.printInfo()
compare.checkCommon()
compare.checkDelta('A')
compare.checkDelta('B')
compare.printCount()
print('--------------')
