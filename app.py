import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pdfplumber
import re
import os
import google.generativeai as genai
from PIL import Image

# --- Setup Gemini ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def mask_text(text):
    return re.sub(r'[A-Z0-9]{4,}', lambda m: '*' * len(m.group()), text)

def extract_text_from_image(image_file):
    image = Image.open(image_file)
    model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content(["Extract payslip details like Basic Pay, HRA, Allowances, EPF, Prof Tax, Net Salary", image])
    return response.text

st.set_page_config(page_title="Salary Simplified", page_icon="💰", layout="wide")

# --- Header ---
st.markdown("""
    <div style='text-align: center; padding-top: 10px;'>
        <h1>💰 Salary Simplified – Understand Your Payslip & Tax Liability</h1>
        <p style='font-size: 16px; color: #ccc;'>
            This tool helps you break down your salary, compare Old vs New tax regimes, and estimate your take-home.
        </p>
    </div>
""", unsafe_allow_html=True)

if GEMINI_API_KEY:
    st.success("✅ Gemini AI enabled: Smart suggestions & insights powered by Google")
else:
    st.warning("⚠️ Gemini AI not active. Please set your API key in Streamlit secrets.")

# --- Upload Section ---
st.markdown("### 📤 Upload Your Salary Slip")
uploaded_file = st.file_uploader("Upload payslip (.pdf or image)", type=["pdf", "png", "jpg", "jpeg"])
show_masked = st.toggle("🔒 Mask sensitive info", value=True)

extracted_text = ""
if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() + "\n"
    else:
        extracted_text = extract_text_from_image(uploaded_file)

    st.markdown("### 📄 Extracted Payslip Info")
    if show_masked:
        st.code(mask_text(extracted_text))
    else:
        st.code(extracted_text)

# --- Inputs ---
st.markdown("### 🗕️ Monthly Salary Inputs")
col1, col2, col3 = st.columns(3)
with col1:
    basic = st.number_input("Basic Pay", min_value=0, value=30000)
    metro = st.checkbox("🌇️ Metro City?", value=False)
    auto_hra = round(0.5 * basic) if metro else round(0.4 * basic)
    use_auto_hra = st.checkbox(f"🩻 Auto-calculate HRA ({'50%' if metro else '40%'} of Basic)", value=True)
with col2:
    hra = st.number_input("House Rent Allowance (HRA)", min_value=0, value=auto_hra if use_auto_hra else 0)
    special = st.number_input("Special Allowance", min_value=0, value=5000)
    bonus = st.number_input("Bonus / Variable Pay", min_value=0, value=2000)
with col3:
    other = st.number_input("Other Income", min_value=0, value=1000)
    epf = st.number_input("EPF Deduction (Monthly)", min_value=0, value=1800)

    state_pt = {
        "Maharashtra": 200, "Karnataka": 200, "Tamil Nadu": 208, "Gujarat": 200, "Delhi": 0,
        "West Bengal": 200, "Kerala": 208, "Other": 0
    }
    selected_state = st.selectbox("🏛️ Select State", list(state_pt.keys()))
    auto_prof_tax = state_pt[selected_state]
    override_pt = st.checkbox("✏️ Manually enter Prof Tax?", value=False)
    prof_tax = st.number_input("Professional Tax", min_value=0, value=auto_prof_tax if not override_pt else 0, disabled=not override_pt)

# --- Regime Selection ---
st.markdown("### ⚖️ Tax Settings")
col1, col2 = st.columns(2)
with col1:
    age = st.selectbox("Your Age Bracket", ["<60", "60-80", ">80"])
with col2:
    regime_choice = st.radio("Tax Regime", ["Old", "New", "Compare Both"], horizontal=True)

st.info("👉 Click below to calculate")

if st.button("💡 Calculate Tax"):
    gross = 12 * (basic + hra + special + bonus + other)
    deductions = 12 * (epf + prof_tax)
    std_deduction = 50000
    total_deductions = deductions + std_deduction
    taxable_income = max(0, gross - total_deductions)

    def tax_old(income):
        slabs = {
            "<60": [(250000, 0), (500000, 0.05), (1000000, 0.2), (float('inf'), 0.3)],
            "60-80": [(300000, 0), (500000, 0.05), (1000000, 0.2), (float('inf'), 0.3)],
            ">80": [(500000, 0), (1000000, 0.2), (float('inf'), 0.3)]
        }
        tax, prev = 0, 0
        for limit, rate in slabs[age]:
            if income > limit:
                tax += (limit - prev) * rate
                prev = limit
            else:
                tax += (income - prev) * rate
                break
        return round(tax)

    def tax_new(income):
        slabs = [(300000, 0), (600000, 0.05), (900000, 0.1),
                 (1200000, 0.15), (1500000, 0.2), (float('inf'), 0.3)]
        tax, prev = 0, 0
        for limit, rate in slabs:
            if income > limit:
                tax += (limit - prev) * rate
                prev = limit
            else:
                tax += (income - prev) * rate
                break
        return round(tax)

    st.markdown("### 📊 Salary & Tax Breakdown")
    st.write(f"**Gross Annual Income:** ₹{gross:,.0f}")
    st.write(f"**Total Deductions (incl. ₹50K std):** ₹{total_deductions:,.0f}")
    st.write(f"**Taxable Income:** ₹{taxable_income:,.0f}")

    if regime_choice == "Old":
        tax = tax_old(taxable_income)
        st.success(f"Tax (Old Regime): ₹{tax:,.0f}")
    elif regime_choice == "New":
        tax = tax_new(gross)
        st.success(f"Tax (New Regime): ₹{tax:,.0f}")
    else:
        tax_old_val = tax_old(taxable_income)
        tax_new_val = tax_new(gross)
        better = "Old" if tax_old_val < tax_new_val else "New"
        tax = min(tax_old_val, tax_new_val)  # ✅ Fix for NameError
        st.info(f"Old: ₹{tax_old_val:,.0f}, New: ₹{tax_new_val:,.0f}")
        st.success(f"✅ Better Regime: {better}")

        fig, ax = plt.subplots()
        ax.bar(["Old", "New"], [tax_old_val, tax_new_val], color=["#4CAF50", "#FF9800"])
        ax.set_ylabel("Tax (₹)")
        st.pyplot(fig)

    take_home = gross - tax - deductions
    st.markdown("### 💸 Estimated Take-Home")
    st.write(f"**Annual:** ₹{take_home:,.0f}")
    st.write(f"**Monthly:** ₹{take_home/12:,.0f}")

    if GEMINI_API_KEY:
        with st.expander("💡 Personalized Money Advice"):
            model = genai.GenerativeModel("gemini-pro")
            prompt = f"Suggest money-saving and investment tips for someone earning ₹{take_home//12} monthly."
            response = model.generate_content(prompt)
            st.markdown(response.text)

with st.expander("🧾 How to Read Your Salary Slip?"):
    st.markdown("""
    - **Basic Pay**: Core part of salary used for PF & gratuity.
    - **HRA**: Tax-exempt if you pay rent (40–50% of basic).
    - **Special Allowance**: Fully taxable.
    - **Bonus**: Usually performance-linked; taxable.
    - **Other Income**: Miscellaneous earnings (e.g., incentives, reimbursements).
    - **EPF**: Statutory retirement contribution (12%).
    - **Professional Tax**: State-specific small deduction.
    - **Income Tax**: Computed under chosen regime.
    """)
