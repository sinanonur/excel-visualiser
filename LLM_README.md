# LLM Custom Graph Generation

This feature allows users to generate custom visualizations using natural language prompts with AI models.

## Features

- **Test Model**: Fast, reliable built-in model for basic correlation plots
- **Gemini 2.5 Flash**: Advanced AI model for complex visualizations
- **Data Cleaning**: Automatic handling of mixed data types and malformed values
- **Interactive Plots**: Generated plots are fully interactive with hover information

## Usage

1. Upload your Excel file with data
2. Go to Plot Generator
3. Select "🤖 Custom Graph (AI)"
4. Choose your AI model (Test Model or Gemini 2.5 Flash)
5. Enter a natural language prompt like:
   - "Create a correlation graph for Energy and Sugar"
   - "Make a scatter plot showing the relationship between Price and Quality"
6. Click "Generate Plot"

## Technical Details

### Models

- **TestLlm**: Built-in model that handles common plot types with robust data cleaning
- **GeminiLlm**: Uses Google's Gemini API for advanced plot generation

### Data Handling

Both models automatically:
- Clean malformed data (e.g., "26,6," → NaN)
- Convert mixed data types to numeric where possible
- Handle missing values appropriately
- Provide fallback plots when data issues occur

### Error Handling

The system includes comprehensive error handling:
- Data type validation
- API error handling
- Malformed code detection
- User-friendly error messages

## Testing

Run the basic test to verify functionality:
```bash
python test_llm_basic.py
```