"""
Wiki Markup to Linked List Converter

Parses wiki markup files and creates a doubly-linked list structure
where each chunk (heading, paragraph, table, list, etc.) is connected
to its neighbors for easy traversal.
"""

import re
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class ContentChunk:
    """Represents a single chunk of content in the wiki document."""
    chunk_type: str  # 'heading', 'paragraph', 'table', 'list', 'code', etc.
    content: str
    level: Optional[int] = None  # For headings (1-6) or list nesting
    metadata: dict = field(default_factory=dict)
    
    # Linked list pointers
    prev: Optional['ContentChunk'] = None
    next: Optional['ContentChunk'] = None
    
    def __repr__(self):
        preview = self.content[:50].replace('\n', ' ')
        return f"ContentChunk(type={self.chunk_type}, content='{preview}...')"


class WikiLinkedList:
    """
    A linked list structure for wiki markup content.
    Provides easy navigation between content chunks.
    """
    
    def __init__(self):
        self.head: Optional[ContentChunk] = None
        self.tail: Optional[ContentChunk] = None
        self.size: int = 0
        self._all_chunks: List[ContentChunk] = []
    
    def append(self, chunk: ContentChunk) -> ContentChunk:
        """Add a chunk to the end of the linked list."""
        if not self.head:
            self.head = chunk
            self.tail = chunk
        else:
            self.tail.next = chunk
            chunk.prev = self.tail
            self.tail = chunk
        
        self.size += 1
        self._all_chunks.append(chunk)
        return chunk
    
    def get_chunk_before(self, chunk: ContentChunk) -> Optional[ContentChunk]:
        """Get the chunk immediately before the given chunk."""
        return chunk.prev
    
    def get_chunk_after(self, chunk: ContentChunk) -> Optional[ContentChunk]:
        """Get the chunk immediately after the given chunk."""
        return chunk.next
    
    def find_chunks_by_type(self, chunk_type: str) -> List[ContentChunk]:
        """Find all chunks of a specific type."""
        return [c for c in self._all_chunks if c.chunk_type == chunk_type]
    
    def get_context(self, chunk: ContentChunk, before: int = 1, after: int = 1) -> dict:
        """
        Get surrounding context for a chunk.
        Returns a dict with 'before', 'current', and 'after' lists.
        """
        context = {
            'before': [],
            'current': chunk,
            'after': []
        }
        
        # Get chunks before
        current = chunk.prev
        for _ in range(before):
            if current:
                context['before'].insert(0, current)
                current = current.prev
        
        # Get chunks after
        current = chunk.next
        for _ in range(after):
            if current:
                context['after'].append(current)
                current = current.next
        
        return context
    
    def to_list(self) -> List[ContentChunk]:
        """Convert linked list to regular Python list."""
        return self._all_chunks
    
    def __iter__(self):
        """Allow iteration over chunks."""
        current = self.head
        while current:
            yield current
            current = current.next
    
    def __len__(self):
        return self.size


