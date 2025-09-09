import pandas as pd
from .base import LlmBase

class TestLlm(LlmBase):
    def generate_plot_code(self, prompt: str, df: pd.DataFrame, selected_columns: list = None) -> str:
        if prompt == "predefined_query_for_scatter_plot":
            return f"""
import plotly.express as px
fig = px.scatter(df, x='{selected_columns[0]}', y='{selected_columns[1]}', title='Test Scatter Plot')
"""
        else:
            return "fig = None"
