from dateutil import parser as dateutilParser
import datetime
from dateutil.tz import tzutc
import humanize

aString = "2019-03-17T16:53:30"
bString = "2019-03-17T13:55:10Z"

a = dateutilParser.parse(aString).replace(tzinfo=tzutc())
b = dateutilParser.parse(bString)

"""
print( b - a )

def showTimeDiff(a, b):
    if a > b:
        diff = a - b
    else:
        diff = b - a
    human = humanize.naturaldate(diff)
    # Trim off " ago" because it is wrong
    return human

print( showTimeDiff(a, b) )
"""

import xxhash

x = xxhash.xxh64()
x.update( b'Hey' )
x.hexdigest()

LE = "5a518dbf43939fe0"
BE = "e09f9343bf8d515a"

ba = bytearray.fromhex("AA55CC3301AA55CC330F234567")
s = ''.join(format(x, '02x') for x in ba)

print(ba)
print(s)

"""
Lyotard2:mhl-compare seb$ xxhsum -H1 SEB_3719.JPG
e09f9343bf8d515a  SEB_3719.JPG
Lyotard2:mhl-compare seb$ xxhsum -H1 --little-endian SEB_3719.JPG
5a518dbf43939fe0  SEB_3719.JPG

    <hash>
        <file>SEB_3719.JPG</file>
        <size>6338411</size>
        <xxhash64>  5a518dbf43939fe0 </xxhash64>
        <xxhash64be> e09f9343bf8d515a </xxhash64be>
    </hash>
"""

pass

ePrint = lambda *args, **kwargs: print(*args, **kwargs, end='...\n')

ePrint('hi', 'lol')

def logDetail(*args, **kwargs):
    print(*args, **kwargs, end='...\n')
    return

logDetail('hi', 'lol')