class WikiMarkupParser:
    """
    Parses wiki markup (MediaWiki syntax) into content chunks.
    """
    
    def __init__(self):
        # Patterns for different wiki markup elements
        self.patterns = {
            'heading': re.compile(r'^(={1,6})\s*(.*?)\s*\1\s*$', re.MULTILINE),
            'table_start': re.compile(r'^\{\|', re.MULTILINE),
            'table_end': re.compile(r'^\|\}', re.MULTILINE),
            'infobox_start': re.compile(r'\{\{[Ii]nfobox', re.MULTILINE),
            'template_start': re.compile(r'\{\{', re.MULTILINE),
            'list_item': re.compile(r'^([*#:;]+)\s*(.*)$', re.MULTILINE),
            'code_block': re.compile(r'<pre>(.*?)</pre>', re.DOTALL),
            'horizontal_rule': re.compile(r'^----+\s*$', re.MULTILINE),
        }
    
    def parse_file(self, filepath: str) -> WikiLinkedList:
        """Parse a wiki markup file and return a linked list structure."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_string(content)
    
    def parse_string(self, content: str) -> WikiLinkedList:
        """Parse wiki markup string and return a linked list structure."""
        linked_list = WikiLinkedList()
        
        # Split content into lines for processing
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for headings
            heading_match = self.patterns['heading'].match(line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                chunk = ContentChunk(
                    chunk_type='heading',
                    content=text,
                    level=level,
                    metadata={'raw': line}
                )
                linked_list.append(chunk)
                i += 1
                continue
            
            # Check for infobox (must check before general table)
            if self.patterns['infobox_start'].match(line):
                infobox_content, end_idx, infobox_data = self._extract_infobox(lines, i)
                chunk = ContentChunk(
                    chunk_type='infobox',
                    content=infobox_content,
                    metadata={
                        'infobox_type': infobox_data.get('type', 'unknown'),
                        'fields': infobox_data.get('fields', {}),
                        'field_count': len(infobox_data.get('fields', {}))
                    }
                )
                linked_list.append(chunk)
                i = end_idx + 1
                continue
            
            # Check for table start
            if self.patterns['table_start'].match(line):
                table_content, end_idx = self._extract_table(lines, i)
                chunk = ContentChunk(
                    chunk_type='table',
                    content=table_content,
                    metadata={'row_count': table_content.count('|-')}
                )
                linked_list.append(chunk)
                i = end_idx + 1
                continue
            
            # Check for list items
            list_match = self.patterns['list_item'].match(line)
            if list_match:
                list_content, end_idx = self._extract_list(lines, i)
                chunk = ContentChunk(
                    chunk_type='list',
                    content=list_content,
                    level=len(list_match.group(1)),
                    metadata={'list_type': list_match.group(1)[0]}
                )
                linked_list.append(chunk)
                i = end_idx + 1
                continue
            
            # Check for horizontal rule
            if self.patterns['horizontal_rule'].match(line):
                chunk = ContentChunk(
                    chunk_type='horizontal_rule',
                    content='----'
                )
                linked_list.append(chunk)
                i += 1
                continue
            
            # Check for empty lines (section breaks)
            if not line.strip():
                i += 1
                continue
            
            # Otherwise, treat as paragraph
            para_content, end_idx = self._extract_paragraph(lines, i)
            if para_content.strip():
                chunk = ContentChunk(
                    chunk_type='paragraph',
                    content=para_content
                )
                linked_list.append(chunk)
            i = end_idx + 1
        
        return linked_list
    
    def _extract_table(self, lines: List[str], start_idx: int) -> tuple:
        """Extract a complete table from the lines."""
        table_lines = [lines[start_idx]]
        i = start_idx + 1
        
        while i < len(lines):
            table_lines.append(lines[i])
            if self.patterns['table_end'].match(lines[i]):
                break
            i += 1
        
        return '\n'.join(table_lines), i
    
    def _extract_infobox(self, lines: List[str], start_idx: int) -> tuple:
        """
        Extract a complete infobox template from the lines.
        Returns: (raw_content, end_idx, parsed_data)
        
        Infoboxes use nested braces {{ }}, so we need to track brace depth.
        """
        infobox_lines = [lines[start_idx]]
        i = start_idx
        
        # Count opening braces in first line
        brace_depth = lines[start_idx].count('{{') - lines[start_idx].count('}}')
        i += 1
        
        # Continue until braces are balanced
        while i < len(lines) and brace_depth > 0:
            line = lines[i]
            infobox_lines.append(line)
            brace_depth += line.count('{{') - line.count('}}')
            i += 1
        
        raw_content = '\n'.join(infobox_lines)
        
        # Parse the infobox fields
        parsed_data = self._parse_infobox_fields(raw_content)
        
        return raw_content, i - 1, parsed_data
    
    def _parse_infobox_fields(self, infobox_content: str) -> dict:
        """
        Parse infobox content to extract structured data.
        Returns a dict with 'type' and 'fields'.
        """
        result = {
            'type': 'unknown',
            'fields': {}
        }
        
        # Extract infobox type (e.g., "Infobox person", "Infobox company")
        type_match = re.match(r'\{\{[Ii]nfobox\s+([^|\n]+)', infobox_content)
        if type_match:
            result['type'] = type_match.group(1).strip()
        
        # Extract field-value pairs
        # Pattern: | field_name = value
        field_pattern = re.compile(r'^\|\s*([^=\n]+?)\s*=\s*(.*)$', re.MULTILINE)
        
        for match in field_pattern.finditer(infobox_content):
            field_name = match.group(1).strip()
            field_value = match.group(2).strip()
            
            # Handle multi-line values (collect until next | or }})
            if field_value:
                result['fields'][field_name] = field_value
        
        return result
    
    def _extract_list(self, lines: List[str], start_idx: int) -> tuple:
        """Extract a complete list (potentially nested) from the lines."""
        list_lines = []
        i = start_idx
        
        while i < len(lines):
            if self.patterns['list_item'].match(lines[i]):
                list_lines.append(lines[i])
                i += 1
            else:
                break
        
        return '\n'.join(list_lines), i - 1
    
    def _extract_paragraph(self, lines: List[str], start_idx: int) -> tuple:
        """Extract a paragraph (consecutive non-empty lines)."""
        para_lines = []
        i = start_idx
        
        while i < len(lines):
            line = lines[i]
            # Stop at empty line, heading, table, or list
            if (not line.strip() or 
                self.patterns['heading'].match(line) or
                self.patterns['table_start'].match(line) or
                self.patterns['list_item'].match(line) or
                self.patterns['horizontal_rule'].match(line)):
                break
            para_lines.append(line)
            i += 1
        
        return '\n'.join(para_lines), i - 1


# Example usage and helper functions
def demo_usage():
    """Demonstrate how to use the wiki markup linked list."""
    
    # Sample wiki markup with infobox
    sample_wiki = """
{{Infobox person
| name = John Doe
| birth_date = January 1, 1980
| occupation = Software Engineer
| nationality = American
| website = {{URL|example.com}}
}}

