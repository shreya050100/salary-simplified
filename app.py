import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pdfplumber

# Set layout
st.set_page_config(page_title="Salary Simplified", page_icon="💰", layout="wide")

# --- Header ---
with st.container():
    st.markdown("""
        <div style='text-align: center; padding-top: 10px;'>
            <h1>💰 Salary Simplified – Understand Your Payslip & Tax Liability</h1>
            <p style='font-size: 16px; color: #ccc;'>
                This tool helps you break down your salary, compare Old vs New tax regimes, and estimate your take-home.
            </p>
        </div>
    """, unsafe_allow_html=True)

# --- Inputs ---
with st.container():
    st.markdown("### 📥 Monthly Salary Inputs")
    col1, col2, col3 = st.columns(3)

    with col1:
        basic = st.number_input("Basic Pay", min_value=0, value=30000)
        metro = st.checkbox("🏙️ Metro City?", value=False)
        auto_hra = round(0.5 * basic) if metro else round(0.4 * basic)
        use_auto_hra = st.checkbox(f"🧮 Auto-calculate HRA ({'50%' if metro else '40%'} of Basic)", value=True)

    with col2:
        hra = st.number_input("House Rent Allowance (HRA)", min_value=0, value=auto_hra if use_auto_hra else 0)
        special = st.number_input("Special Allowance", min_value=0, value=5000)
        bonus = st.number_input("Bonus / Variable Pay", min_value=0, value=2000)

    with col3:
        other = st.number_input("Other Income", min_value=0, value=1000)
        epf = st.number_input("EPF Deduction (Monthly)", min_value=0, value=1800)
        prof_tax = st.number_input("Professional Tax (Monthly)", min_value=0, value=200)

# --- Regime Selection ---
with st.container():
    st.markdown("### ⚖️ Tax Settings")
    col1, col2 = st.columns(2)
    with col1:
        age = st.selectbox("Your Age Bracket", ["<60", "60-80", ">80"])
    with col2:
        regime_choice = st.radio("Choose Tax Regime", ["Old", "New", "Compare Both"], horizontal=True)

# --- File Upload ---
uploaded_file = st.file_uploader("📤 Upload Salary Slip (.c
