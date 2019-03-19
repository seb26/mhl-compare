# mhl-compare
Written in Python. Work in progress (19 March 2019).

Given two [Media Hash List (MHL) files](https://mediahashlist.org/), this command line utility will compare them and show differences in hash, filenames, directory structure, size and more.

Useful when comparing two copies of media files that are intended to be the same, but they originate from other sources or were copied at different times.

### Example scenario
You use a MHL-generating program to copy video files stored on an SD card, to a folder in your local workspace. You give the SD card to a colleague and they make a similar copy with an MHL-generating program to an LTFS tape drive. Later, your colleague reports an issue opening one of the video files, but you are unable to replicate the issue on your local copy.

Both you and your colleague have the capacity to run a MHL-verifying tool to re-read all the files and compare their validity today. However, it may also be useful to determine whether the two copies were identical, back at the time of copy. `mhl-compare` can read both MHL files and point out if their hashes are the same at the time the MHL files were written. It will also indicate any other differences in file structure, naming or modification dates, that are highly likely to occur across different copy software and operating systems.

### Usage

```
python mhl_compare.py first.mhl second.mhl
```

### Installation

Work in progress. Download the .py file and try to run it.

### Compatibility

Written in Python 3, tested on Python 3.7.2 with Homebrew on macOS 10.14.3.

Dependency libraries: `xmltodict`, `dateutil`, `humanize`, `termcolor`, `dictdiffer`.

### Development goals

* Test it with more real MHLs created in real scenarios, aiming to find interpretation issues and handle more exceptions
* Consider the importance of compatibility with Python 2.7.10, given that it is the default version of Python distributed with macOS, and it would mean that the script could be downloaded and run immediately on new machines
* Writing an executable version somehow so that it doesn't require Python
