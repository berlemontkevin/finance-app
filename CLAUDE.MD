# Finance App

## Project Overview
This is a personal finance application for tracking and analyzing bank transactions from CSV exports.

## Project Structure

```
finance-app/
├── data/                    # Financial data files
│   └── *.csv               # Bank transaction exports (CSV format)
├── output/                  # Generated outputs (plots, Excel files)
│   ├── balance_plot_*.png  # Balance over time visualizations
│   └── account_balances_*.xlsx  # Excel exports with transactions
├── app.py                  # Streamlit web application
├── analyze_balance.py      # CLI analysis script
├── config.json             # Configuration file
├── pyproject.toml          # Python project & dependencies (uv)
├── requirements.txt        # Python dependencies (pip fallback)
├── .gitignore             # Git ignore rules
├── README.md              # Quick start guide
└── CLAUDE.MD              # This file
```

## Data Format

The project uses CSV bank statement exports with the following structure:

**Header Information:**
- Account Number (Numéro Compte)
- Account Type (Type): CCP
- Currency (Compte tenu en): euros
- Statement Date (Date)
- Balance (Solde): Current balance in EUR

**Transaction Records:**
- Date: Transaction date (DD/MM/YYYY)
- Libellé: Transaction description
- Montant (EUROS): Amount (negative for debits, positive for credits)

### Sample Data Structure
```
Numéro Compte   ;0149272X026
Type         ;CCP
Compte tenu en  ;euros
Date            ;31/12/2025
Solde (EUROS)   ;42727,72

Date;Libellé;Montant(EUROS)
27/11/2025;"ACHAT CB CARREFOUR...";-85,54
27/11/2025;"VIREMENT DE...";2528,11
```

## Transaction Types Identified
- **ACHAT CB**: Credit card purchases
- **VIREMENT**: Bank transfers (incoming and outgoing)
- **VIREMENT INSTANTANE**: Instant transfers
- **PRELEVEMENT**: Direct debits
- **CHEQUE**: Checks

## Development Notes

### Data Considerations
- CSV files use semicolon (`;`) as delimiter
- Decimal separator is comma (`,`) - French format
- Encoding may include special characters (accented characters)
- Amounts are in EUR with 2 decimal places
- Negative amounts indicate debits/expenses
- Positive amounts indicate credits/income

### Implemented Features

**Web Application:**
- [x] File upload interface (no local file storage required)
- [x] Interactive configuration (initial balance, start date)
- [x] Real-time analysis with instant updates
- [x] French language interface
- [x] Balance evolution chart (interactive Plotly)
- [x] Monthly income/expense bar charts (green/red)
- [x] Transaction search functionality
- [x] Excel export (download button)
- [x] Privacy-focused (in-memory processing only)

**CLI Tool:**
- [x] CSV parser for bank statement imports
- [x] Balance history visualization (PNG plots)
- [x] Export to Excel with transactions and summary
- [x] Multi-file support (processes all CSV files in data folder)
- [x] Configuration file for customization (`config.json`)
- [x] Date filtering by start date
- [x] Duplicate transaction detection

### Potential Future Features
- [ ] Transaction categorization (groceries, utilities, transfers, etc.)
- [ ] Monthly/yearly expense tracking
- [ ] Income vs. expense analysis with charts
- [ ] Budget tracking
- [ ] Recurring transaction detection
- [ ] Multi-account support

### Privacy & Security
- Bank statement data contains sensitive personal information
- Data files should be in `.gitignore`
- Consider encryption for stored data
- Do not commit actual transaction data to version control

## Getting Started

### Installation

1. Install Python dependencies using `uv` (recommended):
```bash
# Install dependencies
uv pip install -e .

# Or sync dependencies
uv sync
```

Or using traditional pip:
```bash
pip install -r requirements.txt
```

2. Configure your initial balance in `config.json`:
```json
{
  "initial_balance": 0.0,  // Set your starting balance here
  ...
}
```

3. Place your bank statement CSV files in the `data/` folder

4. Run the application:

**Option A: Web Application (Recommended)**
```bash
# With uv
uv run streamlit run app.py

# Or without uv
streamlit run app.py
```
Then open your browser to `http://localhost:8501` and:
1. Upload your CSV bank statement files
2. Set your initial balance (e.g., 42734.2 for balance on 01/11/2025)
3. Optionally enable date filtering and set start date (e.g., 01/11/2025)
4. View your analysis in real-time

**Note**: The web app does NOT use `config.json`. All settings are configured through the UI.

**Option B: CLI Analysis**
```bash
# With uv
uv run analyze_balance.py

# Or without uv
python analyze_balance.py
```
This will use settings from `config.json` (initial_balance: 42734.2, start_date: "2025-11-01")

### Output

**Web Application:**
- Interactive French-language dashboard
- Real-time balance evolution chart
- Monthly income/expense comparison (green/red bars)
- Transaction table with search
- Key metrics display (solde initial, solde final, revenus, dépenses)
- Excel export via download button (generated on-demand, not saved to disk)

**How to use:**
- Upload CSV files in the sidebar
- Configure initial balance and start date in the UI
- All processing happens in-memory
- No data is stored on the server

**CLI Analysis generates (saved to disk):**
- **PNG plots**:
  - `output/balance_plot_YYYYMMDD_to_YYYYMMDD.png` (with transaction date range)
  - `output/balance_plot_latest.png` (always points to most recent)
  - Plot title includes date range from earliest to latest transaction
- **Excel files**:
  - `output/account_balances_YYYYMMDD_to_YYYYMMDD.xlsx` (with transaction date range)
  - `output/account_balances_latest.xlsx` (always points to most recent)
  - Contains two sheets:
    - Transactions: Complete transaction history with running balance
    - Summary: Key metrics (total income, expenses, etc.)
- **Duplicate detection**: Automatically removes duplicate transactions when processing multiple CSV files

### Configuration

Edit `config.json` to customize:
- `initial_balance`: Starting balance before first transaction
- `start_date`: Optional start date to filter transactions (format: "YYYY-MM-DD", e.g., "2025-11-01")
  - Only transactions on or after this date will be included
  - Useful for starting analysis from a specific date
- `data_folder`: Location of CSV files (default: "data")
- `output_folder`: Where to save outputs (default: "output")
- `plot_settings`: Chart customization (size, title, labels, grid)

Example configuration:
```json
{
  "initial_balance": 0.0,
  "start_date": "2025-11-01",
  "data_folder": "data",
  "output_folder": "output"
}
```

### Adding New Data

The application is designed to handle updates:
1. Add new CSV files to the `data/` folder
2. Re-run `python analyze_balance.py`
3. The script will process all CSV files and remove duplicates automatically

## Future Enhancements
- Dashboard for financial overview
- Category management and custom rules
- Search and filter transactions
- Export reports (PDF, CSV, JSON)
- Multi-currency support
- Bank account reconciliation
- Interactive plots with zoom/pan capabilities
