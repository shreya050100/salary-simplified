import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pdfplumber
import base64
import os
from PIL import Image
import google.generativeai as genai
from io import BytesIO

# --- Gemini setup ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def extract_text_from_pdf(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def extract_text_from_image(image):
    try:
        model = genai.GenerativeModel("gemini-pro-vision")
        image_bytes = BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes = image_bytes.getvalue()
        response = model.generate_content(["Extract all visible text from this image, especially salary-related fields:", image_bytes])
        return response.text
    except Exception as e:
        st.error(f"Gemini Image Parsing Failed: {e}")
        return ""

# --- Indian Professional Tax Slabs ---
PT_SLABS = {
    "Karnataka": [(15000, 0), (float('inf'), 200)],
    "Maharashtra": [(7500, 0), (10000, 175), (float('inf'), 200)],
    "Delhi": [(float('inf'), 0)],
    "Tamil Nadu": [(21000, 0), (float('inf'), 200)],
    "West Bengal": [(10000, 0), (15000, 110), (25000, 130), (40000, 150), (float('inf'), 200)],
    "Telangana": [(15000, 0), (float('inf'), 200)],
    "Kerala": [(20000, 0), (25000, 100), (30000, 150), (float('inf'), 200)],
    "Gujarat": [(12000, 0), (15000, 150), (float('inf'), 200)],
    "Uttar Pradesh": [(float('inf'), 0)],
    "Other": [(float('inf'), 0)]
}

def get_prof_tax(state, gross_monthly):
    if state not in PT_SLABS:
        state = "Other"
    for limit, amount in PT_SLABS[state]:
        if gross_monthly <= limit:
            return amount
    return 0

