#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (c) Sebastian Reategui 2019, all rights reserved
# MIT License

import os
from datetime import datetime
from operator import attrgetter
import argparse

import xmltodict
from dateutil import parser as dateutilParser
import pytz
from termcolor import colored
from lib.dictdiffer import DictDiffer

# Program defaults
HASH_TYPE_PREFERRED = 'xxhash64be'
HASH_TYPES_ACCEPTABLE = [ 'xxhash64be', 'xxhash64', 'xxhash', 'md5', 'sha1' ]

LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

LOG_COLOR_MHL_A = 'green'
LOG_COLOR_MHL_B = 'yellow'
LOG_COLOR_WARNING = 'red'
LOG_COLOR_INFORMATION = 'cyan'

def showDate(dt):
    if not isinstance(dt, datetime):
        # If for some reason, a datetime object isn't passed,
        # just return whatever was given to you
        return dt
    else:
        return dt.strftime(LOG_TIME_FORMAT)

class MHL:
    def __init__(self, listObj, filepath):
        self.filepath = filepath
        self.identifier = filepath
        self.hashlist_version = listObj['hashlist']['@version']
        self.creatorinfo = listObj['hashlist']['creatorinfo']

        # Add the hashes
        self.hashes = {}
        HASH_DUPLICATE_SUFFIX = 1
        for h in listObj['hashlist']['hash']:
            objHash = Hash(h)
            objHash.parentMHL = self.identifier
            objHashIdentifier = objHash.identifier

            if objHashIdentifier in self.hashes.keys():
                # If this is defined already, it means there's a duplicate
                # Append some digits to its name
                objHashIdentifier = objHashIdentifier + '_' + str(HASH_DUPLICATE_SUFFIX)
                HASH_DUPLICATE_SUFFIX += 1
                objHash.duplicate = True
                self.hashes[objHashIdentifier] = objHash
            else:
                # Store them in the dict by their identifier
                self.hashes[objHashIdentifier] = objHash

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

    def getIdentifiers(self):
        all = [ v.identifier for v in self.hashes.values() ]
        return sorted(all)

    def getSize(self):
        sum = 0
        for h in self.hashes:
            sum += h.size
        return sum


class Hash(MHL):
    def __init__(self, hObj):
        self.parentMHL = False

        if hObj['file']:
            self.recordedHashes = {}
            self.duplicate = False

            # Path operations
            self.filepath = hObj['file']
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
        self.size = int( hObj['size'] )

        hObjKeys = hObj.keys()

        # Try do the date parsing, hopefully without errors
        modDate = dateutilParser.parse( hObj['lastmodificationdate'] )
        if modDate.tzinfo is None:
            self.lastmodificationdate = modDate.replace(tzinfo=pytz.UTC)
        else:
            self.lastmodificationdate = modDate

        if 'creationdate' in hObjKeys:
            self.creationdate = dateutilParser.parse( hObj['creationdate'] )
        if 'hashdate' in hObjKeys:
            self.hashdate = dateutilParser.parse( hObj['hashdate'] )

        # Now, we search for acceptable hash types
        # And because our preferred hash is first in the list, it gets assigned as the identifier
        identifierAlreadyFound = False
        for ht in HASH_TYPES_ACCEPTABLE:
            if ht in hObjKeys:
                # Record all acceptable hashes
                self.recordedHashes[ht] = hObj[ht]

                # But also grab an identifier at the same time
                if identifierAlreadyFound:
                    continue
                else:
                    self.identifier = hObj[ht]
                    self.identifierType = ht
                    identifierAlreadyFound = True

    def __str__(self):
        # By default, print the Identifier
        return self.identifier

class HashNonexistent:
    def __getattr__(self, attribute):
        return None
    def __setattr__(self, attribute):
        return None


