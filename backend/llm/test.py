import pandas as pd
from .base import LlmBase

class TestLlm(LlmBase):
    def generate_plot_code(self, prompt: str, df: pd.DataFrame, selected_columns: list = None) -> str:
        """
        A test LLM that generates simple plots based on common patterns in prompts.
        """
        prompt_lower = prompt.lower()
        
        # Check if it's asking for correlation
        if 'correlation' in prompt_lower:
            # Look for column names in the prompt
            available_cols = df.columns.tolist()
            energy_cols = [col for col in available_cols if 'energy' in col.lower()]
            sugar_cols = [col for col in available_cols if 'sugar' in col.lower()]
            
            if energy_cols and sugar_cols:
                energy_col = energy_cols[0]
                sugar_col = sugar_cols[0]
                return f"""
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Create correlation plot for Energy and Sugar
x_col = '{energy_col}'
y_col = '{sugar_col}'

# Filter out null values and ensure numeric data
clean_data = df[[x_col, y_col]].dropna()

# Convert to numeric if needed
clean_data[x_col] = pd.to_numeric(clean_data[x_col], errors='coerce')
clean_data[y_col] = pd.to_numeric(clean_data[y_col], errors='coerce')

# Remove any rows that couldn't be converted to numeric
clean_data = clean_data.dropna()

if len(clean_data) == 0:
    # No valid data
    fig = go.Figure()
    fig.add_annotation(
        text="No valid numeric data found for correlation",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16)
    )
    fig.update_layout(title="Correlation Plot - No Data")
else:
    # Create the scatter plot
    fig = go.Figure(data=go.Scatter(
        x=clean_data[x_col],
        y=clean_data[y_col],
        mode='markers',
        hovertemplate='<b>%{{x}}</b><br><b>%{{y}}</b><extra></extra>',
        marker=dict(size=8, opacity=0.7)
    ))

    fig.update_layout(
        title='Correlation between ' + x_col + ' and ' + y_col,
        xaxis_title=x_col,
        yaxis_title=y_col,
        showlegend=False
    )

    # Add correlation coefficient as annotation
    try:
        correlation = clean_data[x_col].corr(clean_data[y_col])
        fig.add_annotation(
            text="Correlation: " + f"{{correlation:.3f}}",
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            showarrow=False,
            font=dict(size=12),
            bgcolor="rgba(255,255,255,0.8)"
        )
    except:
        pass  # Skip correlation if calculation fails
"""
        
        # Default scatter plot for any other request
        if len(df.columns) >= 2:
            col1, col2 = df.columns[0], df.columns[1]
            return f"""
import plotly.express as px

fig = px.scatter(df, x='{col1}', y='{col2}', 
                title='Test Plot: {col1} vs {col2}',
                hover_data={{'{col1}': True, '{col2}': True}})
"""
        
        # Fallback if no suitable columns
        return f"""
import plotly.graph_objects as go

fig = go.Figure()
fig.add_annotation(
    text="No suitable data found for visualization",
    xref="paper", yref="paper",
    x=0.5, y=0.5,
    showarrow=False,
    font=dict(size=16)
)
fig.update_layout(title="Test LLM Response")
"""
