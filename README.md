# mhl-compare
Written in Python. Work in progress (19 March 2019).

Given two [Media Hash List (MHL) files](https://mediahashlist.org/), this command line utility will compare them and show differences in hash, filenames, directory structure, size and more, of the media files described within them.

Useful when comparing two copies of media files that are intended to be the same, but they originate from other sources or were copied at different times.

`mhl-compare` does not read and compare physical media files against a MHL file, it only compares MHL files to each other.

---

### Example scenario
You use a MHL-generating program to copy video files stored on an SD card, to a folder in your local workspace. You give the SD card to a colleague and they make a similar copy with an MHL-generating program to an LTFS tape drive on their system. Later, your colleague reports an issue opening one of the video files, but you are unable to replicate the issue on your local copy.

Both you and your colleague have the capacity to run a MHL-verifying tool to re-read all the files and compare their validity *today*. However, it may also be useful to determine whether the two copies were identical, back at *the time of copy*. `mhl-compare` can read both MHL files and point out if their hashes were the same at the time the MHL files were generated. It will also indicate any other differences in file structure, naming or modification dates, that are highly likely to occur across copying software and operating systems.

The benefit is that you and your colleague would be able to see if you legitimately had identical copies of the media set, at the time you made them. It may reveal that some files were missing from either set, incorrectly copied, modified by something, placed in different folders, or any other myriad of file system anomalies. These kinds of differences are hard to observe when running a singular MHL-verifying application (like [MHLTool](https://mediahashlist.org/mhl-tool/), [Sealverify](https://pomfort.com/sealverify/), [Checkpoint](https://hedge.video/checkpoint)).

Additionally, MHL files are small (typically much less than 500 KB) and contain just XML, so it may be more practical to compare *them* instead when working with large media collections, where it is too time-consuming to read and verify the media files themselves, or they are stored in other physical locations.

---

### Usage

```
python mhl_compare.py first.mhl second.mhl
```

#### Options
* `-v, --verbose, --info`
  * Shows detailed, file-by-file description of the differences in each file.
  * By default, only a brief summary counting the number of issues is shown on screen.

---

### Installation

Work in progress. Download the .py file and try to run it.

---

### Compatibility

#### With MHL files
Can open any MHL file that is in [the standard XML format for MHL files](https://mediahashlist.org/mhl-specification/).

#### With running the program itself
Has been tested on Python 3.7.2 on macOS 10.14.3. Written in Python 3, so in its source format, it is not compatible with Python 2 branch, and cannot be run on macOS.

Has not been tested on Windows or Linux, but Python is generally pretty functional across OSs.

Dependency libraries: [`xmltodict`](https://github.com/martinblech/xmltodict), [`dateutil`](https://dateutil.readthedocs.io/en/stable/), [`humanize`](https://pypi.org/project/humanize/), [`termcolor`](https://pypi.org/project/termcolor/), [`dictdiffer`](https://github.com/hughdbrown/dictdiffer).

*Coming soon*: Executable file that can be downloaded and run on any macOS installation.

---

### Development goals

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
