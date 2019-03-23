import defusedxml as xml

handler = xml.sax.handler

f = open('samples/d01.mhl', 'r')
parsed = sax.parse(f, handler)

for item in parsed.iter():
    print(item, type(item))
