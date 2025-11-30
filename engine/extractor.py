import pandas as pd
from typing import Optional, Dict, List
from io import StringIO
import json


class WikiTableExtractor:
    def __init__(self, llm_client_func):
        self.llm_client = llm_client_func

    def _get_table_context(self, table_df: pd.DataFrame, caption: str) -> str:
        """Creates a lightweight string representation for the LLM."""
        headers = list(table_df.columns)
        sample_row = table_df.head(1).values.tolist()
        return json.dumps({
            "table_caption": caption,
            "headers": headers,
            "first_row_sample": sample_row
        })

    @profile  # <--- PROFILING POINT 1: Measures LLM Metadata Analysis time
    def analyze_table_metadata(self, context_str: str) -> Optional[Dict]:
        """
        Step 1 & 2: Determine if table is relevant and map columns.
        """
        system_prompt = """
        You are a data extraction assistant. Analyze the table metadata.
        1. Determine if this table lists REAL PEOPLE.
        2. Identify the best columns for 'person_name', 'location', and 'year'.
        3. If location/year are not in columns, check the table_caption.
        
        Output JSON ONLY:
        {
            "is_people_table": boolean,
            "mappings": {
                "person_name": "exact_column_name_or_null",
                "location": "exact_column_name_or_constant_value_from_caption",
                "year": "exact_column_name_or_constant_value_from_caption"
            }
        }
        """
        
        response = self.llm_client(system_prompt, context_str)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return None

    @profile  # <--- PROFILING POINT 2: Measures LLM Verification time
    def verify_extraction(self, sample_data: List[Dict]) -> bool:
        """
        Step 4: Verify a 3-row sample.
        """
        system_prompt = """
        Verify if these 3 rows represent valid (Person, Location, Year) extraction.
        Return JSON: {"valid": true/false}
        """
        response = self.llm_client(system_prompt, json.dumps(sample_data))
        try:
            return json.loads(response).get("valid", False)
        except:
            return False

    @profile  # <--- PROFILING POINT 3: Measures Pandas operations vs LLM wait time
    def process_page_html(self, html_content: str) -> pd.DataFrame:
        """
        Main pipeline logic.
        """
        try:
            # Profiler will show if reading HTML is a bottleneck
            tables = pd.read_html(StringIO(html_content), keep_default_na=False)
        except ValueError:
            return pd.DataFrame() 

        all_extracted_people = []

        for i, df in enumerate(tables):
            df = df.dropna(how='all')
            caption = f"Table {i}" 

            # --- LLM STEP 1 & 2 ---
            context = self._get_table_context(df, caption)
            analysis = self.analyze_table_metadata(context) # This line will likely show high % time

            if not analysis or not analysis.get("is_people_table"):
                continue

            mappings = analysis.get("mappings", {})
            col_name = mappings.get("person_name")
            col_loc = mappings.get("location")
            col_year = mappings.get("year")

            if not col_name:
                continue

            # --- PANDAS STEP 3 ---
            temp_df = pd.DataFrame()
            
            # Profiler will confirm these operations are near-instant
            if col_name in df.columns:
                temp_df['person_name'] = df[col_name]
            else:
                continue 

            if col_loc in df.columns:
                temp_df['location'] = df[col_loc]
            else:
                temp_df['location'] = col_loc 

            if col_year in df.columns:
                temp_df['year'] = df[col_year]
            else:
                temp_df['year'] = col_year

            # --- LLM STEP 4 ---
            if len(temp_df) > 0:
                sample = temp_df.head(3).to_dict(orient='records')
                # This line will show the verification cost
                if self.verify_extraction(sample):
                    all_extracted_people.append(temp_df)

        if all_extracted_people:
            return pd.concat(all_extracted_people, ignore_index=True)
        return pd.DataFrame(columns=['person_name', 'location', 'year'])