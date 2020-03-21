#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (c) Sebastian Reategui 2019, all rights reserved
# MIT License

import sys
import os
import argparse
import codecs
import re
import itertools
from datetime import datetime

import xmltodict
import humanize
from dateutil.tz import tzutc
from dateutil import parser as dateutilParser
from termcolor import colored
from dictdiffer import DictDiffer

# Program defaults
HASH_TYPE_PREFERRED = 'xxhash64be'
HASH_TYPES_ACCEPTABLE = [ 'xxhash64be', 'xxhash64', 'xxhash', 'md5', 'sha1' ]

LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_SIZE_FORMAT = 'decimal' # By default, 1000 bytes is 1 KB
LOG_VERBOSE = False  # By default, don't show detail about which files changed
LOG_SHOW_DATES = False # By default, don't report on modification dates, hashdates, or creationdates
LIST_OF_DATE_ATTRIBUTES = [ 'lastmodificationdate', 'creationdate', 'hashdate' ]

LOG_COLOR_MHL_A = 'green'
LOG_COLOR_MHL_B = 'yellow'
LOG_COLOR_WARNING = 'red'
LOG_COLOR_INFORMATION = 'cyan'
LOG_COLOR_BOLD = [ 'bold' ]

if getattr( sys, 'frozen', False ):
    LOG_APPTYPE = 'CLI'
else:
    LOG_APPTYPE = 'Python'

LOG_VERSION = '0.4'
LOG_AUTHOR_AND_LICENSE = '(Author: Sebastian Reategui) (MIT License) (2020-03-21)'
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


