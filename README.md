# mhl-compare
Given two [Media Hash List (MHL) files](https://mediahashlist.org/), this **command-line utility for macOS** will compare them and show differences in hash, filenames, directory structure, size and more, of the media files described within them.

Useful when comparing two copies of media files that are intended to be the same, but they originate from other sources or were copied at different times.

`mhl-compare` does not read or compare physical media files against a MHL file, it only compares MHL files to each other.

---

### Download

**Download version 0.4** (latest):
  * https://github.com/seb26/mhl-compare/releases/download/v0.4/mhl-compare-v0.4.zip

### Installation

**Method via Finder**
* Extract the zip (double-click it)
* **Copy** the binary file `mhl-compare` to clipboard
* In Finder toolbar, choose Go > Go  to Folder... or *Shift + Cmd + G*
* Type: `/usr/local/bin`
* Inside this folder /usr/local/bin, **paste** the file you just copied
* Done. To use, scroll down to section on Usage.

**Method via Terminal**

* Extract the zip
* Then run:

```
cp ~/Downloads/mhl-compare-v0.4/mhl-compare /usr/local/bin/
```

That completes the installation, now you can run `mhl-compare` from anywhere in a Terminal.

----

### Usage: compare two files

In a Terminal window, run:

```
mhl-compare first.mhl second.mhl
```

Alternatively, you can type just `mhl-compare`, and from Finder, drag the files onto the Terminal window directly.

This will insert the full file path(s) for you, saving you from typing them manually.

Then hit enter and check out the result.

### Usage: summarise just one file

```
mhl-compare file.mhl
```

A summary of the files listed in the MHL will be output, including a total number and a total size. They will appear grouped by directory.

Useful if you just want to review the contents of an MHL rapidly, without tediously navigating the XML manually with your eyes or Ctrl+F searching it with difficulty.

By default, only the files' names are shown in a long list. Run this with options (below) to see more details, such as hash, size, or date information.

### Options
* `-v, --verbose, --info`
  * Shows detailed, file-by-file description of the differences in each file.
  * Default without this option: a short summary of the similarity is shown including number of clips in common. There is no per-file detail.

* `-b, --binary`
  * Sizes are specified in binary format (i.e. 1 KiB = 1,024 bytes) which is relevant on Windows platform.
  * Default without this option: sizes are shown in decimal format (1 KB = 1,000 bytes), relevant for macOS.

* `-d, --dates`
  * Shows date-related attributes contained within a file, if available.
  * These may include a file's creation date (`creationdate`), modified date (`lastmodificationdate`) or date of hashing (`hashdate`).
  * Default without this option: Dates are not shown at all.
---

### Example scenario
You use a MHL-generating program to copy video files stored on an SD card, to a folder in your local workspace. You give the SD card to a colleague and they make a similar copy with an MHL-generating program to an LTFS tape drive on their system. Later, your colleague reports an issue opening one of the video files, but you are unable to replicate the issue on your local copy.

Both you and your colleague have the capacity to run a MHL-verifying tool to re-read all the files and compare their validity *today*. However, it may also be useful to determine whether the two copies were identical, back at *the time of copy*. `mhl-compare` can read both MHL files and point out if their hashes were the same at the time the MHL files were generated. It will also indicate any other differences in file structure, naming or modification dates, that are highly likely to occur across copying software and operating systems.

The benefit is that you and your colleague would be able to see if you legitimately had identical copies of the media set, at the time you made them. It may reveal that some files were missing from either set, incorrectly copied, modified by something, placed in different folders, or any other myriad of file system anomalies. These kinds of differences are hard to observe when running a singular MHL-verifying application (like [MHLTool](https://mediahashlist.org/mhl-tool/), [Sealverify](https://pomfort.com/sealverify/), [Checkpoint](https://hedge.video/checkpoint)).

Additionally, MHL files are small (typically much less than 500 KB) and contain just XML, so it may be more practical to compare *them* instead when working with large media collections, where it is too time-consuming to read and verify the media files themselves, or they are stored in other physical locations.

### Example scenario 2
You have a single MHL file and wish to understand which files are listed within it. Double-clicking or opening the file in any other program will prompt you to verify the contents, you don't wish to do so, you only want to know the basics first.

You can run mhl-compare on just this one file, and see a list of files contained within the MHL and other attributes about them. mhl-compare will spit out the number of files and also the total size. Learning the size will permit you to immediately perform a size-based comparison against the size of the folder of files itself.

*Without mhl-compare*: while it is possible to open an MHL file in any text editor and view the list of files described within and Ctrl + F to find relevant files, it is not laid out in a very accessible or easy-to-read fashion. It is also completely impractical to quickly figure out the total size of the files, since the size is only shown individually, and you would have to use a calculator or some other automated means to combine all the individual sizes into a single sum.

---

### Compatibility

#### Files it can open
Any MHL file that follows [the standard XML format for MHL files](https://mediahashlist.org/mhl-specification/)
  * This includes MHL files from: Silverstack, ShotPut Pro, YoYotta, Hedge, TeraCopy, and others.

Also, simple lists of checksums are supported as well, such as `.md5` or `.xxhash` files, which are typically in a one-line-per-file structure like below:
```
09ad6a59a9232f81  file.txt
```

#### Running the program itself (the regular download)
Only runs on macOS. Tested only on macOS 10.14.3. It is likely to run successfully on older versions though, it's not a very complex program.

#### Running the program as a Python script
Originally written on Python 3.7.2 on macOS 10.14.3, and developed today on Python 3.7.4 with macOS 10.14.6. Because it has been written with the Python 3 branch, it is not compatible with Python 2, and cannot be run on macOS without the additional installation of Python 3.

I understand this is a huge caveat since it would be great to install and use mhl-compare quickly on foreign machines, which you might not have admin access to or the time required to install additional software like Python 3.

##### Dependencies
Dependency libraries: [`xmltodict`](https://github.com/martinblech/xmltodict), [`dateutil`](https://dateutil.readthedocs.io/en/stable/), [`humanize`](https://pypi.org/project/humanize/), [`termcolor`](https://pypi.org/project/termcolor/), [`dictdiffer`](https://github.com/hughdbrown/dictdiffer).

#### On other operating systems

Has not been tested on Windows or Linux, but Python is generally pretty functional across OSs, so it is likely to work fine.


---

### Development

#### Changelog
Described on GitHub in Releases. See: https://github.com/seb26/mhl-compare/releases

#### Goals

* Test it with more real MHLs created in real scenarios, aiming to find interpretation issues and handle more exceptions
  * Make a list of available programs on the market that generate MHLs and obtain samples
* Observe the Media Hash List schema designed by Pomfort at <<https://mediahashlist.org/mhl-specification/>>
  * Observe generally if this program is set up to accommodate all requirements
  * Consider whether `xmltodict` offers some sort of schema checking functionality?
* Done: ~~Writing an executable version somehow so that it doesn't require Python~~
  * Now able to generate one-file executables using `pyinstaller`, works successfully.
  * Need to set up a development environment where I can:
    * Automate the generation of the executable
    * Push it to GitHub and make it available for download
    * Set up the repository with version numbers/tags
