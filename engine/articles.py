import bz2
import xml.etree.ElementTree as ET

def yield_wiki_articles(filepath):
    """
    Yields Wikipedia articles from a compressed XML bz2 dump, filtering out redirects.

    Args:
        filepath (str): Path to the .xml.bz2 file (e.g., enwiki-latest-pages-articles.xml.bz2)

    Yields:
        dict: A dictionary containing 'id', 'title', and 'text' of the article.
    """
    
    # Open the compressed file in text mode with utf-8 encoding
    with bz2.open(filepath, 'rt', encoding='utf-8') as f:
        # iterparse allows us to read the file incrementally without loading RAM.
        # We need 'start' events to capture the root for clearing memory later,
        # and 'end' events to process completed elements.
        context = ET.iterparse(f, events=("start", "end"))
        
        # Turn it into an iterator
        context = iter(context)
        
        # Get the root element (the first event is the start of the root)
        # We need this reference to clear children effectively
        event, root = next(context)

        # Iterate through the XML elements
        for event, elem in context:
            # We only process on 'end' events to ensure the element is fully populated
            if event == "end" and elem.tag.endswith('page'):
                
                title = ''
                text = ''
                page_id = ''
                is_redirect = False
                ns = '0' # Default to 0, which is Main/Article namespace

                # Inspect children of the <page> element
                for child in elem:
                    if child.tag.endswith('title'):
                        title = child.text
                    
                    elif child.tag.endswith('ns'):
                        ns = child.text

                    elif child.tag.endswith('redirect'):
                        is_redirect = True
                    
                    elif child.tag.endswith('id'):
                        # This captures the Page ID (not the Revision ID)
                        page_id = child.text

                    elif child.tag.endswith('revision'):
                        # Dig into the revision to get the text
                        for rev_child in child:
                            if rev_child.tag.endswith('text'):
                                text = rev_child.text

                # Filtering Logic:
                # 1. Namespace 0 (Main Articles)
                # 2. Not a redirect tag
                # 3. Text is not None and not empty
                if ns == '0' and not is_redirect and text and len(text) > 0:
                    yield {
                        'id': page_id,
                        'title': title,
                        'text': text
                    }

                # CRITICAL MEMORY MANAGEMENT:
                # 1. Clear the content of the current element (page)
                elem.clear()
                
                # 2. Clear the children of the root to release the empty shell of this page
                #    This is safe because we are processing sequentially and don't look back.
                root.clear()

# --- Usage Example ---
if __name__ == "__main__":
    # NOTE: Ensure this points to the XML dump, not the index.txt file
    path = r"C:\Users\Lenovo\Downloads\wikidump\enwiki-20250501-pages-articles-multistream.xml.bz2"

    try:
        print(f"Processing: {path}...")
        article_generator = yield_wiki_articles(path)

        # Print the first 5 articles found
        for i, article in enumerate(article_generator):
            print(f"[{i+1}] ID: {article['id']} | Title: {article['title']}")
            print(f"    Start of text: {article['text'][:100]}...")
            print("-" * 60)
            
            if i >= 4: # Stop after 5 for demonstration
                break
                
    except FileNotFoundError:
        print("File not found. Please check the path.")
    except Exception as e:
        import traceback
        traceback.print_exc()