import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Car Rental Acquisition Simulator", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] {
        background-color: #343434;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    [data-testid="stMetricValue"] { color: white; }
    [data-testid="stMetricLabel"] { color: #dcdcdc; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚗 Final Business Evaluation: Sander's Car Rental Acquisition")
st.markdown("Use this tool to stress-test the acquisition. All variables are based on the meeting notes from Jan 15, 2026.")

# --- SIDEBAR: GLOBAL STRATEGIC SETTINGS ---
st.sidebar.header("1. Global Acquisition Costs")
total_goodwill = st.sidebar.number_input("Goodwill / System Price (ANG)", value=15000, help="Value for website, phone, T&Cs, and Draaiboek.")

st.sidebar.header("2. Revenue & Utilization")
utilization_rate = st.sidebar.slider("Global Utilization Rate (%)", 0, 100, 85, help="Avg occupancy throughout the year.")
summer_gap_total = st.sidebar.number_input("Total 'Summer Gap' Bonus (ANG)", value=8000, help="Projected extra revenue from tourist pivot in July/Aug.")

st.sidebar.header("3. Hidden Operational Costs")
monthly_labor = st.sidebar.number_input("Monthly Labor (3rd person backup)", value=500)
fixed_opex_annual = st.sidebar.number_input("Fixed Costs (Web/Admin/Misc - Annual)", value=1500)
ob_tax_rate = st.sidebar.slider("OB / Sales Tax (%)", 0.0, 10.0, 6.0)

st.sidebar.header("4. Financing / Loan")
use_loan = st.sidebar.checkbox("Use Financing?")
loan_pct, loan_interest, loan_term = 0, 0, 0
if use_loan:
    loan_pct = st.sidebar.slider("Loan % of Total Price", 10, 100, 50)
    loan_interest = st.sidebar.number_input("Annual Interest Rate (%)", value=7.0)
    loan_term = st.sidebar.number_input("Loan Term (Years)", value=3)

# --- SECTION 1: GRANULAR FLEET CONFIGURATION ---
st.subheader("📋 Fleet Configuration")
st.markdown("Edit specific purchase prices, rental rates, and maintenance buffers for each car.")

# Column Keys for logic consistency
C_NAME = "Vehicle Name"
C_PRICE = "Purchase Price (ANG)"
C_RENT = "Monthly Rental (ANG)"
C_MAINT = "Annual Maint (ANG)"
C_INS = "Annual Ins/Roadside (ANG)"

if 'fleet_df' not in st.session_state:
    st.session_state.fleet_df = pd.DataFrame([
        {C_NAME: "Kia Picanto 1", C_PRICE: 8000, C_RENT: 900, C_MAINT: 3600, C_INS: 1680},
        {C_NAME: "Kia Picanto 2", C_PRICE: 8000, C_RENT: 900, C_MAINT: 3600, C_INS: 1680},
        {C_NAME: "Hyundai i10", C_PRICE: 8000, C_RENT: 1000, C_MAINT: 3600, C_INS: 1680},
        {C_NAME: "Lancer 1", C_PRICE: 8000, C_RENT: 1000, C_MAINT: 3600, C_INS: 1680},
        {C_NAME: "Kia rio 1", C_PRICE: 8000, C_RENT: 900, C_MAINT: 3600, C_INS: 1680}
    ])

edited_df = st.data_editor(st.session_state.fleet_df, num_rows="dynamic", use_container_width=True)

# --- CALCULATIONS ---
if not edited_df.empty:
    num_cars = len(edited_df)
    
    # Investment & Financing
    total_assets = edited_df[C_PRICE].sum()
    total_price = total_assets + total_goodwill
    
    loan_amount = total_price * (loan_pct / 100) if use_loan else 0
    upfront_cash = total_price - loan_amount
    
    if use_loan and loan_term > 0:
        m_rate = (loan_interest / 100) / 12
        n_pay = loan_term * 12
        monthly_loan = loan_amount * (m_rate * (1 + m_rate)**n_pay) / ((1 + m_rate)**n_pay - 1) if m_rate > 0 else loan_amount / n_pay
    else:
        monthly_loan = 0

    # Revenue Logic
    base_annual_rev = (edited_df[C_RENT].sum() * 12) * (utilization_rate / 100)
    gross_rev = base_annual_rev + summer_gap_total
    after_tax_rev = gross_rev * (1 - (ob_tax_rate / 100))

    # Expense Logic
    annual_car_costs = edited_df[C_MAINT].sum() + edited_df[C_INS].sum()
    total_annual_opex = annual_car_costs + (monthly_labor * 12) + fixed_opex_annual

    # Profitability
    annual_net_profit = after_tax_rev - total_annual_opex
    monthly_net_profit = annual_net_profit / 12
    monthly_cash_flow = monthly_net_profit - monthly_loan
    
    payback_months = upfront_cash / monthly_cash_flow if monthly_cash_flow > 0 else float('inf')
    roi_pct = (annual_net_profit / total_price) * 100 if total_price > 0 else 0

    # --- SECTION 2: METRICS DASHBOARD ---
    st.subheader("🏁 Financial Verdict")
    if monthly_cash_flow > 0:
        st.success(f"📈 **Payback on Upfront Cash (ANG {upfront_cash:,.0f}) in {payback_months:.1f} months.**")
    else:
        st.error("⚠️ **Negative Cash Flow:** Business profit does not cover your loan and expenses.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Deal Price", f"ANG {total_price:,.0f}")
    m2.metric("Upfront Cash", f"ANG {upfront_cash:,.0f}")
    m3.metric("Net Monthly Cash Flow", f"ANG {monthly_cash_flow:,.0f}")
    m4.metric("Annual ROI", f"{roi_pct:.1f}%")

    st.divider()

    # --- SECTION 3: CASH FLOW CHART ---
    st.subheader("📈 5-Year Cumulative Cash Flow")
    
    months = np.arange(0, 61)
    cash_pos = -upfront_cash + (monthly_cash_flow * months)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=cash_pos, name='Net Cash position', line=dict(color='#00CC96', width=4)))
    fig.add_trace(go.Scatter(x=months, y=[0]*61, name='Break-even Line', line=dict(color='#EF553B', width=2, dash='dash')))
    fig.update_layout(xaxis_title="Months", yaxis_title="ANG", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    # --- SECTION 4: DATA INSIGHTS ---
    with st.expander("🔍 Detailed Assumptions Breakdown"):
        st.write(f"""
        - **Summer Gap:** We added **ANG {summer_gap_total:,.0f}** to your gross revenue to reflect the tourist pivot strategy.
        - **Taxation:** Deducted **{ob_tax_rate}%** from your gross revenue as Sales Tax.
        - **Financing:** Your upfront cash is **ANG {upfront_cash:,.0f}**. The rest is a loan with a monthly payment of **ANG {monthly_loan:,.2f}**.
        - **Goodwill:** You are paying **ANG {total_goodwill:,.0f}** for the reputation and knowledge base.
        """)
else:
    st.warning("Please add vehicles to the table above to generate the evaluation.")
