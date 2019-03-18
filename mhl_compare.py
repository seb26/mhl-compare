import os
from datetime import datetime
import pprint
import xmltodict

pp = pprint.PrettyPrinter(indent=1)

FILE_A = 'example1.mhl'
FILE_B = 'example2.mhl'
parsed_files = {}

with open(FILE_A, 'r') as fA:
    parsed_files['a'] = xmltodict.parse( fA.read(), dict_constructor=dict )
with open(FILE_B, 'r') as fB:
    parsed_files['b'] = xmltodict.parse( fB.read(), dict_constructor=dict )

db = {
    'a': {},
    'b': {}
}

# Program defaults
MHL_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
HASH_TYPE_PREFERRED = 'xxhash64be'
HASH_TYPES_ACCEPTABLE = [ 'xxhash64be', 'xxhash64', 'xxhash', 'md5', 'sha1' ]

class Hash:
    def __init__(self, hObj):
        if hObj['file']:
            self.filepath = hObj['file']
            self.filename = os.path.split( self.filepath )[1]
            self.hashes = {}
        else:
            # For some reason, the <hash> entry is missing a <file> attribute
            # Probably should throw an error and let the user know their MHL is malformed
            self.filepath = False
        try:
            # Try do the rest, hopefully without errors
            self.size = hObj['size']
            self.lastmodificationdate = hObj['lastmodificationdate']
        except:
            print('Your MHL is malformed, go home')
        # Now, test for the hash type
        if hObj[HASH_TYPE_PREFERRED]:
            self.identifier = hObj[HASH_TYPE_PREFERRED]
            self.identifierType = HASH_TYPE_PREFERRED
        for h in HASH_TYPES_ACCEPTABLE:
            if h in hObj.keys():
                # Use the next best acceptable hash as the Identiifer
                if not self.identifier:
                    self.identifier = hObj[h]
                    self.identifierType = h
                # Then otherwise categorise all other available hashes
                self.hashes['h'] = hObj[h]

class List:
    def __init__(self, filepath, listObj):
        self.filepath = filepath
        self.hashlist_version =

# Set up a dictionary entry for each hash
# For every a, b, c entry listed as a parsed dict
for letter, parsed in parsed_files.items():

    # Find each object in that parsed dict
    for object in parsed['hashlist']['hash']:
        # Designate its filename and filepath
        filepath = object['file']
        filename = os.path.split( filepath )[1]
        try:
            hash = object[HASH_TYPE_DEFAULT]
        except:
            print('EXCEPTION')
            print(object)
            continue

        # Then add it to the database
        # { 'Z.jpg': { 'filepath': 'Path/Z.jpg', 'object': <hash> in Dict format }
        # According to an identifier. Today, I've selected hash.
        identifier = hash
        db[letter][identifier] = {
            'filepath': filepath,
            'filename': filename,
            'object': object
            }

COUNT_HASHES_A = len(db['a'])
COUNT_HASHES_B = len(db['b'])
COUNT_HASHES_DIFF = abs( COUNT_HASHES_A - COUNT_HASHES_B )
COUNT_MATCH = 0
COUNT_MATCH_WARNING = 0
COUNT_FAIL = 0

DIRTY_HASHES = []

# Debugging
# pp.pprint(db)

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
