import unittest
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.app import app, data_processor
from backend.llm.test import TestLlm

class TestLlmPlot(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Create a sample dataframe
        self.df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': [5, 4, 3, 2, 1]
        })
        data_processor.data = self.df
        data_processor.original_data = self.df
        data_processor.column_info = {
            'col1': {'type': 'numeric'},
            'col2': {'type': 'numeric'}
        }

    def test_generate_llm_plot_with_test_model(self):
        # Use the test model to generate a plot
        response = self.app.post('/generate-llm-plot',
                                 json={
                                     'prompt': 'predefined_query_for_scatter_plot',
                                     'columns': ['col1', 'col2'],
                                     'model': 'test'
                                 })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('plot', data)

        # Check if the plot data contains the expected title
        import json
        plot_data = json.loads(data['plot'])
        self.assertEqual(plot_data['layout']['title']['text'], 'Test Scatter Plot')

if __name__ == '__main__':
    unittest.main()
