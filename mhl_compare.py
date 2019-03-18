#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (c) Sebastian Reategui 2019, all rights reserved
# MIT License

import os
from datetime import datetime
import argparse

import xmltodict
from dateutil.parser import *

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

    def gatherDelta(self):
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

            # Iterate over all attributes (size, date) of the hash
            for a, b in zip( hashA.__dict__.items(), hashB.__dict__.items() ):
                # Example: a = ('identifier', '18fc3d609a8a3469')
                # a[0] is the attribute
                # a[1] is the value of the attribute

                if a[1] == b[1]:
                    # In terms of this attribute, HashA and HashB match exactly
                    # Pass, this is expected
                    # print('match', a[0], a[1], b[1])
                    pass
                else:
                    # In terms of this attribute, HashA and HashB have different values
                    # This may mean different filename, different date, or just simply additional hashes
                    # Let's probe to find out

                    if a[0] == 'lastmodificationdate':
                        # TODO: TIME DIFFERENCE BETWEEN MODIFICATION DATES
                        # Make it human time?
                        print('DIFFERENT: modification time:', a[1] - b[1])
                    elif a[0] == 'size':
                        print('DIFFERENT: size:', a[1], b[1], 'Difference', abs(a[1] - b[1]) )
                    elif a[0] == 'recordedHashes':
                        if hashA.identifierType == hashB.identifierType:
                            # They have the same hash
                            # Therefore, a difference in recordedHashes is not worth reporting
                            pass
                        else:
                            print('These files have different hash types')
                            print(hashA.identifierType, hashB.identifierType, a[1], b[1])
                    elif a[0] == 'directory':
                        print('DIFFERENT: directory:', a[1], b[1])

    def checkDeltas(self):

        # Clean out the HashNonexistant objects
        deltaCleanA = [ h for h in self.deltaA if not isinstance(h, HashNonexistant) ]
        deltaCleanB = [ h for h in self.deltaB if not isinstance(h, HashNonexistant) ]

        # Assign them a letter so we can refer to it later
        for hash in deltaCleanA:
            hash.parentMHLLetter = 'A'
        for hash in deltaCleanB:
            hash.parentMHLLetter = 'B'

        for hash in deltaCleanA + deltaCleanB:
            print('This hash exists only in:', hash.parentMHL)
            print('    ', hash.filepath, '(' + str(hash.size) + ' bytes)' )
            print('    Hashes: ', hash.recordedHashes)
            print('    Investigate a little bit...')

            if hash.parentMHLLetter == 'A':
                oppositeMHL = self.B
            else:
                oppositeMHL = self.A

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
parser.add_argument( "FILE_A_PATH", help = "path to list A", type = str)
parser.add_argument( "FILE_B_PATH", help = "path to list B", type = str)
args = parser.parse_args()

f = open(args.FILE_A_PATH, 'r')
PARSE_FILE_A = xmltodict.parse( f.read(), dict_constructor = dict )
f.close()

f = open(args.FILE_B_PATH, 'r')
PARSE_FILE_B = xmltodict.parse( f.read(), dict_constructor = dict )
f.close()

MHL_FILE_A = MHL(PARSE_FILE_A, args.FILE_A_PATH)
MHL_FILE_B = MHL(PARSE_FILE_B, args.FILE_B_PATH)

compare = Comparison(MHL_FILE_A, MHL_FILE_B)
compare.gatherDelta()
compare.checkCommon()
compare.checkDeltas()
