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
    Hash: Identical.

    Modification time: First MHL: 2019-03-17 08:32:51
    Modification time: Second MHL: 2019-03-17 09:00:00 (+27 minutes 9 seconds)

## COMMON - MINOR DIFFERENCE
  Files with different filenames:
    DCIM/100EOS5D/SEB_3046.JPG (19649bc55e32b83f)
    Hash: Identical.

    Filename: First MHL: SEB_3046.JPG
    Filename: Second MHL: SEB_3046_V2.JPG


## COMMON - MINOR DIFFERENCE
  Files with different directories:
    DCIM/100EOS5D/SEB_3046.JPG (19649bc55e32b83f)
    Hash: Identical.
    Filename: Identical.

    Directory: First MHL: DCIM/100EOS5D/
    Directory: Second MHL: EOS_DIGITAL/DCIM/100EOS5D/

## DELTA - FILES WITH DIFFERENT HASHES
  Files with different hashes:
### example 1 - filename SAME, directory SAME, hash WRONGTYPE, size SAME, modtime SAME
    DCIM/100EOS5D/SEB_3046.JPG
    Hash: First MHL: xxhash64be (19649bc55e32b83f)
    Hash: Second MHL: xxhash64 (ab68a3c61484d311)
    Hash: These two hash types cannot be compared. Unable to tell if file is same or different.
      [directory identical - do not mention]

    Size: Identical, 12498349 bytes
      [modification time identical - do not mention]

### example 2 - filename SAME, directory DIFFERENT, hash WRONGTYPE, size SAME, modtime SAME
    DCIM/100EOS5D/SEB_3046.JPG
    Filename: Identical.

    Hash: First MHL: xxhash64be (19649bc55e32b83f)
    Hash: Second MHL: xxhash64 (ab68a3c61484d311)
    Hash: These two hash types cannot be compared. Unable to tell if file is same or different.

    Directory: First MHL: DCIM/100EOS5D/
    Directory: Second MHL: EOS_DIGITAL/DCIM/100EOS5D/

    Size: Identical. 12498349 bytes

      [modification time identical - do not mention]

### example 3 - filename SAME, directory SAME, hash RIGHT TYPE, size SAME, modtime SAME
    DCIM/100EOS5D/SEB_3046.JPG
    Filename: Identical.

    Hash: First MHL:   19649bc55e32b83f (xxhash64)
    Hash: Second MHL:  ab68a3c61484d311 (xxhash64)
    Hash: These hashes are different.

      [directory identical - do not mention]

    Size: First MHL: 12498349 bytes (-501651 bytes)
    Size: Second MHL: 13000000 bytes

    Modification time: First MHL: 2019-03-17 08:32:51
    Modification time: Second MHL: 2019-03-17 09:00:00 (+27 minutes 9 seconds)

### example 4 - filename SAME, directory SAME, hash WRONGTYPE, size SAME, modtime SAME
    DCIM/100EOS5D/SEB_3046.JPG
    Filename: Identical.

    Hash: First MHL: xxhash64be (19649bc55e32b83f)
    Hash: Second MHL: xxhash64 (ab68a3c61484d311)
    Hash: These two hash types cannot be compared. Unable to tell if file is same or different.

    Directory: First MHL: DCIM/100EOS5D/
    Directory: Second MHL: EOS_DIGITAL/DCIM/100EOS5D/

    Size: First MHL: 12498349 bytes (-501651 bytes)
    Size: Second MHL: 13000000 bytes

    Modification time: First MHL: 2019-03-17 08:32:51
    Modification time: Second MHL: 2019-03-17 09:00:00 (+27 minutes 9 seconds)

### examples -- combinations that cannot exist
###          -- filename DIFFERENT, directory SAME, hash WRONGTYPE
    This is because if HASH is wrongtype and filename is different, there is no other criteria with which to successfully search for possible matches.
    If a file has a wrong hashtype, there is already little reason to compare them.
    If a file has a wrong hashtype and a non-matching filename, it's probably because the files are OBJECTIVELY DIFFERENT and not related to each other.
    Size is not a relevant comparison because it's possible for multiple files to exist in the same directory with the same size (metadata files for example.)

## DELTA - CONFIRMED MISSING - hash NO MATCH, filename NO MATCH
  Files only in one list or the other:
    First MHL (example1.mhl)
    System Volume Information/IndexerVolumeGuid
    Size: 76 bytes
    Hash: fcaaa32dad594213 (xxhash64be)
    Other hashes: 1DC2AEF7309F1550E5FD5771D98F537D (md5)

    Second MHL (example2.mhl)
    Random.log
    Size: 100 bytes
    Hash: fcaaa32dad594213 (xxhash64be)
    Other hashes: 1DC2AEF7309F1550E5FD5771D98F537D (md5)
