import os
import re
import pandas as pd
import google.generativeai as genai
from .base import LlmBase

class GeminiLlm(LlmBase):
    def __init__(self, model_name="gemini-2.5-flash"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_plot_code(self, prompt: str, df: pd.DataFrame, selected_columns: list = None) -> str:
        data_description = self._get_data_description(df, selected_columns)

        # Create example based on available columns
        example_code = "import plotly.express as px\nfig = px.scatter(df, x='column1', y='column2', title='My Scatter Plot')"
        if selected_columns and len(selected_columns) >= 2:
            example_code = f"import plotly.express as px\nfig = px.scatter(df, x='{selected_columns[0]}', y='{selected_columns[1]}', title='My Scatter Plot')"
        elif selected_columns and len(selected_columns) >= 1:
            example_code = f"import plotly.express as px\nfig = px.histogram(df, x='{selected_columns[0]}', title='My Histogram')"

        full_prompt = f"""
You are a data visualization expert. Your task is to generate Python code to create a Plotly figure based on the user's request.

**Data Description:**
The data is provided in a pandas DataFrame named `df`.
{data_description}

**User Request:**
"{prompt}"

**Instructions:**
1.  Generate Python code that creates a Plotly figure.
2.  The code should only contain the plot generation logic. Do not include any data loading or preprocessing.
3.  The final line of your code must be `fig`, which is the Plotly figure object.
4.  You can use `plotly.graph_objects` as `go` or `plotly.express` as `px`.
5.  Ensure the code is safe and does not contain any malicious operations.
6.  If working with numeric data that might contain mixed types or strings, use pd.to_numeric(errors='coerce') to clean the data.
7.  Always handle missing values appropriately using dropna() when needed.

**Example:**
```python
{example_code}
```

Your turn:
"""

        response = self.model.generate_content(full_prompt)
        return self._parse_response(response.text)

    def _get_data_description(self, df: pd.DataFrame, selected_columns: list = None) -> str:
        description = f"The DataFrame has {df.shape[0]} rows and {df.shape[1]} columns.\n"

        if selected_columns:
            description += f"The user has selected the following columns: {', '.join(selected_columns)}.\n"
            # Get info for selected columns
            with pd.option_context('display.max_colwidth', None):
                info_str = df[selected_columns].info(verbose=True)
            description += f"Column details:\n{info_str}"

        else:
            # Get info for all columns
            with pd.option_context('display.max_colwidth', None):
                info_str = df.info(verbose=True)
            description += f"Column details:\n{info_str}"

        return description

    def _parse_response(self, response_text: str) -> str:
        # The response might be in a markdown block, so we need to extract the code
        code_match = re.search(r"```python\n(.*)\n```", response_text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        return response_text.strip()
