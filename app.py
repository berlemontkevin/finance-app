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
import sys

# Import functions from analyze_balance.py
from analyze_balance import load_all_transactions, calculate_balances, load_config


# French month names
FRENCH_MONTHS = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}


@st.cache_data
def load_data():
    """Load and process transaction data with caching."""
    try:
        config = load_config()
        start_date = config.get('start_date')
        transactions = load_all_transactions(config['data_folder'], start_date)
        df = calculate_balances(transactions, config['initial_balance'])
        return df, config
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")
        return None, None


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

    # Load data
    df, config = load_data()

    if df is None or len(df) == 0:
        st.warning("⚠️ Aucune donnée disponible. Veuillez ajouter des fichiers CSV dans le dossier 'data/'.")
        return

    # Sidebar filters
    st.sidebar.header("🔍 Filtres")

    # Date range filter
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()

    st.sidebar.subheader("Période")
    date_range = st.sidebar.date_input(
        "Sélectionner une période",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="date_range"
    )

    # Handle date range selection
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
        df_filtered = df[mask].copy()
    else:
        df_filtered = df.copy()

    if len(df_filtered) == 0:
        st.warning("⚠️ Aucune transaction dans la période sélectionnée.")
        return

    # Key metrics
    st.subheader("📊 Résumé de la Période")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Solde Initial",
            format_currency(df_filtered['balance'].iloc[0] - df_filtered['amount'].iloc[0])
        )

    with col2:
        st.metric(
            "Solde Final",
            format_currency(df_filtered['balance'].iloc[-1])
        )

    with col3:
        total_income = df_filtered[df_filtered['amount'] > 0]['amount'].sum()
        st.metric(
            "Revenus Total",
            format_currency(total_income),
            delta=None,
            delta_color="normal"
        )

    with col4:
        total_expenses = df_filtered[df_filtered['amount'] < 0]['amount'].sum()
        st.metric(
            "Dépenses Total",
            format_currency(total_expenses),
            delta=None,
            delta_color="inverse"
        )

    st.markdown("---")

    # Balance evolution chart
    st.subheader("📈 Évolution du Solde")

    fig_balance = go.Figure()

    fig_balance.add_trace(go.Scatter(
        x=df_filtered['date'],
        y=df_filtered['balance'],
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

    monthly_data = prepare_monthly_data(df_filtered)

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
    transactions_display = df_filtered.copy()
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

    # Footer
    st.markdown("---")
    st.caption(f"📅 Période totale: {min_date.strftime('%d/%m/%Y')} - {max_date.strftime('%d/%m/%Y')} | "
               f"💳 {len(df)} transactions | "
               f"🔍 {len(df_filtered)} affichées")


if __name__ == '__main__':
    main()
