# Fountain Parser

## About

NOTE: Forked from [fountain](https://github.com/Tagirijus/fountain) to add support for Fountain's built-in markup styling.

This Python script is a Fountain script parser, which converts `.fountain` files to Python objects.

* Modified by [Ian Thomas](https://github.com/wildwinter/)
* Modified by [Tagirijus](https://github.com/Tagirijus/)
* Ported to Python 3 by Colton J. Provias - cj@coltonprovias.com - [original code here](https://gist.github.com/ColtonProvias/8232624)
* based on `Fountain` by Nima Yousefi & John August; original code for Objective-C at [https://github.com/nyousefi/Fountain].

## Install

1. Make a pull request of this repo
3. Go into the repo-dir on your machine
2. `sudo python3 setup.py install`

## Usage

```
from fountain import fountain

fount = fountain.Fountain(STRING)
```

This will make `fount` into a Fountain object.

### Style Markup
This version supports simple bold, italic, and underline markup.

Symbols
```
*italic*
**bold**
***bolditalic***
_underline_
_underlined and **also bold**_
```

It adds the method `split_to_chunks()` to `FountainElement`.

Optionally you can call it on an element to scan the text and break it into `FountainChunk` objects which will be stored on `FountainElement.chunks`.

These chunks each consist of a text element, and whether italic, bool, or underline is true for that element.

```
from fountain import fountain

fount = fountain.Fountain(STRING)

for element in fount.elements:
    
    # For these two types we want to care about markup...
    if (element.element_type == 'Character' 
        or element.element_type == 'Action'):

        chunks = element.split_to_chunks()
        for chunk in chunks:
            some_dummy_font_setup(
                bold = chunk.bold, 
                italic = chunk.italic,
                underline = chunk.underline)
            print_the_text(chunk.text)

        print_new_line()

    # Otherwise
    else:
        print_the_text(element.element_text)
        print_new_line()
        

```
