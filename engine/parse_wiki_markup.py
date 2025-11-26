import wikitextparser as wtp
import json

def parse_wiki_markup(wiki_text):
    parsed = wtp.parse(wiki_text)
    
    # 1. Extract Infoboxes
    infoboxes = []
    target_templates = [
        t for t in parsed.templates 
        if t.name.strip().lower().startswith("infobox")
    ]
    
    for template in target_templates:
        data = {param.name.strip(): param.value.strip() for param in template.arguments}
        data['_template_name'] = template.name.strip()
        infoboxes.append(json.dumps(data, indent=2))

    # 2. Extract Tables
    tables = [t.string for t in parsed.tables]

    # 3. Extract Bullet Points (FIXED)
    bullet_groups = []
    for lst in parsed.get_lists():
        # Check if the raw list string starts with a bullet '*'
        # lst.string contains the full raw wikitext of the list
        if lst.string.strip().startswith('*'):
            current_group = []
            for item in lst.items:
                # item is a string of wikitext, so we parse it to remove bold/links
                text_content = wtp.parse(item).plain_text().strip()
                if text_content:
                    current_group.append(text_content)
            
            if current_group:
                bullet_groups.append(current_group)

    # 4. Generate Raw Text
    # Remove extracted elements from the AST to leave only raw text
    for t in parsed.tables:
        t.string = ""
    for t in target_templates:
        t.string = ""
    for l in parsed.get_lists():
        l.string = ""
        
    raw_text = parsed.plain_text().strip()

    return {
        "tables": tables,
        "bullets": bullet_groups,
        "infoboxes": infoboxes,
        "raw_text": raw_text
    }