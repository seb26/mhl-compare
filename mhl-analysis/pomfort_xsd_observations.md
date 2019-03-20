My observations of the XSD format provided by Pomfort.

My words written in dot points, and code blocks show parts of the schema that I don't quite understand.

## Types
* MD5, restricted to hexBinary, length: 16
* SHA1, restricted to hexBinary, length 20
* xxhash, restricted to integer, total digits 10
* xxhash64, restricted to hexBinary, length 8
* Version:
```
<xs:simpleType name="versionType">
	<xs:restriction base="xs:decimal">
		<xs:fractionDigits value="1"/>
		<xs:minInclusive value="0"/>
	</xs:restriction>
</xs:simpleType>
```

## Simple elements
* `file` is a string
* Size is a positive integer
* All dates are dateTime (note: no apparent requirement for timezone information)
* Most MHL metadata, like name, computer name, program generator, are strings

## Attributes
```
<!-- definition of attributes -->
<xs:attribute name="version" type="versionType" />
<xs:attribute name="referencehhashlist" type="xs:boolean" />
```

* `referencehhashlist` is used to make reference to another MHL file, to allow for recursive searching and verifying of other directories as described by other MHL files (see Pomfort's [January 2012 proposal document, page 7](https://mediahashlist.org/wp-content/uploads/2012/01/Media-Hash-File-Format-Proposal-v1_3.pdf)).

## Complex elements
* `<md5>`
* `<sha1>`
* `<xxhash>`
* `<xxhash64>` -- A comment describes this as "deprecated, little endian xxhash64"
* `<xxhash64be>`
* A null element, string, only used for "file size verification"
* `<creatorinfo>` -- which packages the metadata about who created the MHL file
