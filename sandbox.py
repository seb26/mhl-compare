from dateutil import parser as dateutilParser
import datetime
import pytz

a = "2019-03-17T16:53:30"
b = "2019-03-17T16:53:30Z"

aParsed = dateutilParser.parse(a)
bParsed = dateutilParser.parse(b)

aware = aParsed.replace(tzinfo=pytz.UTC)

print(aParsed)
print(bParsed)

print(aware)
