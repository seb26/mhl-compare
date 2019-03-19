#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (c) Sebastian Reategui 2019, all rights reserved
# MIT License

import os
from datetime import datetime
import argparse

import xmltodict
from dateutil.parser import *
from termcolor import colored
from lib.dictdiffer import DictDiffer

# Program defaults
MHL_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
HASH_TYPE_PREFERRED = 'xxhash64be'
HASH_TYPES_ACCEPTABLE = [ 'xxhash64be', 'xxhash64', 'xxhash', 'md5', 'sha1' ]


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
            return HashNonexistant()

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
        return HashNonexistant()

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
        return HashNonexistant()

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
            self.filepath = hObj['file']
            path = os.path.split( self.filepath )
            self.directory = path[0]
            self.filename = path[1]
            self.recordedHashes = {}
            self.duplicate = False
        else:
            # For some reason, the <hash> entry is missing a <file> attribute
            # Probably should throw an error and let the user know their MHL is malformed
            self.filepath = False
        self.size = int( hObj['size'] )

        hObjKeys = hObj.keys()

        # Try do the date parsing, hopefully without errors
        self.lastmodificationdate = parse( hObj['lastmodificationdate'] )

        if 'creationdate' in hObjKeys:
            self.creationdate = parse( hObj['creationdate'] )
        if 'hashdate' in hObjKeys:
            self.hashdate = parse( hObj['hashdate'] )

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

