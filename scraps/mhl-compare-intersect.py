import operator

class Hash:

    def __init__(self, xmlObject, mhlIdentifier):
        self.xmlObject = xmlObject
        self.identifier = xmlObject['identifier']
        self.identifierType = xmlObject['identifierType']
        self.mhl = mhlIdentifier

        self.filename = xmlObject['filename']

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

    def __lt__(self, other):
        # Aid in sorting by filepath
        return self.filename < other.filename

    def __str__(self):
        return self.identifier + '|' + self.filename

filesA = [
    { 'identifier': "abcdef", 'identifierType': 'xxhash64be', 'filename': 'Example.jpg' },
    { 'identifier': "bcdefa", 'identifierType': 'xxhash64be', 'filename': 'Example_2.jpg' },
    { 'identifier': "aafrance", 'identifierType': 'xxhash64be', 'filename': 'image-france.jpg' },
    { 'identifier': "zzitaly", 'identifierType': 'xxhash64be', 'filename': 'image-italy.jpg' },
    { 'identifier': "ccc", 'identifierType': 'xxhash64be', 'filename': 'only_in_A.jpg' }
]

filesB = [
    { 'identifier': "abcdef", 'identifierType': 'xxhash64be', 'filename': 'rExample.jpg' },
    { 'identifier': "bcdefa", 'identifierType': 'xxhash64be', 'filename': 'rExample_2.jpg' },
    { 'identifier': "aafrance", 'identifierType': 'xxhash64be', 'filename': 'image-france.jpg' },
    { 'identifier': "zzitaly", 'identifierType': 'xxhash64be', 'filename': 'image-italy.jpg' },
    { 'identifier': "ddd", 'identifierType': 'xxhash64be', 'filename': 'only_in_B.jpg' }
]

setA = { Hash(xmlObject, 'MHL-A') for xmlObject in filesA }
setB = { Hash(xmlObject, 'MHL-B') for xmlObject in filesB }

deltaA = setA - setB
deltaB = setB - setA
setA_filtered = setA - deltaA
setB_filtered = setB - deltaB

print('setA', setA)
print('setB', setB)
print('deltaA', deltaA)
print('deltaB', deltaB)
print('setA_filtered', setA_filtered)
print('setB_filtered', setB_filtered)

print('sort')

common = zip(setA_filtered, setB_filtered)

print('>new', new)
for i in new:
    print(i[0], i[1])


    # STILL NEED TO:
    # Zip common entries together so that you get both A objects and B objects later
