import os
from datetime import datetime
import xmltodict

# Debugging only
import pprint
pp = pprint.PrettyPrinter(indent=1)

# File paths for testing
FILE_A_PATH = 'example3.mhl'
FILE_B_PATH = 'example1.mhl'

# Program defaults
MHL_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
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
        return None

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
        return None

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
        try:
            # Try do the rest, hopefully without errors
            self.size = int( hObj['size'] )
            self.lastmodificationdate = datetime.strptime( hObj['lastmodificationdate'], MHL_TIME_FORMAT )
        except:
            print('Your MHL is malformed, go home')

        # Now, we search for acceptable hash types
        # And because our preferred hash is first in the list, it gets assigned as the identifier
        identifierAlreadyFound = False
        for ht in HASH_TYPES_ACCEPTABLE:
            if ht in hObj.keys():
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

        for hash in self.deltaA + self.deltaB:
            if isinstance(hash, HashNonexistant):
                continue
            else:
                print('test parent', hash.__mro__   )
                print('This file exists only in:', hash.parentMHL)
                print('    ', hash.filepath, '(' + str(hash.size) + ' bytes)' )
                print('    ', hash.recordedHashes)
                print('    Investigate a little bit...')

                if hash.filename:
                    searchResultA = self.A.findHashByAttribute( 'filename', hash.filename )
                    searchResultB = self.B.findHashByAttribute( 'filename', hash.filename )




f = open(FILE_A_PATH, 'r')
PARSE_FILE_A = xmltodict.parse( f.read(), dict_constructor = dict )
f.close()

f = open(FILE_B_PATH, 'r')
PARSE_FILE_B = xmltodict.parse( f.read(), dict_constructor = dict )
f.close()

MHL_FILE_A = MHL(PARSE_FILE_A, FILE_A_PATH)
MHL_FILE_B = MHL(PARSE_FILE_B, FILE_B_PATH)

COUNT_MATCH = 0
COUNT_MATCH_WARNING = 0
COUNT_FAIL = 0

# print(MHL_FILE_A.getIdentifiers())
# print(MHL_FILE_B.getIdentifiers())

compare = Comparison(MHL_FILE_A, MHL_FILE_B)
compare.gatherDelta()
# compare.checkCommon()
compare.checkDeltas()

# query = MHL_FILE_A.findHashByAttribute( 'md5', 'D32310BF7F58D57BA6F1D37DEEBB2C21' )
# print(query)

# y = MHL_FILE_A.findByOtherHash( 'md5', 'D32310BF7F58D57BA6F1D37DEEBB2C21' )
# print(y.size)

"""
for bIdentifier, b in MHL_FILE_B.hashes.items():
    if bIdentifier in MHL_FILE_A.getIdentifiers():
        continue
    else:
        print('FAIL', b.identifier, b.filename)



###### DEPRECATED
for bIdentifier, bItem in db['b'].items():
    bFilepath = bItem['filepath']
    bFilename = bItem['filename']
    bObject = bItem['object']
    bHash = bObject[HASH_TYPE_SELECTED]
    aOtherHashes = []
    bOtherHashes = []

    # First, search for the file via the identifier
    if bIdentifier in db['a'].keys():
        # Found the file successfully, via the identifier
        aMatching = db['a'][bIdentifier]
        aMatchingObject = aMatching['object']
        aFilepath = aMatching['filepath']
        aFilename = aMatching['filename']
        aHash = aMatchingObject[HASH_TYPE_SELECTED]

        # It's a match, because the hash matched.
        # Notwithstanding the probability of two different files having the same hash.

        # But also check the filepath and filename briefly
        if bFilepath == aFilepath:
            COUNT_MATCH += 1
        else:
            COUNT_MATCH_WARNING += 1
            print('MATCH: This file matched but its filepath is different:', '[' + aFilepath + '] versus [' + bFilepath + ']')

    else:
        # Couldn't find it via the hash

        # Begin to search the entire tree
        # If we can find the same path, it means the file is present
        # in both MHLs, but has a different hash
        for aIdentifier, aValue in db['a'].items():
            aFilename = aValue['filename']
            aFilepath = aValue['filepath']
            aObject = aValue['object']

            # Try compare the filepath
            if bFilepath == aFilepath:
                COUNT_FAIL += 1
                print(
                    'FAIL: This file has a different hash:',
                    aFilepath,
                    '(A:', aIdentifier + '; B:', bIdentifier +
                    '; Hash Type:', HASH_TYPE_SELECTED + ')'
                )
                # Add the dirty hash to a list
                DIRTY_HASHES = [ aIdentifier, bIdentifier ]

                # Present some values for the viewer to examine
                #   Modification date
                aModTime = datetime.strptime( aObject['lastmodificationdate'], MHL_TIME_FORMAT )
                bModTime = datetime.strptime( bObject['lastmodificationdate'], MHL_TIME_FORMAT )
                modTimeDiff = abs(bModTime - aModTime)
                print( '      ' +
                    'Time difference of', modTimeDiff,
                    '; A Modification:', aObject['lastmodificationdate'] +
                    '; B Modification:', bObject['lastmodificationdate']
                )

                #   Size in bytes
                aSize = int(aObject['size'])
                sizeDifference = abs( aSize - int(bObject['size'])  )
                if sizeDifference > 0:
                    print('      ' + 'Size difference:', sizeDifference )
                else:
                    print('      ' + 'Size is the same. Total bytes:', aSize )

                #   Other hashes
                #   Briefly check for the presence of any other hash types
                for hashType in HASH_TYPES_ACCEPTABLE[1:]:
                    if hashType in aObject.keys():
                        print('      Another hash present in List A:', hashType, aObject[hashType] )
                    if hashType in bObject.keys():
                        print('      Another hash present in list B:', hashType, bObject[hashType] )
                break
            else:
                # Move onto next search result, this one didn't match
                continue
            print(bFilepath, 'however filepath didntmatch', aFilepath)

# After comparing

# See what was missing
hashes_missing_a = [ x for x in db['a'].keys() - db['b'].keys() if x not in DIRTY_HASHES ]
hashes_missing_b = [ x for x in db['b'].keys() - db['a'].keys() if x not in DIRTY_HASHES ]
if hashes_missing_a or hashes_missing_b:
    print('# MISSING FILES -----------')
if hashes_missing_a:
    print('These files were mentioned in List A, but were absent in List B')
    hashes_missing_a.sort()
    for h in hashes_missing_a:
        hh = db['a'][h]['object']
        print( '      ', hh['file'], '(' + hh['size'], 'bytes)' )
if hashes_missing_b:
    print('These files were mentioned in List B, but were absent in List A')
    hashes_missing_b.sort()
    for h in hashes_missing_b:
        hh = db['b'][h]['object']
        print( '      ', hh['file'], '(' + hh['size'], 'bytes)' )

print('# END -----------')
print('Total files from A:                ', COUNT_HASHES_A)
print('Total files from B:                ', COUNT_HASHES_B)
print('Difference:                        ', COUNT_HASHES_DIFF)
print('')
print('Positive matches:                  ', COUNT_MATCH)
print('Positive matches but with warnings:', COUNT_MATCH_WARNING)
print('Total failures:                    ', COUNT_FAIL)
"""