class Comparison:
    def __init__(self, listA, listB):
        self.A = listA
        self.B = listB
        self.deltaA = set()
        self.deltaB = set()
        self.common = set()

        # Define the categories of outcomes.
        count_values = [
            'PERFECT', # Match hash and all filesystem attributes
            'MINOR', # Match hash but one or more filesystem attributes are different
            'HASH_TYPE_DIFFERENT', # Hash type is different, cannot be compared
            'HASH_CHANGED', # Hash is different, indicating a file change
            'MISSING', # Exists only in one list or the other
            'IMPOSSIBLE' # For anomalies (like hash the same but size different)
            ]
        # Create a place to store these numbers as we go along.
        self.COUNT = {}
        for v in count_values:
            self.COUNT[v] = 0

    def createComparisonLists(self):
        # Get the identifiers just as strings
        setA = set( self.A.getIdentifiers() )
        setB = set( self.B.getIdentifiers() )
        # Then compare them and generate lists
        # Also get a set of all the hashes in common between the two
        deltaA = setA - setB
        deltaB = setB - setA
        common = setA.union(setB) - deltaA - deltaB

        self.deltaA = [ self.A.findHash(i) for i in deltaA ]
        self.deltaB = [ self.B.findHash(i) for i in deltaA ]
        self.common = [ ( self.A.findHash(i), self.B.findHash(i) ) for i in common ]
        # Remember, self.common is a list of TUPLES because it contains objects from both lists.

        return True

    def checkCommon(self):

        for hashA, hashB in self.common:

            diff = DictDiffer( hashA.__dict__, hashB.__dict__ )
            dAdded = diff.added()
            dRemoved = diff.removed()
            dChanged = diff.changed()
            dUnchanged = diff.unchanged()

            # Debugging
            """
            print(dAdded)
            print(dRemoved)
            print(dChangedOnly)
            print(dChanged)
            print(dUnchanged)
            """

            if { 'filename', 'directory', 'size', 'lastmodificationdate' }.issubset(dUnchanged):
                # If neither of these variables have changed, then we have a clean match.
                # Report it and move on.
                self.COUNT['PERFECT'] += 1
                continue

            if 'filename' in dChanged:
                self.COUNT['MINOR'] += 1
                print( '  ' + colored( hashA.filename, 'green' ) )
                print( '    Filename: different (1st):', colored( hashA.filename, LOG_COLOR_MHL_A ) )
                print( '                        (2nd):', colored( hashB.filename, LOG_COLOR_MHL_B ) )
            else:
                print( '  ' + hashA.filename )
            if 'directory' in dChanged:
                self.COUNT['MINOR'] += 1
                print( '      Path: different (1st):', colored( hashA.directory, LOG_COLOR_MHL_A ) )
                print( '                      (2nd):', colored( hashB.directory, LOG_COLOR_MHL_B ) )
            else:
                print( '      Path: identical: ' + hashA.directory )

            # Straight up print the hash, don't check it.
            # At this stage, it's not possible for the hash to be different.
            # A check has already been performed for the pair to even be included in this group.
            print( '      Hash: identical: {} ({})'.format( hashA.identifier, hashA.identifierType ) )

            if 'size' in dChanged:
                # It is an anomaly if the size has changed, but not the hash.
                # Report it as impossible, but also print it to the user anyway.
                self.COUNT['IMPOSSIBLE'] += 1
                print( '      Size: different (1st):', colored( str(hashA.size), LOG_COLOR_MHL_A ) )
                print( '                      (2nd):', colored( str(hashB.size), LOG_COLOR_MHL_B ) )
            else:
                print( '      ' + 'Size: identical: ' + str(hashA.size), 'bytes' )

            if 'lastmodificationdate' in dChanged:

                self.COUNT['MINOR'] += 1
                print( '      Modified date: different (1st):', colored( showDate(hashA.lastmodificationdate), LOG_COLOR_MHL_A ) )
                print( '                               (2nd):', colored( showDate(hashB.lastmodificationdate), LOG_COLOR_MHL_B ) )

            # Briefly explain to the user what attributes were added/removed
            if len(dAdded) > 0:
                dAddedList = ', '.join( str(i) for i in dAdded )
                print( '      These attributes exist in 1st only:',
                    colored(dAddedList, LOG_COLOR_MHL_A ) )
            if len(dRemoved) > 0:
                dRemovedList = ', '.join( str(i) for i in dRemoved )
                print( '      These attributes exist in 2nd only:',
                colored(dRemovedList, LOG_COLOR_MHL_B ) )

    def checkDelta(self, listA=False, listB=False):
        if listA:
            delta = self.deltaA
            # Refer to the opposite MHL to access and perform searches on it
            oppositeMHL = self.B

            listLetter = 'A'
            listLabel = '1st'
            listLabelOpposite = '2nd'
            listColor = LOG_COLOR_MHL_A
            listColorOpposite = LOG_COLOR_MHL_B
        elif listB:
            delta = self.deltaB
            oppositeMHL = self.A

            listLetter = 'B'
            listLabel = '2nd'
            listLabelOpposite = '1st'
            listColor = LOG_COLOR_MHL_B
            listColorOpposite = LOG_COLOR_MHL_A
        else:
            print("INTERNAL: Couldn't check deltas, none were specified. Specify one")
            return

        # Quickly clean Nonexistent objects out if they exist
        deltaClean = [ h for h in delta if not isinstance(h,HashNonexistent) ]
        # Sort by filepath
        deltaClean.sort(key=attrgetter('filepath'))

        for hash in deltaClean:

            print(colored('DEBUG >>>', 'yellow'), hash.identifier, colored(hash.filename, 'green'))
            # print('rh', hash.recordedHashes)

            foundHashPossible = None
            beenCounted = False # If this hash has been counted yet

            # Look for a match by other hash
            for otherHashType, otherHashValue in hash.recordedHashes.items():
                if otherHashType == hash.identifierType:
                    pass # to next hash in the list

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

            if foundHashPossible == False:
                # Searched but no matches by other hash.
                # Look for a match by filename
                hashPossible = oppositeMHL.findHashByAttribute( 'filename', hash.filename )

                if isinstance(hashPossible, HashNonexistent):
                    # Definitely missing. No other matches by name or hash.
                    foundHashPossible = False
                else:
                    foundHashPossible = True

            if foundHashPossible == True:
                # Compare the hash and the possible hash.
                diff = DictDiffer(hash.__dict__, hashPossible.__dict__)
                dAdded = diff.added()
                dRemoved = diff.removed()
                dUnchanged = diff.unchanged()
                dChanged = diff.changed()

                # First print a filename so everything fits underneath it.
                print( '  ' + hash.filename )

                # Then begin testing.
                if hash.identifierType == hashPossible.identifierType:
                    # Hash type is the same
                    if hash.identifier == hashPossible.identifier:
                        # And so are the hashes
                        if not beenCounted:
                            self.COUNT['PERFECT'] += 1
                            beenCounted = True
                        print('      Hash: identical.')
                    else:
                        # But the hashes are different. File has changed?
                        if not beenCounted:
                            self.COUNT['HASH_CHANGED'] += 1
                            beenCounted = True
                        print( colored('      Hash: These hashes are different from each other. It is likely the file has changed.', LOG_COLOR_WARNING ) )
                else:
                    # Hash type is not the same,
                    if not beenCounted:
                        self.COUNT['HASH_TYPE_DIFFERENT'] += 1
                        beenCounted = True
                    print(colored("      Hash: These hashes are of different types. It's not possible to compare them.", LOG_COLOR_INFORMATION))
                print('      Hash ({}):'.format(listLabel),
                colored('{} ({})'.format(hash.identifier, hash.identifierType), listColor)
                )
                print('      Hash ({}):'.format(listLabelOpposite),
                colored('{} ({})'.format(hashPossible.identifier, hashPossible.identifierType), listColorOpposite)
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
                        print( '    Filename: different (1st):', colored( hash.filename, LOG_COLOR_MHL_A ) )
                        print( '                        (2nd):', colored( hashPossible.filename, LOG_COLOR_MHL_B ) )
                    else:
                        # If the filename is the same, it has already been declared closer to the top.
                        pass

                    if 'directory' in dChanged:
                        self.COUNT['MINOR'] += 1
                        print( '      Path: different (1st):', colored( hash.directory, LOG_COLOR_MHL_A ) )
                        print( '                      (2nd):', colored( hashPossible.directory, LOG_COLOR_MHL_B ) )
                    else:
                        print( '      Path: identical:', hash.directory )


                    if 'size' in dChanged:
                        # It is an anomaly if the size has changed, but not the hash.
                        # Report it as impossible, but also print it to the user anyway.
                        self.COUNT['IMPOSSIBLE'] += 1
                        print( '      Size: different (1st):', colored( str(hash.size), LOG_COLOR_MHL_A ) )
                        print( '                      (2nd):', colored( str(hashPossible.size), LOG_COLOR_MHL_B ) )
                    else:
                        print( '      ' + 'Size: identical: ' + str(hashPossible.size), 'bytes' )

                    if 'lastmodificationdate' in dChanged:
                        self.COUNT['MINOR'] += 1
                        print( '      Modified date: different (1st):', colored( showDate(hash.lastmodificationdate), LOG_COLOR_MHL_A ) )
                        print( '                               (2nd):', colored( showDate(hashPossible.lastmodificationdate), LOG_COLOR_MHL_B ) )

                    # Briefly explain to the user what attributes were added/removed
                    if len(dAdded) > 0:
                        dAddedList = ', '.join( str(i) for i in dAdded )
                        print( '      These attributes exist in 1st only:',
                            colored(dAddedList, LOG_COLOR_MHL_A ) )
                    if len(dRemoved) > 0:
                        dRemovedList = ', '.join( str(i) for i in dRemoved )
                        print( '      These attributes exist in 2nd only:',
                        colored(dRemovedList, LOG_COLOR_MHL_B ) )

                    pass

            if foundHashPossible == False:
                # Begin to print the results
                self.COUNT['MISSING'] += 1
                print('This file only exists in',
                    colored(listLabel + ' MHL', listColor) + ':' )
                print('  ' + colored(hash.filename, listColor))
                print( '      ' + 'Path:', hash.directory )
                print( '      ' + 'Size:', str(hash.size), 'bytes' )
                print( '      ' + 'Hash:', hash.identifier, '({})'.format(hash.identifierType ) )

    def printCount(self):
        print( self.COUNT )
        return


# Arguments
parser = argparse.ArgumentParser()
parser.add_argument( "FILE_A_PATH", help="path to list A", type=str)
parser.add_argument( "FILE_B_PATH", help="path to list B", type=str)
args = parser.parse_args()

f = open(args.FILE_A_PATH, 'r')
PARSE_FILE_A = xmltodict.parse( f.read(), dict_constructor=dict )
f.close()

f = open(args.FILE_B_PATH, 'r')
PARSE_FILE_B = xmltodict.parse( f.read(), dict_constructor=dict )
f.close()

MHL_FILE_A = MHL(PARSE_FILE_A, args.FILE_A_PATH)
MHL_FILE_B = MHL(PARSE_FILE_B, args.FILE_B_PATH)

compare = Comparison(MHL_FILE_A, MHL_FILE_B)
compare.createComparisonLists()
print('#################### checkCommon')
compare.checkCommon()
print('#################### checkDelta A')
compare.checkDelta(listA=True)
print('#################### checkDelta B')
compare.checkDelta(listB=True)
compare.printCount()
