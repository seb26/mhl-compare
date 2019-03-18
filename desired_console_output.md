~ mhl_compare.py example1.mhl example2.hml
## SUMMARY
example1.mhl
  Items: 15
  Total size:

example2.mhl
  Items: 23
  Total size:

## COMMON - MATCH
Matching files:
  Total: 15 (65.1% of all files)

Files with differences:
  Total: 3

## COMMON - MINOR DIFFERENCE
  Files with different modification times:
    DCIM/100EOS5D/SEB_3046.JPG (19649bc55e32b83f)
    Difference: 5 hours
    However, hash is identical.

## COMMON - MINOR DIFFERENCE
  Files with different directories:
    DCIM/100EOS5D/SEB_3046.JPG (19649bc55e32b83f)
    First directory: DCIM/100EOS5D/SEB_3046.JPG
    Second directory: EOS_DIGITAL/DCIM/100EOS5D/SEB_3046.JPG
    However, hash is identical.

## DELTA
  Files with different hashes:
    DCIM/100EOS5D/SEB_3046.JPG
    Size is identical: 12498349 bytes
    First MHL has 19649bc55e32b83f (xxhash64be)
    Second MHL has ab68a3c61484d311 (xxhash64)

    DCIM/100EOS5D/SEB_3046.JPG
    First MHL size is 12498349 bytes
    Second MHL size is 13000000 bytes
    Difference: 501651 bytes.

    First MHL has 19649bc55e32b83f (xxhash64be)
    Second MHL has ab68a3c61484d311 (xxhash64)

    First MHL has 2019-03-17 08:32:51
    Second MHL has 2019-03-17 09:00:00
    Difference: 27 minutes 9 seconds

## DELTA - CONFIRMED MISSING
  Files only in one list or the other:
    First MHL (example1.mhl)
    System Volume Information/IndexerVolumeGuid
    Size: 76 bytes
    Hash: fcaaa32dad594213 (xxhash64be)
    Other hashes: 1DC2AEF7309F1550E5FD5771D98F537D (md5)

    Second MHL (example2.mhl)
    Random.log
    Size: 76 bytes
    Hash: fcaaa32dad594213 (xxhash64be)
    Other hashes: 1DC2AEF7309F1550E5FD5771D98F537D (md5)
