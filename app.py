#!/usr/bin/env python3
"""
Finance App - Streamlit Web Application
Interactive dashboard for analyzing bank account transactions in French.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import json
from datetime import datetime
import tempfile
import io

# Import functions from analyze_balance.py
from analyze_balance import parse_csv_file, calculate_balances


# French month names
FRENCH_MONTHS = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}


def process_uploaded_files(uploaded_files, start_date=None, initial_balance=0.0):
    """
    Process uploaded CSV files and return combined transaction data.

    Args:
        uploaded_files: List of uploaded file objects from Streamlit
        start_date: Optional start date to filter transactions
        initial_balance: Initial balance before first transaction

    Returns:
        DataFrame: Processed transactions with balance
    """
    all_transactions = []

    for uploaded_file in uploaded_files:
        # Create a temporary file to store the uploaded content
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            # Parse the CSV file
            account_info, df = parse_csv_file(tmp_path)

            if not df.empty:
                all_transactions.append(df)
        finally:
            # Clean up temporary file
            Path(tmp_path).unlink(missing_ok=True)

    if not all_transactions:
        return None

    # Combine all transactions
    combined_df = pd.concat(all_transactions, ignore_index=True)

    # Sort by date
    combined_df = combined_df.sort_values('date').reset_index(drop=True)

    # Remove duplicates
    combined_df = combined_df.drop_duplicates(subset=['date', 'description', 'amount'], keep='first')
    combined_df = combined_df.reset_index(drop=True)

    # Filter by start date if provided
    if start_date is not None:
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        combined_df = combined_df[combined_df['date'] >= start_date].reset_index(drop=True)

    # Calculate balances
    df_with_balance = calculate_balances(combined_df, initial_balance)

    return df_with_balance


def format_currency(value):
    """Format value as EUR currency in French format."""
    return f"{value:,.2f} €".replace(",", " ").replace(".", ",")


def prepare_monthly_data(df):
    """Prepare monthly income and expense data."""
    df_monthly = df.copy()
    df_monthly['year_month'] = df_monthly['date'].dt.to_period('M')
    df_monthly['month_name'] = df_monthly['date'].dt.month.map(FRENCH_MONTHS)
    df_monthly['year'] = df_monthly['date'].dt.year

    # Separate income and expenses
    df_monthly['income'] = df_monthly['amount'].apply(lambda x: x if x > 0 else 0)
    df_monthly['expense'] = df_monthly['amount'].apply(lambda x: abs(x) if x < 0 else 0)

    # Group by month
    monthly_summary = df_monthly.groupby(['year_month', 'month_name', 'year']).agg({
        'income': 'sum',
        'expense': 'sum'
    }).reset_index()

    monthly_summary['net'] = monthly_summary['income'] - monthly_summary['expense']
    monthly_summary['month_label'] = monthly_summary['month_name'] + ' ' + monthly_summary['year'].astype(str)

    return monthly_summary


def main():
    """Main Streamlit application."""

    # Page configuration
    st.set_page_config(
        page_title="Analyse Financière",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Title
    st.title("💰 Tableau de Bord Financier")
    st.markdown("---")

    # Sidebar - File upload and configuration
    st.sidebar.header("📁 Données")

    # File uploader
    uploaded_files = st.sidebar.file_uploader(
        "Télécharger vos fichiers CSV bancaires",
        type=['csv'],
        accept_multiple_files=True,
        help="Sélectionnez un ou plusieurs fichiers CSV de relevés bancaires"
    )

    if not uploaded_files:
        st.info("👈 Veuillez télécharger vos fichiers CSV de relevés bancaires dans la barre latérale pour commencer l'analyse.")
        st.markdown("""
        ### Instructions
        1. Cliquez sur **"Browse files"** dans la barre latérale
        2. Sélectionnez un ou plusieurs fichiers CSV de vos relevés bancaires
        3. Configurez le solde initial et la date de début (optionnel)
        4. L'analyse se mettra à jour automatiquement

        ### Format de fichier attendu
        - Format CSV avec séparateur point-virgule (`;`)
        - Colonnes: Date, Libellé, Montant
        - Format de date: DD/MM/YYYY
        - Format numérique: virgule comme séparateur décimal
        """)
        return

    st.sidebar.success(f"✅ {len(uploaded_files)} fichier(s) chargé(s)")

    # Configuration
    st.sidebar.header("⚙️ Configuration")

    initial_balance = st.sidebar.number_input(
        "Solde initial (€)",
        value=0.0,
        step=100.0,
        format="%.2f",
        help="Le solde de votre compte avant la première transaction"
    )

    use_start_date = st.sidebar.checkbox(
        "Filtrer par date de début",
        value=False,
        help="Activer pour ne prendre en compte que les transactions à partir d'une certaine date"
    )

    start_date = None
    if use_start_date:
        start_date = st.sidebar.date_input(
            "Date de début",
            value=None,
            help="Seules les transactions à partir de cette date seront incluses"
        )
        if start_date:
            start_date = pd.to_datetime(start_date)

    # Process uploaded files
    with st.spinner("Traitement des fichiers en cours..."):
        df = process_uploaded_files(uploaded_files, start_date, initial_balance)

    if df is None or len(df) == 0:
        st.error("❌ Aucune transaction trouvée dans les fichiers téléchargés.")
        return

    # Key metrics
    st.subheader("📊 Résumé de la Période")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Solde Initial",
            format_currency(df['balance'].iloc[0] - df['amount'].iloc[0])
        )

    with col2:
        st.metric(
            "Solde Final",
            format_currency(df['balance'].iloc[-1])
        )

    with col3:
        total_income = df[df['amount'] > 0]['amount'].sum()
        st.metric(
            "Revenus Total",
            format_currency(total_income),
            delta=None,
            delta_color="normal"
        )

    with col4:
        total_expenses = df[df['amount'] < 0]['amount'].sum()
        st.metric(
            "Dépenses Total",
            format_currency(total_expenses),
            delta=None,
            delta_color="inverse"
        )

    st.markdown("---")

    # Date range info
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()

    st.info(f"📅 Période analysée: {min_date.strftime('%d/%m/%Y')} - {max_date.strftime('%d/%m/%Y')} | 💳 {len(df)} transactions")

    # Balance evolution chart
    st.subheader("📈 Évolution du Solde")

    fig_balance = go.Figure()

    fig_balance.add_trace(go.Scatter(
        x=df['date'],
        y=df['balance'],
        mode='lines+markers',
        name='Solde',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=4),
        hovertemplate='<b>Date:</b> %{x|%d/%m/%Y}<br>' +
                      '<b>Solde:</b> %{y:,.2f} €<br>' +
                      '<extra></extra>'
    ))

    fig_balance.update_layout(
        xaxis_title="Date",
        yaxis_title="Solde (€)",
        hovermode='x unified',
        height=400,
        template='plotly_white',
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
    )

    st.plotly_chart(fig_balance, use_container_width=True)

    st.markdown("---")

    # Monthly income/expense chart
    st.subheader("📊 Revenus et Dépenses Mensuels")

    monthly_data = prepare_monthly_data(df)

    fig_monthly = go.Figure()

    # Add income bars (green)
    fig_monthly.add_trace(go.Bar(
        x=monthly_data['month_label'],
        y=monthly_data['income'],
        name='Revenus',
        marker_color='#2ecc71',
        hovertemplate='<b>%{x}</b><br>' +
                      'Revenus: %{y:,.2f} €<br>' +
                      '<extra></extra>'
    ))

    # Add expense bars (red)
    fig_monthly.add_trace(go.Bar(
        x=monthly_data['month_label'],
        y=monthly_data['expense'],
        name='Dépenses',
        marker_color='#e74c3c',
        hovertemplate='<b>%{x}</b><br>' +
                      'Dépenses: %{y:,.2f} €<br>' +
                      '<extra></extra>'
    ))

    fig_monthly.update_layout(
        barmode='group',
        xaxis_title="Mois",
        yaxis_title="Montant (€)",
        hovermode='x unified',
        height=400,
        template='plotly_white',
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    st.plotly_chart(fig_monthly, use_container_width=True)

    st.markdown("---")

    # Monthly summary table
    st.subheader("📋 Résumé Mensuel")

    monthly_display = monthly_data.copy()
    monthly_display['Revenus'] = monthly_display['income'].apply(format_currency)
    monthly_display['Dépenses'] = monthly_display['expense'].apply(format_currency)
    monthly_display['Solde Net'] = monthly_display['net'].apply(format_currency)

    st.dataframe(
        monthly_display[['month_label', 'Revenus', 'Dépenses', 'Solde Net']].rename(
            columns={'month_label': 'Mois'}
        ),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # Transaction details
    st.subheader("📝 Détails des Transactions")

    # Search filter
    search_term = st.text_input("🔎 Rechercher dans les descriptions", "")

    # Prepare transaction display
    transactions_display = df.copy()
    transactions_display['Date'] = transactions_display['date'].dt.strftime('%d/%m/%Y')
    transactions_display['Description'] = transactions_display['description']
    transactions_display['Montant'] = transactions_display['amount'].apply(format_currency)
    transactions_display['Solde'] = transactions_display['balance'].apply(format_currency)

    # Apply search filter
    if search_term:
        mask = transactions_display['Description'].str.contains(search_term, case=False, na=False)
        transactions_display = transactions_display[mask]

    # Display transactions table
    st.dataframe(
        transactions_display[['Date', 'Description', 'Montant', 'Solde']],
        use_container_width=True,
        hide_index=True,
        height=400
    )

    # Download button for Excel export
    st.markdown("---")
    st.subheader("💾 Export")

    # Prepare Excel export
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Transactions sheet
        export_df = df.copy()
        export_df['date'] = export_df['date'].dt.strftime('%d/%m/%Y')
        export_df = export_df.rename(columns={
            'date': 'Date',
            'description': 'Description',
            'amount': 'Montant (EUR)',
            'balance': 'Solde (EUR)'
        })
        export_df[['Date', 'Description', 'Montant (EUR)', 'Solde (EUR)']].to_excel(
            writer, sheet_name='Transactions', index=False
        )

        # Summary sheet
        summary_data = {
            'Métrique': [
                'Solde Initial',
                'Solde Final',
                'Total Revenus',
                'Total Dépenses',
                'Variation Nette',
                'Nombre de Transactions',
                'Première Transaction',
                'Dernière Transaction'
            ],
            'Valeur': [
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
        summary_df.to_excel(writer, sheet_name='Résumé', index=False)

    excel_data = output.getvalue()

    st.download_button(
        label="📥 Télécharger l'analyse en Excel",
        data=excel_data,
        file_name=f"analyse_financiere_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == '__main__':
    main()