== Introduction ==

This is a paragraph of text explaining the topic.
It continues on multiple lines.

=== Subsection ===

Another paragraph here.

{|
! Header 1 !! Header 2
|-
| Cell 1 || Cell 2
|-
| Cell 3 || Cell 4
|}

After the table, we have more text.

* List item 1
* List item 2
** Nested item

== Conclusion ==

Final thoughts go here.
"""
    
    # Parse the wiki markup
    parser = WikiMarkupParser()
    wiki_list = parser.parse_string(sample_wiki)
    
    print(f"Parsed {len(wiki_list)} chunks\n")
    
    # Find and display infoboxes
    infoboxes = wiki_list.find_chunks_by_type('infobox')
    if infoboxes:
        print("=" * 60)
        print("INFOBOX FOUND")
        print("=" * 60)
        infobox = infoboxes[0]
        print(f"Type: {infobox.metadata['infobox_type']}")
        print(f"Number of fields: {infobox.metadata['field_count']}")
        print("\nFields:")
        for field_name, field_value in infobox.metadata['fields'].items():
            print(f"  {field_name}: {field_value}")
        
        # Get the chunk after the infobox
        print("\n" + "-" * 60)
        print("Chunk after infobox:")
        after = wiki_list.get_chunk_after(infobox)
        if after:
            print(f"  Type: {after.chunk_type}")
            print(f"  Content: {after.content[:50]}...")
        print()
    
    # Find all tables
    tables = wiki_list.find_chunks_by_type('table')
    if tables:
        print("=" * 60)
        print("TABLE FOUND")
        print("=" * 60)
        table = tables[0]
        print(f"Row count: {table.metadata['row_count']}\n")
        
        # Get the chunk before and after the table
        print("Chunk before table:")
        before = wiki_list.get_chunk_before(table)
        if before:
            print(f"  Type: {before.chunk_type}")
            print(f"  Content: {before.content[:50]}...\n")
        
        print("Chunk after table:")
        after = wiki_list.get_chunk_after(table)
        if after:
            print(f"  Type: {after.chunk_type}")
            print(f"  Content: {after.content[:50]}...\n")
        
        # Get broader context (2 chunks before and after)
        context = wiki_list.get_context(table, before=2, after=2)
        print("Context (2 chunks before and after):")
        print(f"  Before: {len(context['before'])} chunks")
        print(f"  After: {len(context['after'])} chunks")
        print()
    
    # Iterate through all chunks
    print("=" * 60)
    print("ALL CHUNKS IN ORDER")
    print("=" * 60)
    for i, chunk in enumerate(wiki_list, 1):
        content_preview = chunk.content[:40].replace('\n', ' ')
        print(f"{i}. {chunk.chunk_type:12} | {content_preview}...")
        if chunk.chunk_type == 'infobox':
            print(f"   └─ Type: {chunk.metadata['infobox_type']}, "
                  f"Fields: {chunk.metadata['field_count']}")


if __name__ == '__main__':
    demo_usage()