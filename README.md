# XCXGecko
Trainer for XCX using [pyGecko](https://github.com/wiiudev/pyGecko). Requires kernel exploit to use.

## Features

* Modify funds, miranium, reward tickets, ...
* Modify character name, level, rank, BP, affinity
* Modify character geometry (height, chest, ...)
* Modify amount of item (materials, probes, ...)
* [Change/Add items](#change-and-add-items)
* [Quickly create custom codes (e.g. max items for crafting)](#custom-codes)

<table><tr><td width="50%">
  <img src="https://raw.githubusercontent.com/mimicax/XCXGecko/master/screenshot.png ">
  (main interface)
</td>
<td width="50%">
  <img src="https://raw.githubusercontent.com/mimicax/XCXGecko/master/sample.jpg">
  (chibi/mega characters, different chest sizes, custom names)
</td></tr></table>

## Change and Add Items

Changing item type:

1. Click ```Cache Slots``` for desired item type
* Choose slot to be modified, and note <i>original item</i>'s name/ID
* Select new item ```Name```, or type in new ```ID (hex)```
* Set desired ```Amount```, then click ```Poke```

Restoring original item:

1. In game, purchase/acquire <i>original item</i>
* Click ```Cache Slots``` for desired item type
* Select <i>original item</i> ```Name```, or type in ```ID (hex)```
* Click ```Search ID``` to find slot
* Set desired ```Amount```, then click ```Poke```

## Custom Codes

In the ```Custom Codes``` tab, you can create one-click entry that pokes one or more addresses.

Example: maximize item amounts to engineer <i>Potential Boost XX</i> augment:

1. Purchase, find, or [add](#change-and-add-items) <i>Nutricious Microbes</i>, <i>Clear Gerrid Soup</i>, <i>Gularthion Everflame</i>, and <i>Bonjelium</i>
* Click ```Cache Slots``` for Materials
* Set ```Name``` to <i>Nutricious Microbes</i>, click ```Search ID```, set ```Amount``` to 99, then click ```Poke```
* In ```Status``` dialog, note down latest POKE entry, e.g. ```POKE 1C3BD65C 00138318``` (assuming poke verbosity is enabled in ```config.ini```)
* Repeat above to find POKE codes for <i>Clear Gerrid Soup</i>, <i>Gularthion Everflame</i>, and <i>Bonjelium (Precious Resources)</i>
* In ```Custom Codes``` tab, click ```Add Entry```, then paste all 4 POKE entries on separate lines
* Click ```Poke``` to maximize amounts for all 4 items

## Binary Dependencies

* [Microsoft Visual C++ 2008 Redistributable Package (x86)](http://www.microsoft.com/en-us/download/details.aspx?id=29)

## Run using python

Extra dependencies:

* [Python 2.7+](https://www.python.org/downloads/release/python-2711/)
* [PyQt4 for Python 2.7+](https://www.riverbankcomputing.com/software/pyqt/download)

Run ```python XCXGecko.py```

## Build binary

Extra dependencies:

* [py2exe for Python 2.7+](http://sourceforge.net/projects/py2exe/files/py2exe/0.6.9/)

Run ```build.bat```
