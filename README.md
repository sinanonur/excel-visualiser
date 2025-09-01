# Excel Data Science Visualizer

A comprehensive web-based tool for exploring and visualizing Excel datasets with automatic data type detection, list/set column expansion, and interactive plotting capabilities.

## Features

### 🔍 **Data Exploration**
- Upload Excel files (.xlsx, .xls) through drag-and-drop interface
- Automatic data type detection (numeric, categorical, text, datetime, boolean)
- Data preview with pagination
- Column statistics and information

### 📋 **Smart List/Set Detection**
- Automatically detects columns containing lists `[item1, item2, ...]` or sets `{item1, item2, ...}`
- Expand list/set columns into separate columns for detailed analysis
- Supports complex nested data structures

### 🔍 **Advanced Data Filtering**
- **Categorical Filters**: Select specific categories to include
- **Numeric Filters**: Set min/max thresholds with interactive sliders
- **Text Filters**: Filter by text content or regular expressions
- **Boolean Filters**: Filter by true/false values
- **Real-time Filter Status**: See filtered vs. total row counts
- **Multiple Filters**: Apply multiple filters simultaneously

### 📊 **Interactive Visualizations**
- **Violin Plots**: Distribution shape for numeric data
- **Histograms**: Distribution of numeric data
- **Box Plots**: Statistical summaries (single or grouped by category)
- **Bar Charts**: Categorical data (single or stacked/grouped)
- **Scatter Plots**: Relationships between numeric variables
- **Filter-Aware Plotting**: All visualizations respect active filters

### 🛠 **Column Management**
- Manual data type override
- Column expansion for list/set data
- Real-time column statistics
- Type-aware visualization suggestions

## 🚀 Quick Installation

Choose your operating system:

| Platform | Command |
|----------|---------|
| **Linux** | `chmod +x install-linux.sh && ./install-linux.sh` |
| **macOS** | `chmod +x install-macos.sh && ./install-macos.sh` |
| **Windows** | Double-click `install-windows.bat` |

### ▶️ Start the Application

| Platform | Command |
|----------|---------|
| **Linux/macOS** | `./run.sh start` |
| **Windows** | Double-click `run.bat` |

**🌐 Access**: http://localhost:3000 (opens automatically)

**📖 Need help?** See [QUICK_START.md](QUICK_START.md) or [INSTALLATION.md](INSTALLATION.md)

---

## Manual Installation (Advanced Users)

<details>
<summary>Click to expand manual installation steps</summary>

### Prerequisites
- Python 3.7+
- Node.js 14+
- 4GB RAM (8GB recommended)

### Backend Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate.bat # Windows

# Install dependencies
pip install -r requirements.txt

# Start backend
cd backend
python app.py
```

### Frontend Setup
```bash
# Install dependencies
npm install

# Start frontend
npm start
```

</details>

## Usage

1. **Start the Application**
   - Run the backend: `python start_backend.py` (runs on http://localhost:5001)
   - Run the frontend: `./start_frontend.sh` (runs on http://localhost:3000)
   - Open your browser to `http://localhost:3000`

2. **Upload Your Excel File**
   - Drag and drop your .xlsx or .xls file
   - The system will automatically detect column types and list structures

3. **Explore Your Data**
   - **Data Preview**: View your data with column type indicators
   - **Column Management**: Adjust data types and expand list columns
   - **Filters**: Apply advanced filters to focus on specific data subsets
   - **Visualizations**: Create interactive plots based on your (filtered) data

4. **Filter Your Data (Optional)**
   - Navigate to the "Filters" tab
   - Set categorical selections, numeric ranges, or text patterns
   - Apply filters and see real-time row count updates
   - Clear individual filters or all filters at once

5. **Generate Visualizations**
   - Select appropriate plot types based on your column data types
   - Choose columns for visualization
   - Configure plot options (e.g., stacked vs. grouped bar charts)

## Data Type Detection

The system automatically detects:
- **Numeric**: Integer and floating-point numbers
- **Categorical**: Limited unique values or small unique ratio
- **Text**: High variability text data
- **DateTime**: Date and time formats
- **Boolean**: True/false values
- **Lists/Sets**: Columns containing `[...]` or `{...}` formatted data

## List/Set Column Expansion

When the system detects columns containing list or set data (e.g., `[apple, banana, cherry]`), you can expand them into separate columns:
- Each item in the list becomes a new column
- Original column structure is preserved
- Supports both Python list `[...]` and set `{...}` formats

## API Endpoints

### Backend API (Flask)
- `POST /upload`: Upload and process Excel files
- `GET /column-info`: Get current column information
- `POST /update-column-type`: Update column data type
- `POST /expand-column`: Expand list/set columns
- `GET /filter-options/<column>`: Get filtering options for a column
- `POST /apply-filters`: Apply filters to the dataset
- `POST /clear-filters`: Clear all active filters
- `GET /filter-status`: Get current filter status
- `POST /plot`: Generate interactive plots (respects active filters)
- `GET /data-preview`: Get paginated data preview (respects active filters)

## Technology Stack

### Backend
- **Flask**: Web framework
- **Pandas**: Data processing and analysis
- **Plotly**: Interactive plotting
- **OpenPyXL**: Excel file processing
- **NumPy**: Numerical computations

### Frontend
- **React**: User interface
- **Material-UI**: Component library
- **Plotly.js**: Interactive plotting
- **Axios**: HTTP client
- **React Dropzone**: File upload

## Project Structure

```
excel-visualiser/
├── backend/
│   └── app.py              # Flask API server
├── src/
│   ├── components/
│   │   ├── FileUpload.js   # File upload component
│   │   ├── DataPreview.js  # Data preview table
│   │   ├── ColumnManager.js # Column type management
│   │   └── PlotGenerator.js # Visualization interface
│   ├── App.js              # Main application component
│   ├── index.js            # Application entry point
│   └── index.css           # Global styles
├── public/
│   └── index.html          # HTML template
├── requirements.txt        # Python dependencies
├── package.json           # Node.js dependencies
├── start_backend.py       # Backend startup script
└── start_frontend.sh      # Frontend startup script
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Troubleshooting

### Common Issues

**Backend won't start**
- Ensure Python 3.7+ is installed
- Check if all requirements are installed: `pip install -r requirements.txt`
- Verify port 5000 is available

**Frontend won't start**
- Ensure Node.js 14+ is installed
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check if port 3000 is available

**File upload fails**
- Ensure the file is a valid Excel format (.xlsx, .xls)
- Check file size limits
- Verify backend server is running

**Plots not generating**
- Ensure selected columns match the plot type requirements
- Check column data types are correctly detected
- Verify backend API is accessible