"""
fountain.py

from https://github.com/wildwinter/fountain

Released under MIT License.

Ported to Python 3 by Colton J. Provias - cj@coltonprovias.com
Original Python code at https://gist.github.com/ColtonProvias/8232624
Based on Fountain by Nima Yousefi & John August
Original code for Objective-C at https://github.com/nyousefi/Fountain
Further Edited by Manuel Senfft
Further Edited by Ian Thomas
"""

from enum import Enum

# Element Types
class Element(Enum):
    EMPTY = 1
    BONEYARD = 2
    PAGE_BREAK = 3
    SYNOPSIS = 4
    COMMENT = 5
    SECTION_HEADING = 6
    SCENE_HEADING = 7
    TRANSITION = 8
    ACTION = 9
    CHARACTER = 10
    PARENTHETICAL = 11
    DIALOGUE = 12


COMMON_TRANSITIONS = {'FADE OUT.', 'CUT TO BLACK.', 'FADE TO BLACK.'}
CHARACTER_ALLOWABLE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ _ÄÖÜ0123456789'


def strip_slashes(text):
    return text.replace("\\","")

class FountainChunk:
    def __init__(self, bold=False, italic=False, underline=False):
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.text = ""
                  
    def copy(self):
        return FountainChunk(self.bold, self.italic, self.underline)
    
    def __repr__(self):
        out = ""
        if self.underline:
            out += "<u>"
        if self.bold:
            out += "<b>"
        if self.italic:
            out += "<i>"
        out += self.text
        if self.italic:
            out += "</i>"
        if self.bold:
            out += "</b>"
        if self.underline:
            out += "</u>"
        return out

                
class FountainElement:
    def __init__(
        self,
        element_type,
        element_text='',
        section_depth=0,
        scene_number='',
        is_centered=False,
        is_dual_dialogue=False,
        original_line=0,
        scene_abbreviation='.',
        original_content=''
    ):
        self.element_type = element_type
        self.element_text = element_text
        self.section_depth = section_depth
        self.scene_number = scene_number
        self.scene_abbreviation = scene_abbreviation
        self.is_centered = is_centered
        self.is_dual_dialogue = is_dual_dialogue
        self.original_line = original_line
        self.original_content = original_content

    def is_empty(self):
        return (self.element_type == Element.EMPTY 
                or self.element_type == Element.PAGE_BREAK
                or self.element_type == Element.BONEYARD)

    # take the element_text and split it into
    # formatted chunks
    def split_to_chunks(self):
        
        # This is very simple and will choke on
        # invalid nesting
        chunk = FountainChunk()
        chunks  = [chunk]
                                
        is_escaped = False
        stars = ""
        
        for c in self.element_text:
            if is_escaped:
                is_escaped = False
                chunk.text+=c
                continue
                                                
            if stars!="" and c!=stars[0]:            
                new_chunk = chunk.copy()

                if stars=="***":
                    new_chunk.bold = not chunk.bold
                    new_chunk.italic = not chunk.italic
                elif stars=="**":
                    new_chunk.bold = not chunk.bold
                elif stars=="*":
                    new_chunk.italic = not chunk.italic
                                
                chunks.append(new_chunk)

                chunk = new_chunk
                stars = ""
                                                                
            if c=='\\':
                is_escaped = True
                continue
                                                                                            
            if c=='_':
                new_chunk = chunk.copy()
                new_chunk.underline = not chunk.underline
                chunks.append(new_chunk)
                chunk = new_chunk
                continue

            if c=='*':
                stars+=c
                continue
                            
            chunk.text+=c

        return chunks

    def __repr__(self):
        return self.element_type + ': ' + self.element_text

class FountainScene:
    def __init__(self, scene_header_text=""):
        self.header_text = strip_slashes(scene_header_text)
        self.elements = list()

    def append(self, element):
        self.elements.append(element)

    def is_empty(self):
        for element in self.elements:
            if not element.is_empty():
                return False
        return True
    

