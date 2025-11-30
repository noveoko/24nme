import wikitextparser as wtp
import json
import uuid
import re

def parse_wiki_markup(wiki_text):
    parsed = wtp.parse(wiki_text)
    
    # helper to generate a unique placeholder
    def get_id():
        return str(uuid.uuid4().hex)

    # 1. Extract Infoboxes
    infoboxes = []
    target_templates = [
        t for t in parsed.templates 
        if t.name.strip().lower().startswith("infobox")
    ]
    
    for template in target_templates:
        uid = get_id()
        data = {param.name.strip(): param.value.strip() for param in template.arguments}
        data['_template_name'] = template.name.strip()
        
        infoboxes.append({
            "id": uid,
            "data": json.dumps(data, indent=2) # Keeping your existing JSON string format
        })
        
        # Replace template in text with the UUID marker
        template.string = f"__INFOBOX_{uid}__"

    # 2. Extract Tables
    tables = []
    for t in parsed.tables:
        uid = get_id()
        tables.append({
            "id": uid,
            "content": t.string
        })
        
        # Replace table in text with the UUID marker
        t.string = f"__TABLE_{uid}__"

    # 3. Extract Bullet Points
    bullet_groups = []
    # Note: get_lists() returns a list of List objects from the AST
    for lst in parsed.get_lists():
        # lst.string contains the full raw wikitext of the list
        if lst.string.strip().startswith('*'):
            current_group = []
            for item in lst.items:
                # item is a string of wikitext
                text_content = wtp.parse(item).plain_text().strip()
                if text_content:
                    current_group.append(text_content)
            
            if current_group:
                uid = get_id()
                bullet_groups.append({
                    "id": uid,
                    "items": current_group
                })
                # Replace the list with the UUID marker
                lst.string = f"__LIST_{uid}__"
        else:
            # If it's a list we don't care about (e.g. numbered list '#'), 
            # we remove it to keep the text clean, as per your original logic.
            lst.string = ""

    # 4. Generate Raw Text
    # Since we replaced elements with markers in the loops above, 
    # we just need to get the plain text now.
    try:
        raw_text = parsed.plain_text().strip()
    except AttributeError:
        raw_text = parsed.string.strip()
    except Exception as e:
        print(f"Warning: {e}")
        raw_text = ""

    return {
        "tables": tables,
        "bullets": bullet_groups,
        "infoboxes": infoboxes,
        "raw_text": raw_text
    }

# Your existing helper function (Unchanged, included for completeness)
def wikimarkup_to_html(wiki_text: str) -> str:
    def clean_link(match):
        content = match.group(1)
        if '|' in content:
            return content.split('|')[-1]
        return content
    
    wiki_text = re.sub(r'\[\[(.*?)\]\]', clean_link, wiki_text)
    wiki_text = wiki_text.replace('!!', '\n!') 
    wiki_text = wiki_text.replace('||', '\n|')

    lines = wiki_text.strip().split('\n')
    
    html_output = ['<table border="1">']
    current_row = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('{|') or line.startswith('|}'):
            continue
        if line.startswith('|-'):
            if current_row:
                html_output.append('  <tr>')
                html_output.extend(current_row)
                html_output.append('  </tr>')
                current_row = []
            continue
            
        if line.startswith('!') or line.startswith('|'):
            tag = 'th' if line.startswith('!') else 'td'
            content = line[1:]
            match = re.match(r'^([^|]+?)\|(.*)$', content)
            attrs = ""
            cell_data = content
            if match:
                possible_attrs = match.group(1)
                if '=' in possible_attrs or 'span' in possible_attrs:
                    attrs = ' ' + possible_attrs.strip()
                    cell_data = match.group(2)
            cell_data = cell_data.strip()
            current_row.append(f'    <{tag}{attrs}>{cell_data}</{tag}>')

    if current_row:
        html_output.append('  <tr>')
        html_output.extend(current_row)
        html_output.append('  </tr>')

    html_output.append('</table>')
    return '\n'.join(html_output)

def get_element_context(
    element_id: str, 
    raw_text: str, 
    window_size: int = 500, 
    before: bool = True, 
    after: bool = False
) -> str:
    """
    Locates an element by its ID within the raw text and returns the surrounding context.
    
    Args:
        element_id (str): The UUID string of the element.
        raw_text (str): The text containing markers (e.g., __TABLE_uid__).
        window_size (int): Number of characters to extract.
        before (bool): Whether to include text preceding the element.
        after (bool): Whether to include text following the element.
        
    Returns:
        str: The extracted context string, or None if ID not found.
    """
    # 1. Construct pattern to find __ANYTYPE_ID__
    # We use [A-Z]+ to match TABLE, INFOBOX, LIST, etc.
    pattern = re.compile(fr"__[A-Z]+_{re.escape(element_id)}__")
    
    match = pattern.search(raw_text)
    
    if not match:
        print(f"ID {element_id} not found in text.")
        return None

    start_pos, end_pos = match.span()
    context_parts = []

    # 2. Get 'Before' Context
    if before:
        # max(0, ...) ensures we don't wrap around to the end of the string
        clip_start = max(0, start_pos - window_size)
        pre_text = raw_text[clip_start:start_pos]
        context_parts.append(pre_text)

    # 3. Get 'After' Context
    if after:
        clip_end = min(len(raw_text), end_pos + window_size)
        post_text = raw_text[end_pos:clip_end]
        context_parts.append(post_text)

    # Join with a space if both are requested (though usually they are distinct)
    return "".join(context_parts).strip()