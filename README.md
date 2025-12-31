# Finance App - Account Balance Analyzer

A Python tool to analyze bank transactions from CSV exports with both CLI and web interface.

## Quick Start

### Web Application (Recommended)

```bash
# Install dependencies with uv
uv sync

# Run Streamlit web app
uv run streamlit run app.py
```

Then:
1. Open your browser to `http://localhost:8501`
2. Upload your CSV bank statement files
3. Configure initial balance and start date in the sidebar
4. View your financial analysis

### Command Line Analysis

```bash
# Generate static reports
uv run analyze_balance.py
```

Alternative (without uv):
```bash
pip install -r requirements.txt

# Web app
streamlit run app.py

# CLI analysis
python analyze_balance.py
```

## Features

### Web Application
- **File upload**: No need to store files locally, upload directly in the browser
- **Interactive configuration**: Set initial balance and start date in the UI
- **French language interface**: All text and formatting in French
- **Real-time analysis**: Instant updates as you change settings
- **Balance evolution chart**: Interactive Plotly visualization
- **Monthly income/expense comparison**: Green/red bar charts
- **Transaction search**: Filter transactions by description
- **Excel export**: Download your analysis with one click
- **Privacy-focused**: No data stored on server, everything processed in-memory

### CLI Analysis
- Parses French bank statement CSV files
- Generates balance over time plots (PNG)
- Exports Excel file with transactions and summary statistics
- Configurable initial balance and start date via `config.json`
- Handles multiple CSV files automatically
- Removes duplicate transactions

## Configuration (CLI only)

For the command-line tool, edit `config.json`:

```json
{
  "initial_balance": 42734.2,
  "start_date": "2025-11-01",
  "data_folder": "data",
  "output_folder": "output"
}
```

**Note**: The web application uses file upload and interactive configuration instead of `config.json`.

## Output

### Web Application
- Interactive dashboard with all visualizations
- Downloadable Excel report (generated on-demand)

### CLI Analysis
- `output/balance_plot_YYYYMMDD_to_YYYYMMDD.png` - Balance visualization
- `output/account_balances_YYYYMMDD_to_YYYYMMDD.xlsx` - Detailed Excel report

## Documentation

See `CLAUDE.MD` for detailed documentation.
