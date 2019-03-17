import os
import pprint
import xmltodict

pp = pprint.PrettyPrinter(indent=1)

example1 = open('example1.mhl', 'r')
example2 = open('example2.mhl', 'r')
example3 = open('example3.mhl', 'r')

files = {
    'a': xmltodict.parse( example1.read(), dict_constructor=dict ),
    'b': xmltodict.parse( example3.read(), dict_constructor=dict )
}

db = {
    'a': {},
    'b': {}
}

# Set up a dictionary entry for each hash

# For every a, b, c entry listed as a parsed dict
for letter, parsed in files.items():

    # Find each object in that parsed dict
    for object in parsed['hashlist']['hash']:
        # Designate its filename and filepath
        filepath = object['file']
        filename = os.path.split( filepath )[1]

        # Then add it to the database
        # { 'Z.jpg': { 'filepath': 'Path/Z.jpg', 'object': <hash> in Dict format }
        # According to an identifier. Today, I've selected filepath.
        identifier = filepath
        db[letter][identifier] = {
            'filepath': filepath,
            'filename': filename,
            'object': object
            }

MATCH_COUNT = 0

for bName, bItem in db['b'].items():
    if bName in db['a'].keys():
        # Found the file successfully
        aMatching = db['a'][bName]
        aMatchingObject = aMatching['object']
        aName = aMatching['filename']
        aHash = aMatchingObject['xxhash64be']

        bObject = bItem['object']
        bHash = bObject['xxhash64be']

        # Directly compare the hashes
        HASHES_MATCH = True if aHash == bHash else False
        if HASHES_MATCH:
            MATCH_COUNT += 1
        else:
            print( HASHES_MATCH, aName, '(' + aHash + ')' )
            print( '     ', bName, '(' + bHash + ')' )
    else:
        # Couldn't find it at all
        print('FAIL: Not present:', bName)


print('# END -----------')
print('Total positive matches:', MATCH_COUNT)
