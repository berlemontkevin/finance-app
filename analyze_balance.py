#!/usr/bin/env python3
"""
Finance App - Account Balance Analyzer
Processes bank statement CSV files and generates balance plots and Excel exports.
"""

import pandas as pd
import matplotlib.pyplot as plt
import json
import os
from pathlib import Path
from datetime import datetime


def load_config(config_path='config.json'):
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def parse_csv_file(filepath):
    """
    Parse a French bank statement CSV file.

    Args:
        filepath: Path to the CSV file

    Returns:
        tuple: (account_info dict, transactions DataFrame)
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # Parse header information
    account_info = {}
    transaction_start = 0

    for i, line in enumerate(lines):
        if line.strip() == '':
            continue
        if 'Date;Libellé;Montant' in line or 'Date;Libell' in line:
            transaction_start = i + 1
            break

        # Parse header fields
        parts = line.strip().split(';')
        if len(parts) >= 2:
            key = parts[0].strip()
            value = parts[1].strip()
            account_info[key] = value

    # Parse transactions
    if transaction_start == 0:
        return account_info, pd.DataFrame()

    transactions = []
    for line in lines[transaction_start:]:
        if line.strip() == '':
            continue

        parts = line.strip().split(';')
        if len(parts) >= 3:
            date_str = parts[0].strip()
            description = parts[1].strip().strip('"')
            amount_str = parts[2].strip().strip('"')

            try:
                # Parse French date format DD/MM/YYYY
                date = pd.to_datetime(date_str, format='%d/%m/%Y')

                # Parse French number format (comma as decimal separator)
                amount = float(amount_str.replace(',', '.'))

                transactions.append({
                    'date': date,
                    'description': description,
                    'amount': amount
                })
            except (ValueError, IndexError):
                continue

    df = pd.DataFrame(transactions)
    return account_info, df


def load_all_transactions(data_folder, start_date=None):
    """
    Load and combine all CSV files from the data folder.

    Args:
        data_folder: Path to folder containing CSV files
        start_date: Optional start date (YYYY-MM-DD string or datetime) to filter transactions

    Returns:
        DataFrame: Combined transactions from all files
    """
    csv_files = list(Path(data_folder).glob('*.csv'))

    if not csv_files:
        raise ValueError(f"No CSV files found in {data_folder}")

    all_transactions = []

    print(f"Found {len(csv_files)} CSV file(s)")

    for csv_file in csv_files:
        print(f"Processing: {csv_file.name}")
        account_info, df = parse_csv_file(csv_file)

        if not df.empty:
            all_transactions.append(df)
            print(f"  - Loaded {len(df)} transactions")

    if not all_transactions:
        raise ValueError("No transactions found in any CSV file")

    # Combine all transactions
    combined_df = pd.concat(all_transactions, ignore_index=True)

    # Sort by date
    combined_df = combined_df.sort_values('date').reset_index(drop=True)

    # Track duplicates before removal
    initial_count = len(combined_df)

    # Remove duplicates (in case same transaction appears in multiple files)
    # Using all three fields ensures we only remove exact duplicates
    combined_df = combined_df.drop_duplicates(subset=['date', 'description', 'amount'], keep='first')
    combined_df = combined_df.reset_index(drop=True)

    duplicates_removed = initial_count - len(combined_df)
    if duplicates_removed > 0:
        print(f"  - Removed {duplicates_removed} duplicate transaction(s)")

    # Filter by start date if provided
    if start_date is not None:
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)

        initial_count = len(combined_df)
        combined_df = combined_df[combined_df['date'] >= start_date].reset_index(drop=True)
        filtered_count = initial_count - len(combined_df)

        if filtered_count > 0:
            print(f"  - Filtered out {filtered_count} transaction(s) before {start_date.date()}")

    print(f"\nTotal unique transactions: {len(combined_df)}")
    print(f"Date range: {combined_df['date'].min().date()} to {combined_df['date'].max().date()}")

    return combined_df


def calculate_balances(transactions_df, initial_balance=0.0):
    """
    Calculate running balance for all transactions.

    Args:
        transactions_df: DataFrame with transactions
        initial_balance: Starting balance before first transaction

    Returns:
        DataFrame: Transactions with balance column added
    """
    df = transactions_df.copy()
    df['balance'] = initial_balance + df['amount'].cumsum()
    return df


def create_balance_plot(df, config):
    """
    Create and save balance over time plot.

    Args:
        df: DataFrame with date and balance columns
        config: Configuration dictionary
    """
    plot_config = config['plot_settings']

    # Get date range for title
    start_date = df['date'].min().strftime('%d/%m/%Y')
    end_date = df['date'].max().strftime('%d/%m/%Y')
    title_with_dates = f"{plot_config['title']} ({start_date} - {end_date})"

    plt.figure(figsize=plot_config['figure_size'])
    plt.plot(df['date'], df['balance'], linewidth=2, marker='o', markersize=3)

    plt.title(title_with_dates, fontsize=14, fontweight='bold')
    plt.xlabel(plot_config['xlabel'], fontsize=12)
    plt.ylabel(plot_config['ylabel'], fontsize=12)

    if plot_config['grid']:
        plt.grid(True, alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()

    # Create output folder if it doesn't exist
    output_folder = Path(config['output_folder'])
    output_folder.mkdir(exist_ok=True)

    # Create filename with date range
    start_date_file = df['date'].min().strftime('%Y%m%d')
    end_date_file = df['date'].max().strftime('%Y%m%d')
    date_range_str = f"{start_date_file}_to_{end_date_file}"

    # Save plot with date range in filename
    plot_path = output_folder / f'balance_plot_{date_range_str}.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved: {plot_path}")

    # Also save as a non-timestamped version for easy access
    latest_path = output_folder / 'balance_plot_latest.png'
    plt.savefig(latest_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved: {latest_path}")

    plt.close()


def export_to_excel(df, config):
    """
    Export transactions and balances to Excel.

    Args:
        df: DataFrame with transactions and balances
        config: Configuration dictionary
    """
    output_folder = Path(config['output_folder'])
    output_folder.mkdir(exist_ok=True)

    # Prepare data for export
    export_df = df.copy()

    # Store date range before converting to string
    start_date_file = df['date'].min().strftime('%Y%m%d')
    end_date_file = df['date'].max().strftime('%Y%m%d')
    date_range_str = f"{start_date_file}_to_{end_date_file}"

    export_df['date'] = export_df['date'].dt.strftime('%d/%m/%Y')

    # Rename columns for clarity
    export_df = export_df.rename(columns={
        'date': 'Date',
        'description': 'Description',
        'amount': 'Amount (EUR)',
        'balance': 'Balance (EUR)'
    })

    # Save to Excel with date range in filename
    excel_path = output_folder / f'account_balances_{date_range_str}.xlsx'

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        export_df.to_excel(writer, sheet_name='Transactions', index=False)

        # Create a summary sheet
        summary_data = {
            'Metric': [
                'Initial Balance',
                'Final Balance',
                'Total Income',
                'Total Expenses',
                'Net Change',
                'Number of Transactions',
                'First Transaction Date',
                'Last Transaction Date'
            ],
            'Value': [
                f"{df['balance'].iloc[0] - df['amount'].iloc[0]:.2f}",
                f"{df['balance'].iloc[-1]:.2f}",
                f"{df[df['amount'] > 0]['amount'].sum():.2f}",
                f"{df[df['amount'] < 0]['amount'].sum():.2f}",
                f"{df['amount'].sum():.2f}",
                len(df),
                df['date'].min().strftime('%d/%m/%Y'),
                df['date'].max().strftime('%d/%m/%Y')
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

    print(f"Excel file saved: {excel_path}")

    # Also save as a non-timestamped version
    latest_excel_path = output_folder / 'account_balances_latest.xlsx'
    with pd.ExcelWriter(latest_excel_path, engine='openpyxl') as writer:
        export_df.to_excel(writer, sheet_name='Transactions', index=False)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

    print(f"Excel file saved: {latest_excel_path}")


def main():
    """Main execution function."""
    print("=" * 60)
    print("Finance App - Account Balance Analyzer")
    print("=" * 60)

    # Load configuration
    config = load_config()
    print(f"\nInitial balance: {config['initial_balance']:.2f} EUR")

    # Check for start date filter
    start_date = config.get('start_date')
    if start_date:
        print(f"Start date filter: {start_date}")

    # Load all transactions
    transactions = load_all_transactions(config['data_folder'], start_date)

    # Calculate balances
    df_with_balance = calculate_balances(transactions, config['initial_balance'])

    # Display summary
    print(f"\nFinal balance: {df_with_balance['balance'].iloc[-1]:.2f} EUR")
    print(f"Total income: {df_with_balance[df_with_balance['amount'] > 0]['amount'].sum():.2f} EUR")
    print(f"Total expenses: {df_with_balance[df_with_balance['amount'] < 0]['amount'].sum():.2f} EUR")

    # Create visualizations and exports
    create_balance_plot(df_with_balance, config)
    export_to_excel(df_with_balance, config)

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
