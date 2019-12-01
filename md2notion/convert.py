from . import NotionPyRenderer

def convert(mdStr, notionPage):
    """
    Converts a single markdown string and places the contents
    at notionPage
    """
    rendered = mistletoe.markdown(mdStr, NotionPyRenderer)
    for blockDescriptor in rendered:
        blockClass = blockDescriptor.type
        del blockDescriptor.type
        notionPage.children.add_new(blockClass, **blockDescriptor)
        #TODO: Support CollectionViewBlock
