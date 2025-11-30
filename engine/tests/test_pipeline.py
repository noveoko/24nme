import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import json
import requests
from io import StringIO


# Import your code here. Assuming your file is named 'pipeline.py'
# from pipeline import WikiTableExtractor, clean_llm_json, call_ollama

from engine.llm import clean_json_response, call_ollama
from engine.extractor import WikiTableExtractor

# If you are pasting this in the same file as the code, ignore the import above.

# ==========================================
# 1. TEST HELPER FUNCTIONS
# ==========================================
class TestHelpers(unittest.TestCase):
    def test_clean_llm_json(self):
        # Case A: Pure JSON
        raw = '{"key": "value"}'
        self.assertEqual(clean_llm_json(raw), raw)

        # Case B: Markdown block
        md = '```json\n{"key": "value"}\n```'
        self.assertEqual(clean_llm_json(md), '{"key": "value"}')

        # Case C: Markdown without "json" label
        md_plain = '```\n[1, 2, 3]\n```'
        self.assertEqual(clean_llm_json(md_plain), '[1, 2, 3]')

        # Case D: Surrounding text (Chatty LLM)
        chatty = "Here is your JSON:\n```json\n{\"a\": 1}\n```\nHope that helps!"
        self.assertEqual(clean_llm_json(chatty), '{"a": 1}')


# ==========================================
# 2. TEST OLLAMA CLIENT (INFRASTRUCTURE)
# ==========================================
class TestOllamaClient(unittest.TestCase):
    @patch('requests.post')
    def test_call_ollama_success(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": '```json\n{"success": true}\n```'}
        }
        mock_post.return_value = mock_response

        result = call_ollama("sys", "user")
        self.assertEqual(result, '{"success": true}')
        
        # Verify timeout was set to 120 as per your code
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['timeout'], 120)

    @patch('requests.post')
    def test_call_ollama_timeout(self, mock_post):
        # Simulate ReadTimeout
        mock_post.side_effect = requests.exceptions.ReadTimeout("Timeout")
        
        result = call_ollama("sys", "user")
        self.assertEqual(result, "{}") # Should return empty JSON string on error

    @patch('requests.post')
    def test_call_ollama_connection_error(self, mock_post):
        # Simulate ConnectionError
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection Refused")
        
        result = call_ollama("sys", "user")
        self.assertEqual(result, "{}")


# ==========================================
# 3. TEST CORE PIPELINE (LOGIC)
# ==========================================
class SmartMockLLM:
    """
    Deterministcally simulates the LLM based on input headers.
    """
    def __call__(self, system_prompt, user_content):
        # 1. Handle Verification Step (Step 4)
        if "Verify if these 3 rows" in system_prompt:
            # We assume for testing that data passed to verification is valid
            # unless we specifically inject a "Bad" record if needed.
            return '{"valid": true}'

        # 2. Handle Metadata Analysis Step (Step 1 & 2)
        try:
            data = json.loads(user_content)
            headers = [h.lower() for h in data.get('headers', [])]
            caption = data.get('table_caption', '')

            # Scenario: Explicit People Table
            if 'full name' in headers:
                return json.dumps({
                    "is_people_table": True,
                    "mappings": {
                        "person_name": "Full Name",
                        "location": "Birth Place",
                        "year": "Born"
                    }
                })

            # Scenario: Constant Value (Location in Caption)
            if 'artist' in headers:
                return json.dumps({
                    "is_people_table": True,
                    "mappings": {
                        "person_name": "Artist",
                        "location": "Paris", # Constant
                        "year": "Period"
                    }
                })

            # Scenario: Not a Person Table
            if 'model' in headers and 'engine' in headers:
                return json.dumps({
                    "is_people_table": False,
                    "mappings": {}
                })

            # Default: Empty/Fail
            return '{"is_people_table": false}'

        except Exception:
            return '{}'


class TestWikiTableExtractor(unittest.TestCase):
    def setUp(self):
        self.mock_llm = SmartMockLLM()
        self.extractor = WikiTableExtractor(self.mock_llm)

    def test_process_standard_table(self):
        """Test a standard table where columns map 1:1"""
        html = """
        <table>
            <thead><tr><th>Full Name</th><th>Birth Place</th><th>Born</th></tr></thead>
            <tbody>
                <tr><td>John Doe</td><td>New York</td><td>1980</td></tr>
                <tr><td>Jane Doe</td><td>London</td><td>1985</td></tr>
            </tbody>
        </table>
        """
        df = self.extractor.process_page_html(html)
        
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 2)
        self.assertIn('person_name', df.columns)
        self.assertEqual(df.iloc[0]['person_name'], 'John Doe')
        self.assertEqual(df.iloc[0]['location'], 'New York')

    def test_process_constant_value_mapping(self):
        """Test when LLM says location is a constant string (not a column)"""
        html = """
        <table>
            <caption>French Painters</caption>
            <thead><tr><th>Artist</th><th>Period</th></tr></thead>
            <tbody>
                <tr><td>Monet</td><td>19th Century</td></tr>
            </tbody>
        </table>
        """
        df = self.extractor.process_page_html(html)
        
        self.assertFalse(df.empty)
        self.assertEqual(df.iloc[0]['person_name'], 'Monet')
        # Check that the constant value was applied
        self.assertEqual(df.iloc[0]['location'], 'Paris') 

    def test_filter_irrelevant_table(self):
        """Test that non-people tables are discarded"""
        html = """
        <table>
            <thead><tr><th>Model</th><th>Engine</th><th>HP</th></tr></thead>
            <tbody>
                <tr><td>Ford</td><td>V8</td><td>300</td></tr>
            </tbody>
        </table>
        """
        df = self.extractor.process_page_html(html)
        self.assertTrue(df.empty, "Should return empty DF for cars table")

    def test_handle_malformed_html(self):
        """Test resilience against bad HTML"""
        html = "<html><body>Not a table</body></html>"
        # The code catches ValueError from pd.read_html
        df = self.extractor.process_page_html(html)
        self.assertTrue(df.empty)

    def test_no_valid_columns_found(self):
        """Test case where LLM returns True but mapping fails (e.g. column missing)"""
        # Inject a dumb mock that returns a column that doesn't exist
        def dumb_mock(sys, user):
            return json.dumps({
                "is_people_table": True,
                "mappings": {"person_name": "Ghost Column", "location": "X", "year": "Y"}
            })
        
        bad_extractor = WikiTableExtractor(dumb_mock)
        html = "<table><thead><tr><th>Real Name</th></tr><tbody><tr><td>A</td></tr></tbody></table>"
        
        df = bad_extractor.process_page_html(html)
        self.assertTrue(df.empty, "Should filter out if mapped column is missing")

# Run tests
if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)