def humanSize(numBytes, showBytes=False):
    if numBytes < 1024:
        return str(numBytes) + " bytes"
    else:
        if LOG_SIZE_FORMAT == 'binary':
            humanize_binary_setting = True
        else:
            humanize_binary_setting = False

        display_human_size = humanize.naturalsize(
            numBytes,
            binary=humanize_binary_setting,
            format="%.2f" # 2 decimal places
        )

        # If yes, display (1024 bytes) in brackets next to the human amount.
        if showBytes:
            return display_human_size + ' ({} bytes)'.format(str(numBytes))
        else:
            return display_human_size


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
    def __init__(self, filepath):
        self.filepath = filepath
        self.mhlIdentifier = filepath
        self.hashes = {}
        self.duplicates = set()

        PATTERN_XXHASHLIST = re.compile('^([0-9a-fA-F]{16})\s{2}(.*)$')

        # (1) Try to parse it as XML
        try:
            with open(self.filepath, 'r') as f:
                listObj = xmltodict.parse( f.read(), dict_constructor=dict )
                self.originType = 'MHL'
        except:
            # Syntax error from xmldict
            # (2) Try parsing this as an .xxhash simple list of sums
            with open(filepath, 'r') as f:
                lines = f.readlines()
                f.close()

                fauxMHL = {
                    '_ORIGIN': os.path.basename(filepath),
                    'hashlist': {
                        'hash': []
                    }
                }
                for line in lines:
                    match = PATTERN_XXHASHLIST.match(line)
                    if match:
                        hash = match[1]
                        hashFilepath = match[2]

                        # Create a faux MHL line, imitating XML already parsed as a dict
                        fauxMHL_hash = {
                            'file': hashFilepath,
                            'size': None,
                            'xxhash64be': hash,
                        }
                        fauxMHL['hashlist']['hash'].append(fauxMHL_hash)
                listObj = fauxMHL
                self.originType = 'HASHLIST_PLAIN'

        if '@version' in listObj['hashlist']:
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
            if h.sizeDefined:
                sum += h.size
        if self.originType == 'HASHLIST_PLAIN':
            # Then there is no record of sizes
            return None
        else:
            return sum


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


        xmlObjectKeys = xmlObject.keys()

        if 'size' in xmlObjectKeys:
            if xmlObject['size']:
                self.sizeDefined = True
                self.size = int( xmlObject['size'] )
                self.sizeHuman = humanSize(self.size)
            else:
                # It's "None", unspecified
                self.sizeDefined = False
                self.size = None
                self.sizeHuman = 'Not specified'

        if 'lastmodificationdate' in xmlObjectKeys:
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

            if { 'filename', 'directory', 'size' }.issubset(dUnchanged):
                # If neither of these variables have changed, then we have a perfect match.
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
                # First, check if the Size is simply "Not specified"
                if hashA.sizeDefined == False or hashB.sizeDefined == False:
                    self.COUNT['PERFECT'] += 1
                    beenCounted = True

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
                if LOG_SHOW_DATES:
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
                else:
                    # Don't count date changes unless user wants it (LOG_SHOW_DATES is true)
                    pass

            # Briefly explain to the user what attributes were added/removed
            if LOG_SHOW_DATES == False:
                dAddedFiltered = [ i for i in dAdded if i not in LIST_OF_DATE_ATTRIBUTES ]
                dRemovedFiltered = [ i for i in dRemoved if i not in LIST_OF_DATE_ATTRIBUTES ]
            else:
                dAddedFiltered = dAdded
                dRemovedFiltered = dRemoved

            if len(dAddedFiltered) > 0:
                dAddedString = ', '.join( str(i) for i in dAddedFiltered )
                logDetail(
                    '      These attributes exist in 1st only:',
                    color(dAddedString, LOG_COLOR_MHL_A )
                )
            if len(dRemovedFiltered) > 0:
                dRemovedString = ', '.join( str(i) for i in dRemovedFiltered )
                logDetail(
                    '      These attributes exist in 2nd only:',
                    color(dRemovedString, LOG_COLOR_MHL_B )
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
            # E.g., if XXHASH and MD5 present, search by MD5
            for otherHashType, otherHashValue in hash.recordedHashes.items():
                if otherHashType == hash.identifierType:
                    pass  # Skip the hash type we are already using

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

                if { 'filename', 'directory', 'size' }.issubset(dUnchanged):
                    # If neither of these variables have changed, then we have a perfect match.
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
                        # First, check if the Size is simply "Not specified"
                        # This is not an anomaly if so.
                        if hash.sizeDefined == False:
                            # If we have come this far (hash match, name, directory) but size can't be compared
                            # That is as good as we are gonna get.
                            self.COUNT['PERFECT'] += 1
                            beenCounted = True
                        else:
                            # It is an anomaly if the size has changed while the hash has not.
                            # Report it as impossible, but also print it to the user anyway.
                            if not beenCounted:
                                self.COUNT['IMPOSSIBLE'] += 1
                                beenCounted = True
                            logDetail( '      Size: different (1st):', color( hash.sizeHuman, LOG_COLOR_MHL_A ) )
                            logDetail( '                      (2nd):', color( hashPossible.sizeHuman, LOG_COLOR_MHL_B ) )
                    else:
                        logDetail( '      ' + 'Size: identical: ' + hashPossible.sizeHuman )

                    if 'lastmodificationdate' in dChanged:
                        if LOG_SHOW_DATES:
                            if not beenCounted:
                                self.COUNT['MINOR'] += 1
                                beenCounted = True

                            hModDate = showDate(hash.lastmodificationdate)
                            hPModDate = showDate(hashPossible.lastmodificationdate)

                            logDetail( '      Modified date: different (1st):', color( hModDate, LOG_COLOR_MHL_A ) )
                            logDetail( '                               (2nd):', color( hPModDate, LOG_COLOR_MHL_B ) )
                        else:
                            # Don't count date changes unless user wants it (LOG_SHOW_DATES is true)
                            pass

                    # Briefly explain to the user what attributes were added/removed
                    if LOG_SHOW_DATES == False:
                        dAddedFiltered = [ i for i in dAdded if i not in LIST_OF_DATE_ATTRIBUTES ]
                        dRemovedFiltered = [ i for i in dRemoved if i not in LIST_OF_DATE_ATTRIBUTES ]
                    else:
                        dAddedFiltered = dAdded
                        dRemovedFiltered = dRemoved

                    if len(dAddedFiltered) > 0:
                        dAddedString = ', '.join( str(i) for i in dAddedFiltered )
                        logDetail(
                            '      These attributes exist in 1st only:',
                            color(dAddedString, LOG_COLOR_MHL_A )
                        )
                    if len(dRemovedFiltered) > 0:
                        dRemovedString = ', '.join( str(i) for i in dRemovedFiltered )
                        logDetail(
                            '      These attributes exist in 2nd only:',
                            color(dRemovedString, LOG_COLOR_MHL_B )
                        )

                    pass

            else:
                # Else if foundHashPossible was False.
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



        if self.A.originType == 'HASHLIST_PLAIN':
            displayed_size_A = 'Size not specified (file is a simple list of checksums)'
        else:
            displayed_size_A = humanSize(self.A.totalSize(), showBytes=True)
        if self.B.originType == 'HASHLIST_PLAIN':
            displayed_size_B = 'Size not specified (file is a simple list of checksums)'
        else:
            displayed_size_B = humanSize(self.B.totalSize(), showBytes=True)

        print('')
        if LOG_VERBOSE:
            print('Summary:')
        print('1st MHL file:', color(self.A.filepath, LOG_COLOR_MHL_A) )
        print('             ', color(count_files_A, LOG_COLOR_MHL_A) )
        print('             ', color(displayed_size_A, LOG_COLOR_MHL_A) )
        print('2nd MHL file:', color(self.B.filepath, LOG_COLOR_MHL_B) )
        print('             ', color(count_files_B, LOG_COLOR_MHL_B) )
        print('             ', color(displayed_size_B, LOG_COLOR_MHL_B) )
        return

    def printCount(self):
        outcomes = {
            'PERFECT': {
                'desc': 'matched perfectly'
                },
            'MINOR': {
                'desc': 'matched (but with differences in name or directory)'
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
parser.add_argument( "FILEPATH", nargs='+', help="Path to the first file")
parser.add_argument(
    "-v", "--verbose", "--info",
    help="gives greater detail on all files affected",
    action="store_true"
)
parser.add_argument(
    "-b", "--binary",
    help="Shows sizes in binary format, appropriate for Windows (1024 bytes = 1 KiB)",
    action="store_true"
)
parser.add_argument(
    "-d", "--dates",
    help="Report on differences in modification date, creation date or hash date",
    action="store_true"
)
args = parser.parse_args()


if args.verbose:
    LOG_VERBOSE = True
if args.binary:
    LOG_SIZE_FORMAT = 'binary'
if args.dates:
    LOG_SHOW_DATES = True


if len(args.FILEPATH) == 1:
    # Print a summary of just this file
    filepath = args.FILEPATH[0]
    if not os.path.isfile(filepath):
        raise FileNotFoundError('\n\nCould not find this MHL file. Check the path for typos?\n{}'.format(filepath))

    MHL = MHL(filepath)

    def keyfunc(x):
        return x.directory

    MHL_items = sorted(MHL.hashes.values())
    for dir, items in itertools.groupby(MHL_items, keyfunc):
        print(color(dir, 'green', attrs=LOG_COLOR_BOLD) + ':')
        for item in items:
            print_filename = '  > ' + item.filename
            print_log_detail_to_add = '\t{} {}'.format(
                color('({})'.format(item.identifier), 'yellow'),
                item.sizeHuman
            )
            if LOG_VERBOSE == True:
                print(print_filename + print_log_detail_to_add)
            else:
                print(print_filename)

            # Show date information, if user requests
            if LOG_SHOW_DATES:
                for attrib in LIST_OF_DATE_ATTRIBUTES:
                    if hasattr(item, attrib):
                        logDetail( '        {:<20}:'.format(attrib), getattr(item, attrib))
        # After each directory, line break
        print()
    print('--------------')
    # Summarise the MHL
    print('{} files, {} in total'.format(
        MHL.count(),
        humanSize( MHL.totalSize(), showBytes=True )
        )
    )


elif len(args.FILEPATH) == 2:
    # Our main comparison will take place with 2 files.
    # Check the paths exist first.
    for filepath in args.FILEPATH:
        if not os.path.isfile(filepath):
            raise FileNotFoundError('\n\nCould not find this MHL file. Check the path for typos?\n{}'.format(filepath))
    # Then define our A and B files.
    filepath_A = args.FILEPATH[0]
    filepath_B = args.FILEPATH[1]

    MHL_FILE_A = MHL(filepath_A)
    MHL_FILE_B = MHL(filepath_B)

    compare = Comparison(MHL_FILE_A, MHL_FILE_B)
    compare.printInfo()
    compare.checkCommon()
    compare.checkDelta('A')
    compare.checkDelta('B')
    compare.printCount()

else:
    raise Exception('\n\nYou have specified {} files. Only two at a time are supported for comparison.\nDouble check you have not included any erroneous spaces in the file path.'.format(len(args.FILEPATH)))


#####

print('--------------')
