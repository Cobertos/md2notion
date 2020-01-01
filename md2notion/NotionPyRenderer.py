import random
import re
import collections
from notion.block import CodeBlock, DividerBlock, HeaderBlock, SubheaderBlock, \
    SubsubheaderBlock, QuoteBlock, TextBlock, NumberedListBlock, \
    BulletedListBlock, ImageBlock, CollectionViewBlock
from mistletoe.base_renderer import BaseRenderer
from mistletoe.span_token import Image, Link

def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes, dict)):
            yield from flatten(el)
        else:
            yield el

class NotionPyRenderer(BaseRenderer):
    """
    A class that will render out a Markdown file into a descriptor for upload
    with notion-py. Each object will have a .type for the block type and then
    a bunch of different dict entries corresponding to kwargs for that block
    type.
    For CollectionViewBlocks, a .rows entry exists in the dictionary with a list
    object containing a descriptor for every row. This is still TODO
    """

    class DebugStackEl:
        def __init__(self, token):
            self.token = token
            self.currentChild = 0

    def __init__(self, *args, **kwargs):
        self._debugLastContent = None
        self._debugStack = []
        super(NotionPyRenderer, self).__init__(*args, **kwargs)

    def _printDebugStack(self):
        debugStr = ""
        for idx, el in enumerate(self._debugStack):
            if idx > 0:
                lastEl = self._debugStack[idx-1]
                debugStr += f"\n > {'✓,'*(lastEl.currentChild)}"
            debugStr += f"✗ @ {el.token.__class__.__name__}.children[{el.currentChild}]"
        if self._debugLastContent:
            debugStr += f"\n Error raised just after '{self._debugLastContent[-80:]}'"
        return debugStr

    def _pushDebugStack(self, token):
        self._debugStack.append(NotionPyRenderer.DebugStackEl(token))

    def _popDebugStack(self):
        self._debugStack = self._debugStack[:-1]
        #Bookkeeping to know where we are in the tree
        if self._debugStack: #len() > 0
            self._debugStack[-1].currentChild += 1

    def render(self, token):
        """
        Takes a single Markdown token and renders it down to
        NotionPy classes. Note that all the recursion is handled in the delegated
        methods.
        Overrides super().render but still uses render_map and then just
        does special parsing for stuff
        """
        self._pushDebugStack(token)
        rendered = self.render_map[token.__class__.__name__](token)
        self._popDebugStack()
        return rendered

    def renderMultiple(self, tokens):
        """
        Takes an array of sibling tokens and renders each one out.
        """
        return list(flatten(self.render(t) for t in tokens))

    def renderMultipleToString(self, tokens):
        """
        Takes token and renders it and all it's children to a single string
        """
        def toString(renderedBlock):
            if isinstance(renderedBlock, str):
                return renderedBlock
            elif isinstance(renderedBlock, dict) and renderedBlock['type'] == TextBlock:
                return renderedBlock['title'] #This unwraps TextBlocks/paragraphs to use in other blocks
            elif isinstance(renderedBlock, dict) and renderedBlock['type'] == ImageBlock:
                print("ERROR: Notion.so cannot support Images inside of inline contexts (like links). Ignoring image...")
                return f"-- Image {renderedBlock['source']} removed during Markdown Import (can't add image to inline context) --"
            else:
                raise RuntimeError(f"Can't render to string: {tokenType} inside inline element @ \n{parseStack}")
            # Do a normal render, but if any of the renders come back with not
            # a string, then something in the heirarchy was not something
            # that could be converted to a string and raise
            rendered = self.render(token)
            if not isinstance(rendered, str):
                tokenType = token.__class__.__name__
                parseStack = self._printDebugStack()
                # Print an error if we encounter an error we expect, otherwise
                # raise a RuntimeError
                
            return rendered

        #Render multiple, try to convert any objects to strings, join everything together
        return "".join([ toString(b) for b in self.renderMultiple(tokens)])

    def render_document(self, token):
        return self.renderMultiple(token.children)

    # == MD Block Tokens ==
    def render_block_code(self, token):
        #Indented code and ``` ``` code fence
        #Notion seems really picky about the language field and the case sensitivity
        #so we match the string to the specific version that Notion.so expects
        notionSoLangs = [
            "ABAP", 
            "Arduino", 
            "Bash", 
            "BASIC", 
            "C", 
            "Clojure", 
            "CoffeeScript", 
            "C++", 
            "C#", 
            "CSS", 
            "Dart", 
            "Diff", 
            "Docker", 
            "Elixir", 
            "Elm", 
            "Erlang", 
            "Flow", 
            "Fortran", 
            "F#", 
            "Gherkin", 
            "GLSL", 
            "Go", 
            "GraphQL", 
            "Groovy", 
            "Haskell", 
            "HTML", 
            "Java", 
            "JavaScript", 
            "JSON", 
            "Kotlin", 
            "LaTeX", 
            "Less", 
            "Lisp", 
            "LiveScript", 
            "Lua", 
            "Makefile", 
            "Markdown", 
            "Markup", 
            "MATLAB", 
            "Nix", 
            "Objective-C", 
            "OCaml", 
            "Pascal", 
            "Perl", 
            "PHP", 
            "Plain Text", 
            "PowerShell", 
            "Prolog", 
            "Python", 
            "R", 
            "Reason", 
            "Ruby", 
            "Rust", 
            "Sass", 
            "Scala", 
            "Scheme", 
            "Scss", 
            "Shell", 
            "SQL", 
            "Swift", 
            "TypeScript", 
            "VB.Net", 
            "Verilog", 
            "VHDL", 
            "Visual Basic", 
            "WebAssembly", 
            "XML", 
            "YAML"
        ]
        matchLang = next((lang for lang in notionSoLangs if re.match(re.escape(token.language), lang, re.I)), [None])
        if not matchLang:
            print(f"Code block language {matchLang} has no corresponding syntax in Notion.so")

        return {
            'type': CodeBlock,
            'language': matchLang,
            'title': self.renderMultipleToString(token.children)
        }
    def render_thematic_break(self, token):
        return {
            'type': DividerBlock
        }
    def render_heading(self, token):
        level = token.level
        if level > 3:
            print(f"h{level} not supported in Notion.so, converting to h3")
            level = 3
        return {
            'type': [HeaderBlock, SubheaderBlock, SubsubheaderBlock][level-1],
            'title': self.renderMultipleToString(token.children)
        }
    def render_quote(self, token):
        return {
            'type': QuoteBlock,
            'title': self.renderMultipleToString(token.children)
        }
    def render_paragraph(self, token):
        return {
            'type': TextBlock,
            'title': self.renderMultipleToString(token.children)
        }
    def render_list(self, token):
        #List items themselves are each blocks, so skip it and directly render
        #the children
        return self.renderMultiple(token.children)

    # == MD Span Tokens ==
    # These ones are not converted to Notion.so blocks, so just use their markdown
    # equivalent and NotionPy handles the rest...
    # Note that only raw_text will ever have no children
    def render_strong(self, token):
        return f"**{self.renderMultipleToString(token.children)}**"
    def render_emphasis(self, token):
        return f"*{self.renderMultipleToString(token.children)}*"
    def render_inline_code(self, token):
        return f"`{self.renderMultipleToString(token.children)}`"
    def render_raw_text(self, token):
        self._debugLastContent = token.content
        return token.content
    def render_strikethrough(self, token):
        return f"~{self.renderMultipleToString(token.children)}~"
    def render_link(self, token):
        return f"[{self.renderMultipleToString(token.children)}]({token.target})"
    def render_escape_sequence(self, token):
        #Pretty sure this is just like \xxx type escape sequences?
        return f"\\{self.renderMultipleToString(token.children)}"
    def render_line_break(self, token):
        return '\n'

    # These convert to Notion.so blocks
    def render_list_item(self, token):
        leaderContainsNumber = re.match(r'\d', token.leader) #Contains a number

        #Lists can have "children" (nested lists, nested images...), so we need
        #to render out all the nodes and sort through them to find the string
        #for this item and any children
        rendered = self.renderMultiple(token.children)
        children = [b for b in rendered if b['type'] != TextBlock]
        strings = [s['title'] for s in rendered if s['type'] == TextBlock]

        return {
            'type': NumberedListBlock if leaderContainsNumber else BulletedListBlock,
            'title': "".join(strings),
            'children': children
        }

    def render_image(self, token):
        #Alt text
        alt = token.title or self.renderMultipleToString(token.children)
        return {
            'type': ImageBlock,
            'display_source': token.src,
            'source': token.src,
            'caption': alt
        }

    def render_table(self, token):
        headerRow = self.render(token.header) #Header is a single row
        rows = [self.render(r) for r in token.children] #don't use renderMultiple because it flattens

        def randColId():
            def randChr():
                #ASCII 32 - 126 is ' ' to '~', all printable characters
                return chr(random.randrange(32,126))
            #4 characters long of random printable characters, I don't think it
            #has any correlation to the data?
            return "".join([randChr() for c in range(4)])
        def textColSchema(colName):
            return { 'name' : colName, 'type': 'text' }
        #The schema is basically special identifiers + the type of property
        #to put into Notion. Coming from Markdown, everything is going to
        #be text.
        # 'J=}x': {
        #     'name': 'Column',
        #     'type': 'text'
        # },
        schema = { randColId() : textColSchema(headerRow[r]) for r in range(len(headerRow) - 1) }
        #The last one needs to be named 'Title' and is type title
        # 'title': {
        #     'name': 'Name',
        #     'type': 'title'
        # }
        schema.update({
                'title' : {
                    'name': headerRow[-1],
                    'type': 'title'
                }
            })

        #CollectionViewBlock, and it's gonna be a bit hard to do because this
        #isn't fully fleshed out in notion-py yet but we can still use create_record
        return {
            'type': CollectionViewBlock,
            'rows': rows, #everything except the initial row
            'schema': schema
        }

    def render_table_row(self, token):
        #Rows are a concept in Notion (`CollectionRowBlock`) but notion-py provides
        #another API to use it, `.add_row()` so we just render down to an array
        #and handle in the Table block.
        return self.renderMultiple(token.children)

    def render_table_cell(self, token):
        #Render straight down to a string, cells aren't a concept in Notion
        return self.renderMultipleToString(token.children)