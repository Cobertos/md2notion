import mistletoe
from .NotionPyRenderer import NotionPyRenderer

def convert(mdFile, notionPage):
    """
    Converts a single markdown string and places the contents
    at notionPage
    """
    rendered = mistletoe.markdown(mdFile, NotionPyRenderer)
    for blockDescriptor in rendered:
        blockClass = blockDescriptor["type"]
        del blockDescriptor["type"]
        notionPage.children.add_new(blockClass, **blockDescriptor)
        #TODO: Support CollectionViewBlock

if __name__ == "__main__":
    import sys
    import os.path
    import glob
    from notion.block import PageBlock
    from notion.client import NotionClient
    client = NotionClient(token_v2=sys.argv[1])
    page = client.get_block(sys.argv[2])

    for fp in glob.glob(*sys.argv[3:], recursive=True):
        pageName = os.path.basename(fp)[:40]
        print(f"Converting {fp} to {pageName}")
        with open(fp, "r", encoding="utf-8") as f:
            newPage = page.children.add_new(PageBlock, title=pageName)
            convert(f, newPage)