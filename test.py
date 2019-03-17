import xmltodict

f1 = open('example1.mhl', 'r')
f2 = open('example2.mhl', 'r')
f3 = open('example3.mhl', 'r')

example1 = xmltodict.parse( f1.read(), dict_constructor=dict )
example2 = xmltodict.parse( f2.read(), dict_constructor=dict )
example3 = xmltodict.parse( f3.read(), dict_constructor=dict )

db_a = { f['file']: f for f in example1['hashlist']['hash'] }
db_b = { f['file']: f for f in example3['hashlist']['hash'] }

MATCH_COUNT = 0

for bName, bObject in db_b.items():
    if bName in db_a.keys():
        # Found the file successfully
        bHash = bObject['xxhash64be']
        aMatchingObject = db_a[bName]
        aHash = aMatchingObject['xxhash64be']
        aName = aMatchingObject['file']

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