# --- Page Setup ---
st.set_page_config(page_title="Salary Simplified", page_icon="💰", layout="wide")
st.markdown("""
    <style>
    .masked { background-color: #111; color: #111; border-radius: 5px; padding: 2px 6px; }
    .unmasked { background-color: #1f1f1f; color: #fff; border-radius: 5px; padding: 2px 6px; }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("💰 Salary Simplified")
st.markdown("Break down your salary, upload your payslip, compare tax regimes & get AI tips.")

# --- File Upload ---
uploaded_file = st.file_uploader("📤 Upload Payslip (PDF/Image optional)", type=["pdf", "png", "jpg", "jpeg"])
payslip_text = ""

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        payslip_text = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type.startswith("image"):
        image = Image.open(uploaded_file)
        payslip_text = extract_text_from_image(image)
    st.subheader("🔍 Raw Extracted Payslip Data")
    mask_toggle = st.toggle("🔒 Mask Sensitive Data", value=True)
    if mask_toggle:
        st.markdown(f"<div class='masked'>{payslip_text[:800]}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='unmasked'>{payslip_text[:800]}</div>", unsafe_allow_html=True)

# --- Manual Input Section ---
st.markdown("### 🧾 Salary Inputs")
col1, col2, col3 = st.columns(3)
with col1:
    state = st.selectbox("State (for Prof. Tax)", list(PT_SLABS.keys()))
    metro = st.checkbox("🏙️ Metro City (HRA = 50%)", value=False)
    basic = st.number_input("Basic Pay", min_value=0, value=30000)
with col2:
    special = st.number_input("Special Allowance", min_value=0, value=5000)
    bonus = st.number_input("Bonus", min_value=0, value=2000)
    other = st.number_input("Other Income", min_value=0, value=1000)
with col3:
    auto_hra = round(0.5 * basic) if metro else round(0.4 * basic)
    hra = st.number_input("House Rent Allowance (HRA)", min_value=0, value=auto_hra)
    epf = st.number_input("EPF Monthly", min_value=0, value=1800)

# --- Age & Regime Selection ---
st.markdown("### ⚖️ Tax Regime")
age = st.selectbox("Age", ["<60", "60-80", ">80"])
regime_choice = st.radio("Tax Regime", ["Old", "New", "Compare Both"], horizontal=True)

# --- Tax Calculation Logic ---
if st.button("💡 Calculate Tax"):
    gross_monthly = basic + hra + special + bonus + other
    gross_annual = gross_monthly * 12
    prof_tax = get_prof_tax(state, gross_monthly)
    deductions = 12 * (epf + prof_tax)
    std_deduction = 50000
    total_deductions = deductions + std_deduction
    taxable_income = max(0, gross_annual - total_deductions)

    def tax_old(income):
        slabs = {
            "<60": [(250000, 0), (500000, 0.05), (1000000, 0.2), (float('inf'), 0.3)],
            "60-80": [(300000, 0), (500000, 0.05), (1000000, 0.2), (float('inf'), 0.3)],
            ">80": [(500000, 0), (1000000, 0.2), (float('inf'), 0.3)]
        }
        tax = 0
        prev = 0
        for limit, rate in slabs[age]:
            if income > limit:
                tax += (limit - prev) * rate
                prev = limit
            else:
                tax += (income - prev) * rate
                break
        return round(tax)

    def tax_new(income):
        slabs = [(300000, 0), (600000, 0.05), (900000, 0.1), (1200000, 0.15), (1500000, 0.2), (float('inf'), 0.3)]
        tax = 0
        prev = 0
        for limit, rate in slabs:
            if income > limit:
                tax += (limit - prev) * rate
                prev = limit
            else:
                tax += (income - prev) * rate
                break
        return round(tax)

    # --- Output ---
    st.subheader("📊 Salary & Tax Breakdown")
    st.write(f"**Gross Income (Annual):** ₹{gross_annual:,.0f}")
    st.write(f"**Total Deductions (incl. ₹50K std):** ₹{total_deductions:,.0f}")
    st.write(f"**Taxable Income:** ₹{taxable_income:,.0f}")

    if regime_choice == "Old":
        tax = tax_old(taxable_income)
        st.success(f"Estimated Tax (Old Regime): ₹{tax:,.0f}")
    elif regime_choice == "New":
        tax = tax_new(gross_annual)
        st.success(f"Estimated Tax (New Regime): ₹{tax:,.0f}")
    else:
        t_old = tax_old(taxable_income)
        t_new = tax_new(gross_annual)
        better = "Old" if t_old < t_new else "New"
        st.info(f"Old Regime: ₹{t_old:,} | New Regime: ₹{t_new:,}")
        st.success(f"✅ Recommended: **{better} Regime**")
        tax = min(t_old, t_new)

        # --- Chart ---
        fig, ax = plt.subplots()
        ax.bar(["Old", "New"], [t_old, t_new], color=["#4CAF50", "#FF9800"])
        ax.set_ylabel("Tax (₹)")
        ax.set_title("Regime Comparison")
        st.pyplot(fig)

    # --- Take-home ---
    take_home = gross_annual - tax - deductions
    st.subheader("💸 Estimated Take-Home")
    st.write(f"**Monthly Take-Home:** ₹{take_home/12:,.0f}")

    # --- AI Money Tips ---
    if GEMINI_API_KEY:
        with st.spinner("Getting smart money suggestions 💡"):
            tip_model = genai.GenerativeModel("gemini-pro")
            prompt = f"Give beginner-friendly investment & tax-saving suggestions in bullet points for someone earning ₹{take_home/12:,.0f} per month. Keep it short and helpful."
            tips = tip_model.generate_content(prompt)
            st.markdown("### 💡 Smart Money Tips")
            st.markdown(tips.text)

# --- Salary Slip Help ---
st.markdown("---")
st.markdown("### 🧾 How to Read Your Salary Slip?")
st.markdown("""
- **Basic Pay**: Core component; affects PF & gratuity.
- **HRA**: Partially tax-exempt if rent paid. Metro = 50% Basic, Non-Metro = 40%.
- **Special Allowance**: Fully taxable.
- **Bonus**: Variable component; taxable.
- **Other Income**: Covers reimbursements, incentives, or one-time payments.
- **EPF**: 12% of Basic, deducted monthly.
- **Professional Tax**: State-wise fixed tax deducted monthly.
- **Income Tax**: Based on taxable income after all deductions.
""")
