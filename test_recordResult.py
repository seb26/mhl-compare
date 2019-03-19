from termcolor import colored, cprint
import datetime

class HashNonexistant:
    pass

result = {
    'PERFECT': [],
    'MINOR': [],
    'HASH_TYPE': [],
    'FILE_CHANGED': [],
    'MISSING': [],
    'IMPOSSIBLE': []
}

def recordResult(
        objectA, objectB,
        hashType, hash, filename, directory, size, modifiedDate):

    # Need to have a brief check for structure of tuples and booleans
    # Relying on them a lot here
    # Will make debugging harder

    entry = {
        'objects': ( objectA, objectB ),
        'hashType': hashType,
        'hash': hash,
        'filename': filename,
        'directory': directory,
        'size': size,
        'modifiedDate': modifiedDate
    }
    if isinstance(objectA, HashNonexistant) or isinstance(objectB, HashNonexistant):
        # If either object is nonexistant, then they belong in the MISSING category.
        result['MISSING'].append(entry)
    else:
        # Otherwise, they are potentially genuine matches
        # Continue to evaluate them

        if hashType[0] is True and hash[0] is True:
            # The hash types and the hash match. These are definitely the files
            if size[0] is True:
                if filename[0] is False or directory[0] is False or modifiedDate is False:
                    # At least one of the above attributes was Different
                    result['MINOR'].append(entry)
                else:
                    # All attributes match
                    result['PERFECT'].append(entry)
            else:
                # IMPOSSIBLE
                # How can a hash stay the same, but its size be Different?
                result['IMPOSSIBLE'].append(entry)
                pass
        else:
            if filename[0] is True:
                if size[0] is False or directory[0] is False or modifiedDate is False:
                    result['FILE_CHANGED'].append(entry)
                else:
                    # All attributes match
                    # Summary: The hash types don't match, but everything else does
                    result['HASH_TYPE'].append(entry)
            else:
                # Filename doesn't match
                # Give up, if hashtype, hash and filename don't match, it ain't the same file, as far as I can reasonably judge.
                pass

# Example: best case scenario
hashA = {}
hashB = {}
hashType = (True, "xxhash64be", "xxhash64be")
hash = (True, "09ad6a59a9232f81", "09ad6a59a9232f81")
filename = (False, "SEB_3046.JPG", "SEB_3046.JPG")
directory = (False, "DCIM/100EOS5D/extradirectory", "DCIM/100EOS5D/")
size = (True, 1024, 1024)
modifiedDate = (False, datetime.datetime(2019, 3, 9, 10, 14, 14), datetime.datetime(2019, 3, 9, 10, 14, 14))

recordResult(hashA, hashB, hashType, hash, filename, directory, size, modifiedDate)


# CREATE THE FORMATTING


# PROCESS THE RESULTS

# For PERFECT results, don't process any further, just count them.
RESULTS_COUNT_PERFECT = len( result['PERFECT'] )

# For MINOR results
for e in result['MINOR']:
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