class Fountain:
    def __init__(self, string=None, path=None):
        self.metadata = dict()
        self.elements = list()
        self.scenes = list()

        if path:
            with open(path) as fp:
                self.contents = fp.read()
        else:
            self.contents = string
        if self.contents != '':
            self.parse()

    def parse(self):
        contents = self.contents.strip().replace('\r', '')

        contents_has_metadata = ':' in contents.splitlines()[0]
        contents_has_body = '\n\n' in contents

        if contents_has_metadata and contents_has_body:
            script_head, script_body = contents.split('\n\n', 1)
            self._parse_head(script_head.splitlines())
            self._parse_body(script_body.splitlines())
        elif contents_has_metadata and not contents_has_body:
            self._parse_head(contents.splitlines())
        else:
            self._parse_body(contents.splitlines())

    def _parse_head(self, script_head):
        open_key = None
        for line in script_head:
            line = line.rstrip()
            if line[0].isspace():
                self.metadata[open_key].append(line.strip())
            elif line[-1] == ':':
                open_key = line[0:-1].lower()
                self.metadata[open_key] = list()
            else:
                key, value = line.split(':', 1)
                self.metadata[key.strip().lower()] = [value.strip()]

    def _add_scene(self, scene_header_elem):
        last_scene = self.scenes[-1]
        if last_scene.is_empty():
            self.scenes.pop()
        new_scene = FountainScene(scene_header_elem.element_text)
        new_scene.elements.append(scene_header_elem)
        self.scenes.append(new_scene)
        return new_scene

    def _parse_body(self, script_body):
        is_comment_block = False
        is_inside_dialogue_block = False
        newlines_before = 0
        index = -1
        comment_text = list()
        curr_scene = FountainScene()
        self.scenes = [curr_scene]

        for linenum, line in enumerate(script_body):
            assert type(line) is str
            index += 1
            line = line.lstrip()
            full_strip = line.strip()

            if (not line or line.isspace()) and not is_comment_block:
                self.elements.append(FountainElement(Element.EMPTY))
                curr_scene.append(self.elements[-1])
                is_inside_dialogue_block = False
                newlines_before += 1
                continue

            if line.startswith('/*'):
                line = line.rstrip()
                if line.endswith('*/'):
                    text = line.replace('/*', '').replace('*/', '')
                    self.elements.append(
                        FountainElement(
                            Element.BONEYARD,
                            text,
                            original_line=linenum,
                            original_content=line
                        )
                    )
                    curr_scene.append(self.elements[-1])
                    is_comment_block = False
                    newlines_before = 0
                else:
                    is_comment_block = True
                    comment_text.append('')
                continue

            if line.rstrip().endswith('*/'):
                text = line.replace('*/', '')
                comment_text.append(text.strip())
                self.elements.append(
                    FountainElement(
                        Element.BONEYARD,
                        '\n'.join(comment_text),
                        original_line=linenum,
                        original_content=line
                    )
                )
                curr_scene.append(self.elements[-1])
                is_comment_block = False
                comment_text = list()
                newlines_before = 0
                continue

            if is_comment_block:
                comment_text.append(line)
                continue

            if line.startswith('==='):
                self.elements.append(
                    FountainElement(
                        Element.PAGE_BREAK,
                        line,
                        original_line=linenum,
                        original_content=line
                    )
                )
                curr_scene.append(self.elements[-1])
                newlines_before = 0
                continue

            if len(full_strip) > 0 and full_strip[0] == '=':
                self.elements.append(
                    FountainElement(
                        Element.SYNOPSIS,
                        full_strip[1:].strip(),
                        original_line=linenum,
                        original_content=line
                    )
                )
                curr_scene.append(self.elements[-1])
                continue

            if (
                newlines_before > 0
                and full_strip.startswith('[[')
                and full_strip.endswith(']]')
            ):
                self.elements.append(
                    FountainElement(
                        Element.COMMENT,
                        full_strip.strip('[] \t'),
                        original_line=linenum,
                        original_content=line
                    )
                )
                curr_scene.append(self.elements[-1])
                continue

            if len(full_strip) > 0 and full_strip[0] == '#':
                newlines_before = 0
                depth = full_strip.split()[0].count('#')
                self.elements.append(
                    FountainElement(
                        Element.SECTION_HEADING,
                        full_strip[depth:].strip(),
                        section_depth=depth,
                        original_line=linenum,
                        original_content=line
                    )
                )
                curr_scene.append(self.elements[-1])
                continue

            if len(line) > 1 and line[0] == '.' and line[1] != '.':
                newlines_before = 0
                if full_strip[-1] == '#' and full_strip.count('#') > 1:
                    scene_number_start = len(full_strip) - \
                        full_strip[::-1].find('#', 1) - 1
                    self.elements.append(
                        FountainElement(
                            Element.SCENE_HEADING,
                            full_strip[1:scene_number_start].strip(),
                            scene_number=full_strip[
                                scene_number_start:
                            ].strip('#').strip(),
                            original_line=linenum,
                            original_content=line
                        )
                    )
                    curr_scene = self._add_scene(self.elements[-1])
                else:
                    self.elements.append(
                        FountainElement(
                            Element.SCENE_HEADING,
                            full_strip[1:].strip(),
                            original_line=linenum,
                            original_content=line
                        )
                    )
                    curr_scene = self._add_scene(self.elements[-1])
                continue

            if len(line) > 1 and line[0] == '!':
                self.elements.append(
                    FountainElement(
                        Element.ACTION,
                        full_strip[1:].strip(),
                        original_line=linenum,
                        original_content=line
                    )
                )
                curr_scene.append(self.elements[-1])
                continue

            if (
                line[0:4].upper() in
                ['INT ', 'INT.', 'EXT ', 'EXT.', 'EST ', 'EST.', 'I/E ', 'I/E.']
                or line[0:8].upper() in ['INT/EXT ', 'INT/EXT.']
                or line[0:9].upper() in ['INT./EXT ', 'INT./EXT.']
            ):
                newlines_before = 0
                scene_name_start = line.find(line.split()[1])
                if full_strip[-1] == '#' and full_strip.count('#') > 1:
                    scene_number_start = len(full_strip) - \
                        full_strip[::-1].find('#', 1) - 1
                    self.elements.append(
                        FountainElement(
                            Element.SCENE_HEADING,
                            line.split()[0]+" "+full_strip[
                                scene_name_start:scene_number_start
                            ].strip(),
                            scene_number=full_strip[
                                scene_number_start:
                            ].strip('#').strip(),
                            original_line=linenum,
                            scene_abbreviation=line.split()[0],
                            original_content=line
                        )
                    )
                    curr_scene = self._add_scene(self.elements[-1])
                else:
                    self.elements.append(
                        FountainElement(
                            Element.SCENE_HEADING,
                            line.split()[0]+" "+full_strip[scene_name_start:].strip(),
                            original_line=linenum,
                            scene_abbreviation=line.split()[0],
                            original_content=line
                        )
                    )
                    curr_scene = self._add_scene(self.elements[-1])
                continue

            if full_strip.endswith(' TO:'):
                newlines_before = 0
                self.elements.append(
                    FountainElement(
                        Element.TRANSITION,
                        full_strip,
                        original_line=linenum,
                        original_content=line
                    )
                )
                curr_scene.append(self.elements[-1])
                continue

            if full_strip in COMMON_TRANSITIONS:
                newlines_before = 0
                self.elements.append(
                    FountainElement(
                        Element.TRANSITION,
                        full_strip,
                        original_line=linenum,
                        original_content=line
                    )
                )
                curr_scene.append(self.elements[-1])
                continue

            if full_strip[0] == '>':
                newlines_before = 0
                if len(full_strip) > 1 and full_strip[-1] == '<':
                    self.elements.append(
                        FountainElement(
                            Element.ACTION,
                            full_strip[1:-1].strip(),
                            is_centered=True,
                            original_line=linenum,
                            original_content=line
                        )
                    )
                    curr_scene.append(self.elements[-1])
                else:
                    self.elements.append(
                        FountainElement(
                            Element.TRANSITION,
                            full_strip[1:].strip(),
                            original_line=linenum,
                            original_content=line
                        )
                    )
                    curr_scene.append(self.elements[-1])
                continue

            if (
                newlines_before > 0
                and index + 1 < len(script_body)
                and script_body[index + 1]
                and not line[0] in ['[', ']', ',', '(', ')']
                and (all([(c in CHARACTER_ALLOWABLE) for c in full_strip])
                     or full_strip[0] == '@')
            ):
                newlines_before = 0
                if full_strip[-1] == '^':
                    for element in reversed(self.elements):
                        if element.element_type == Element.CHARACTER:
                            element.is_dual_dialogue = True
                            break
                    self.elements.append(
                        FountainElement(
                            Element.CHARACTER,
                            full_strip.lstrip('@').rstrip('^').strip(),
                            is_dual_dialogue=True,
                            original_line=linenum,
                            original_content=line
                        )
                    )
                    curr_scene.append(self.elements[-1])
                    is_inside_dialogue_block = True
                else:
                    self.elements.append(
                        FountainElement(
                            Element.CHARACTER,
                            full_strip.lstrip('@'),
                            original_line=linenum,
                            original_content=line
                        )
                    )
                    curr_scene.append(self.elements[-1])
                    is_inside_dialogue_block = True
                continue

            if is_inside_dialogue_block:
                if newlines_before == 0 and full_strip[0] == '(':
                    self.elements.append(
                        FountainElement(
                            Element.PARENTHETICAL,
                            full_strip,
                            original_line=linenum,
                            original_content=line
                        )
                    )
                    curr_scene.append(self.elements[-1])
                else:
                    if self.elements[-1].element_type == Element.DIALOGUE:
                        self.elements[-1].element_text = '\n'.join(
                            [self.elements[-1].element_text, full_strip]
                        )
                        self.elements[-1].original_content = '\n'.join(
                            [self.elements[-1].original_content, line]
                        )
                    else:
                        self.elements.append(
                            FountainElement(
                                Element.DIALOGUE,
                                full_strip,
                                original_line=linenum,
                                original_content=line
                            )
                        )
                        curr_scene.append(self.elements[-1])
                continue

            if newlines_before == 0 and len(self.elements) > 0:
                self.elements[-1].element_text = '\n'.join(
                    [self.elements[-1].element_text, full_strip])
                newlines_before = 0
            else:
                self.elements.append(
                    FountainElement(
                        Element.ACTION,
                        full_strip,
                        original_line=linenum,
                        original_content=line
                    )
                )
                curr_scene.append(self.elements[-1])
                newlines_before = 0