class HashNonexistant:
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

        self.COUNT_MATCH_ALL = 0
        self.COUNT_MINOR = 0
        self.COUNT_HASH_TYPE_DIFFERENT = 0
        self.COUNT_HASH_CHANGED = 0
        self.COUNT_MISSING = 0
        self.COUNT_IMPOSSIBLE = 0

    """
    def recordResult(self,
            hashType, hash, filename, directory, size, modifiedDate):

        # Need to have a brief check for structure of tuples and booleans
        # Relying on them a lot here
        # Will make debugging harder

        entry = {
            'hashType': hashType,
            'hash': hash,
            'filename': filename,
            'directory': directory,
            'size': size,
            'modifiedDate': modifiedDate
        }
        if isinstance(objectA, HashNonexistant) or isinstance(objectB, HashNonexistant):
            # If either object is nonexistant, then they belong in the MISSING category.
            self.results['MISSING'].append(entry)
        else:
            # Otherwise, they are potentially genuine matches
            # Continue to evaluate them

            if hashType[0] is True and hash[0] is True:
                # The hash types and the hash match. These are definitely the files
                if size[0] is True:
                    if filename[0] is False or directory[0] is False or modifiedDate is False:
                        # At least one of the above attributes was Different
                        self.results['MINOR'].append(entry)
                    else:
                        # All attributes match
                        self.results['PERFECT'].append(entry)
                else:
                    # IMPOSSIBLE
                    # How can a hash stay the same, but its size be Different?
                    result['IMPOSSIBLE'].append(entry)
                    pass
            else:
                if filename[0] is True:
                    if size[0] is False or directory[0] is False or modifiedDate is False:
                        self.results['FILE_CHANGED'].append(entry)
                    else:
                        # All attributes match
                        # Summary: The hash types don't match, but everything else does
                        self.results['HASH_TYPE'].append(entry)
                else:
                    # Filename doesn't match
                    # Give up, if hashtype, hash and filename don't match, it ain't the same file, as far as I can reasonably judge.
                    pass

    recordResult(hashType, hash, filename, directory, size, modifiedDate)


    # For PERFECT results, don't process any further, just count them.
    RESULTS_COUNT_PERFECT = len( result['PERFECT'] )

    # For MINOR results
    for e in self.results['MINOR']:
        if e['filename'][0] == False:
            print( '   ', e['filename'][1] )
            print( '      Different: Filename (1st MHL):', colored( e['filename'][1], 'green' ) )
            print( '      Different: Filename (2nd MHL):', colored( e['filename'][2], 'yellow' ) )
        else:
            print( '   ', e['filename'][1] )
        if e['hash'][0] == False:
            print( '      Different: Hash (1st MHL):', colored( e['hash'][1], 'green' ),
                '({})'.format( e['hashType'][1] ) )
            print( '      Different: Hash (1st MHL):', colored( e['hash'][2], 'yellow' ),
                '({})'.format( e['hashType'][2] ) )
        else:
            print( '      Identical: Hash:', e['hash'][1], '({})'.format( e['hashType'][1] ) )
        if e['directory'][0] == False:
            print( '      Different: Directory (1st MHL):', colored( e['directory'][1], 'green' ) )
            print( '      Different: Directory (2nd MHL):', colored( e['directory'][2], 'yellow' ) )
        else:
            print( '     ', e['directory'][1] )
        if e['modifiedDate'][0] == False:
            print( '      Different: Modified date (1st MHL):', colored( e['modifiedDate'][1], 'green' ) )
            print( '      Different: Modified date (2nd MHL):', colored( e['modifiedDate'][2], 'yellow' ) )
        else:
            print( '     ', e['modifiedDate'][1] )
    """

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
            dChangedOnly = diff.changed()
            dChanged = diff.new_or_changed()
            dUnchanged = diff.unchanged()

            if 'filename' in dChanged:
                self.COUNT_MINOR += 1
                print( '  ' + colored( hashA.filename, 'green' ) )
                print( '    Filename: different (1st):', colored( hashA.filename, 'green' ) )
                print( '                        (2nd):', colored( hashB.filename, 'yellow' ) )
            else:
                print( '  ' + hashA.filename )
            if 'directory' in dChanged:
                self.COUNT_MINOR += 1
                print( '      Directory: different (1st):', colored( hashA.directory, 'green' ) )
                print( '                           (2nd):', colored( hashB.directory, 'yellow' ) )
            else:
                print( '      Directory: identical (' + hashA.directory + ')' )

            # Straight up print the hash, don't check it.
            # At this stage, it's not possible for the hash to be different.
            # A check has already been performed for the pair to even be included in this group.
            print( '      Hash: identical ({}: {})'.format( hashA.identifierType, hashA.identifier ) )

            if 'size' in dChanged:
                # It is an anomaly if the size has changed, but not the hash.
                # Report it as impossible, but also print it to the user anyway.
                self.IMPOSSIBLE += 1
                print( '      Size: different (1st):', colored( str(hashA.size), 'green' ) )
                print( '                      (2nd):', colored( str(hashB.size), 'yellow' ) )
            else:
                print( '      ' + 'Size: identical (' + str(hashA.size), 'bytes)' )

            if 'lastmodificationdate' in dChanged:
                self.COUNT_MINOR += 1
                print( '      Modified date: different (1st):', colored( hashA.lastmodificationdate, 'green' ) )
                print( '                               (2nd):', colored( hashB.lastmodificationdate, 'yellow' ) )
            else:
                print( '      ' + hashA.lastmodificationdate )

            # Briefly explain to the user what attributes were added/removed
            if len(dAdded) > 0:
                dAddedList = ', '.join( str(i) for i in dAdded )
                print( '      These attributes exist in 1st only:',
                    colored(dAddedList, 'green' ) )
            if len(dRemoved) > 0:
                dRemovedList = ', '.join( str(i) for i in dRemoved )
                print( '      These attributes exist in 2nd only:',
                colored(dRemovedList, 'yellow' ) )

    def checkDelta(self, letter):

        letter = letter.upper()
        if not letter == 'A' or letter == 'B':
            raise Exception('This delta function expects a string that is A or B')

        delta = getattr(self, 'delta' + letter, False)
        if delta == False:
            raise exception('Delta object was just False, expected a list, delta results improperly reported?')

        # Clean out the HashNonexistant objects
        deltaClean = [ h for h in delta if not isinstance(h, HashNonexistant) ]

        # Refer to the opposite MHL to access and perform searches on it
        if letter == 'A':
            oppositeMHL = self.B
        elif letter == 'B':
            oppositeMHL = self.A

        for hash in deltaClean:
            # Use "hash.parentMHL"

            # Look for a match by filename
            hashPossible = oppositeMHL.findHashByAttribute( 'filename', hash.filename )
            if isinstance(hashPossible, HashNonexistant):
                # Couldn't find a match by filename
                # Let's try a match by other hash
                for otherHash, otherHashValue in hash.recordedHashes.items():
                    if otherHash == hash.identifierType:
                        pass
                        # No use checking the other hashes if one of them is the identifier
                        # We've already tested that to get this far
                    else:
                        hashPossible = oppositeMHL.findByOtherHash( otherHash, otherHashValue )
                        if isinstance(hashPossible, HashNonexistant):
                            print('    Definitely missing. No other matches by name or hash.')
                            pass

                # Couldn't find a match by other hash
                # Let's try one more by size AND directory
            if isinstance(hashPossible, Hash):
                print('    Found one possible match')
                print('    ', hashPossible.__dict__)
                if hash.filename == hashPossible.filename:
                    print('    The filename is the same')
                else:
                    print('    However the filename is different')
                if hash.filepath == hashPossible.filepath:
                    print('    The filepaths are the same')
                else:
                    print('    However the filepaths are different')
                if hash.size == hashPossible.size:
                    print('    The size is the same')
                else:
                    print('    However the size is different')
                print('    Other hashes:', hashPossible.recordedHashes)
            else:
                # This means couldn't find a match by filename, nor by other hash
                continue


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
# compare.checkDelta('A')
print('#################### checkDelta B')
# compare.checkDelta('B')
