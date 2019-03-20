import xxhash

x = xxhash.xxh64()
x.update( b'Hey' )
x.hexdigest()

be = "653d2888be59715a"
le = "5a7159be88283d65"

import codecs

def hashConvertEndian(hashString):
    return codecs.encode(codecs.decode(hashString, 'hex')[::-1], 'hex').decode()

print( 'be to le', hashConvertEndian(be) )
print( 'le to be', hashConvertEndian(le) )

"""
aa = codecs.decode(le, 'hex')[::-1]
d = codecs.encode(aa, 'hex').decode()

print(d)
"""


"""
  SEB_3720.CR2
      Hash: These hashes are of different types. It's not possible to compare them.
      Hash (1st): 653d2888be59715a (xxhash64be)
      Hash (2nd): 5a7159be88283d65 (xxhash64)



1st:36 35 33 64 32 38 38 38 62 65 35 39 37 31 35 61
2nd:35 61 37 31 35 39 62 65 38 38 32 38 33 64 36 35
"""
