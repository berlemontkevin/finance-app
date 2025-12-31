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
- Interactive dashboard in French
- Date range filtering
- Balance evolution chart
- Monthly income/expense comparison (green/red bars)
- Transaction search and filtering
- Responsive design

### CLI Analysis
- Parses French bank statement CSV files
- Generates balance over time plots
- Exports Excel file with transactions and summary statistics
- Configurable initial balance
- Handles multiple CSV files automatically
- Removes duplicate transactions

## Configuration

Edit `config.json` to set your initial balance:

```json
{
  "initial_balance": 0.0
}
```

## Output

- `output/balance_plot_latest.png` - Balance visualization
- `output/account_balances_latest.xlsx` - Detailed Excel report

## Documentation

See `CLAUDE.MD` for detailed documentation.
