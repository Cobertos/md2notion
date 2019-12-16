from pathlib import Path
import mistletoe
from notion.block import ImageBlock
from .NotionPyRenderer import NotionPyRenderer

def upload(mdFilePath, notionPage, imagePathFunc=None, notionPyRendererCls=NotionPyRenderer):
    """
    Uploads a single markdown file at mdFilePath to Notion.so as a child of
    notionPage.
    @param {string} mdFilePath The path to the markdown file
    @param {NotionBlock} notionPage The Notion.so block to add the markdown to
    @param {callable|None) [imagePathFunc=None] Function taking image source and mdFilePath
    to transform the relative image paths by if necessary (useful if your images are stored in weird
    locations relative to your md file.
    @param {NotionPyRenderer} notionPyRendererCls Class inheritting from the renderer
    incase you want to render the Markdown => Notion.so differently
    """
    with open(mdFilePath, "r", encoding="utf-8") as mdFile:
        # Convert the Markdown file
        rendered = mistletoe.markdown(mdFile, notionPyRendererCls)

        # Upload all the blocks
        for blockDescriptor in rendered:
            blockClass = blockDescriptor["type"]
            del blockDescriptor["type"]
            newBlock = notionPage.children.add_new(blockClass, **blockDescriptor)
            #TODO: Support CollectionViewBlock
            # Upload images to Notion.so that have local file paths
            if isinstance(newBlock, ImageBlock):
                imgRelSrc = blockDescriptor["source"]
                if '://' in imgRelSrc:
                    continue #Don't upload images that are external urls

                if callable(imagePathFunc): #Transform by imagePathLambda
                    imgSrc = imagePathFunc(imgRelSrc, mdFilePath)
                else:
                    imgSrc = Path(mdFilePath).parent  / Path(imgRelSrc)

                if not imgSrc.exists():
                    print(f"ERROR: Local image '{imgSrc}' not found to upload. Skipping...")
                    continue
                print(f"Uploading file '{imgSrc}'")
                newBlock.upload_file(str(imgSrc))


if __name__ == "__main__":
    import argparse
    import sys
    import os.path
    import glob
    from notion.block import PageBlock
    from notion.client import NotionClient
    parser = argparse.ArgumentParser(description='Uploads Markdown files to Notion.so')
    parser.add_argument('token_v2', type=str,
                        help='the token for your Notion.so session')
    parser.add_argument('page_url', type=str,
                        help='the url of the Notion.so page you want to upload your Markdown files to')
    parser.add_argument('md_file_globs', type=str, nargs='+',
                        help='globs to Markdown files to parse and upload')

    args = parser.parse_args(sys.argv[1:])

    client = NotionClient(token_v2=args.token_v2)
    page = client.get_block(args.page_url)

    for fp in glob.glob(*args.md_file_globs, recursive=True):
        # Make the new page in Notion.so
        pageName = os.path.basename(fp)[:40]
        newPage = page.children.add_new(PageBlock, title=pageName)
        print(f"Uploading {fp} to Notion.so at page {pageName}")
        upload(fp, newPage)