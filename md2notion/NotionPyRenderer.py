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
        self._debugStack = []
        super(NotionPyRenderer, self).__init__(*args, **kwargs)

    def _printDebugStack(self):
        debugStr = ""
        for idx, el in enumerate(self._debugStack):
            if idx > 0:
                lastEl = self._debugStack[idx-1]
                debugStr += f"\n > {'✓,'*(lastEl.currentChild)}"
            debugStr += f"{el.token.__class__.__name__}.children[{el.currentChild}]"
        return debugStr

    def render(self, token):
        """
        Takes a token and renders it and all it's children to a tree of
        NotionPy classes. Note that all the recursion is handled in the delegated
        methods.
        Overrides super().render but still uses render_map and then just
        does special parsing for stuff
        """
        self._debugStack.append(NotionPyRenderer.DebugStackEl(token))
        rendered = self.render_map[token.__class__.__name__](token)
        self._debugStack = self._debugStack[:-1]
        if self._debugStack: #len() > 0
            self._debugStack[-1].currentChild += 1
        return rendered

    def renderMultiple(self, tokens, passthrough=False):
        # Some renders might return arrays of nodes, so flatten to one list
        rendered = list(flatten([self.render(t) for t in tokens]))
        if passthrough:
            #If everything is a string, join it together
            if all(map(lambda t: isinstance(t, str), rendered)):
                return "".join(rendered)
            return rendered
        #Handle the rendering of strings that appear in the tree into TextBlocks
        #as paragraphs don't map 1:1 to TextBlocks (because they can appear
        #inside of ListItems and they can also contain Images sometimes too...)
        #TODO: Maybe this should be moved somewhere else...?
        def renderTextBlocks(token):
            if isinstance(token, str):
                return {
                    'type': TextBlock,
                    'title': token
                }
            else:
                return token
        return list(map(renderTextBlocks, rendered))

    def renderMultipleToString(self, tokens):
        """
        Takes token and renders it and all it's children to a single string
        """
        def toString(token):
            # Do a normal render, but if any of the renders come back with not
            # a string, then something in the heirarchy was not something
            # that could be converted to a string and raise
            rendered = self.render(token)
            if not isinstance(rendered, str):
                tokenType = token.__class__.__name__
                parseStack = self._printDebugStack()
                # Print an error if we encounter an error we expect, otherwise
                # raise a RuntimeError
                if any(map(lambda s: isinstance(s.token, Link), self._debugStack)) and isinstance(token, Image):
                    # Images nested somewhere inside of links
                    print(f"ERROR: Notion.so cannot support Images inside of Links, ignoring image... @ \n{parseStack}")
                    return f"-- IMAGE CAN'T BE INSIDE LINK {token.src} --"
                else:
                    raise RuntimeError(f"Can't render to string: {tokenType} inside inline element @ \n{parseStack}")
            return rendered

        return "".join([toString(t) for t in tokens])

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
        #TODO: Paragraphs can contain plain text or block level stuff like images,
        #so just ignore them and at the end, convert any strings to Notion
        # TextBlocks
        return self.renderMultiple(token.children, passthrough=True)
    def render_list(self, token):
        #List items themselves are each blocks, so skip it and directly render
        #the children
        return self.renderMultiple(token.children, passthrough=True)

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
        return {
            'type': NumberedListBlock if leaderContainsNumber else BulletedListBlock,
            'title': self.renderMultipleToString(token.children)
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
        #CollectionView and it's going to have nested items in it
        raise NotImplementedError("Currently this doesn't support tables, please file a bug report and I'll get right on it :3")
        return {
            'type': CollectionViewBlock,
            'rows': self.renderMultiple(token.children)
        }

    def render_table_row(self, token):
        cells = self.renderMultiple(token.children)
        return {
            'type': 'CollectionRowBlock',
            'title': cells[0]
            #cells 1-n are stored not in 'title' but in the names of their
            #properties. Considering Markdown doesn't support this, the best
            #would be to use the first heading in the table as the property
            #but there's no easy way to test for that...
            #TODO: What should we choose, can we use the table delimiters to make
            #a better decision?
        }

    def render_table_cell(self, token):
        #Render straight down to a string, cells aren't a concept in Notion
        return self.renderMultipleToString(token.children)