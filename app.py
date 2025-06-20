import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pdfplumber
import re
import os
import google.generativeai as genai
from PIL import Image

# --- Setup Gemini ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Ensure this is set in Streamlit secrets or your env
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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
    prof_tax = st.number_input("Professional Tax (Monthly)", min_value=0, value=200)

# --- Regime Selection ---
st.markdown("### ⚖️ Tax Settings")
col1, col2 = st.columns(2)
with col1:
    age = st.selectbox("Your Age Bracket", ["<60", "60-80", ">80"])
with col2:
    regime_choice = st.radio("Choose Tax Regime", ["Old", "New", "Compare Both"], horizontal=True)

# --- Upload PDF or Image ---
payslip_data, net_salary_from_payslip = None, None
uploaded_file = st.file_uploader("📄 Upload Salary Slip (.pdf or .png/.jpg)", type=["pdf", "png", "jpg"])
mask_data = st.toggle("🔒 Mask Sensitive Info", value=True)

if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        with pdfplumber.open(uploaded_file) as pdf:
            text = "".join(page.extract_text() for page in pdf.pages)
    else:
        if GEMINI_API_KEY:
            image = Image.open(uploaded_file)
            gemini_model = genai.GenerativeModel("gemini-pro-vision")
            prompt = "Extract the following details from this payslip image: Basic Pay, HRA, Special Allowance, Bonus, Other Income, EPF, Professional Tax, Net Salary. Return result in plain text."
            response = gemini_model.generate_content([prompt, image])
            text = response.text
        else:
            st.error("🔐 Gemini API key missing. Please set it in secrets or env variable.")
            text = ""

    if mask_data:
        for keyword in ["PAN", "UAN", "Bank Account No", "Employee Name", "Provident Fund No"]:
            text = re.sub(rf"(?i)({keyword}\s*:?.*)", f"{keyword}: ****", text)

    st.markdown("### 📄 Extracted Payslip Text")
    st.code(text[:1500])

    def extract_amount(label):
        pattern = rf"{label}.*?(\d{{1,3}}(?:,\d{{3}})*(?:\.\d{{2}})?)"
        match = re.search(pattern, text)
        return float(match.group(1).replace(",", "")) if match else 0

    payslip_data = {
        "Basic Pay": extract_amount("Basic"),
        "HRA": extract_amount("House Rent Allowance"),
        "Special Allowance": extract_amount("Special Allowance"),
        "Bonus": extract_amount("Bonus"),
        "Other Income": extract_amount("Medical Allowance|Other Income"),
        "EPF": extract_amount("Provident Fund"),
        "Professional Tax": extract_amount("Profession Tax")
    }

    net_match = re.search(r"Net Salary\s*[:\-]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)", text)
    if net_match:
        net_salary_from_payslip = float(net_match.group(1).replace(",", ""))

st.info("🔍 Click '💡 Calculate Tax' to compute your estimate.")

if st.button("💡 Calculate Tax"):
    if payslip_data and any(payslip_data.values()):
        st.info("📄 Using values from uploaded payslip.")
        basic = payslip_data["Basic Pay"]
        hra = payslip_data["HRA"]
        special = payslip_data["Special Allowance"]
        bonus = payslip_data["Bonus"]
        other = payslip_data["Other Income"]
        epf = payslip_data["EPF"]
        prof_tax = payslip_data["Professional Tax"]
    else:
        st.info("✍️ Using manually entered salary values.")

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
        slabs = [(300000, 0), (600000, 0.05), (900000, 0.1), (1200000, 0.15), (1500000, 0.2), (float('inf'), 0.3)]
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
        st.success(f"Estimated Tax under Old Regime: ₹{tax:,.0f}")
    elif regime_choice == "New":
        tax = tax_new(taxable_income)
        st.success(f"Estimated Tax under New Regime: ₹{tax:,.0f}")
    else:
        tax_old_val = tax_old(taxable_income)
        tax_new_val = tax_new(taxable_income)
        better = "Old" if tax_old_val < tax_new_val else "New"
        st.info(f"Old Regime: ₹{tax_old_val:,.0f} | New Regime: ₹{tax_new_val:,.0f}")
        st.success(f"✅ Better Option: **{better} Regime**")

        fig, ax = plt.subplots()
        ax.bar(["Old Regime", "New Regime"], [tax_old_val, tax_new_val], color=["#4CAF50", "#FF9800"])
        ax.set_title("Old vs New Regime Tax Comparison")
        ax.set_ylabel("Tax Amount (₹)")
        st.pyplot(fig)

        tax = min(tax_old_val, tax_new_val)

    if net_salary_from_payslip:
        take_home = net_salary_from_payslip * 12
        st.info("✅ Using net salary from uploaded payslip.")
    else:
        take_home = gross - tax - deductions

    st.markdown("### 💸 Estimated Take-Home")
    st.write(f"**Annual Take-Home Pay:** ₹{take_home:,.0f}")
    st.write(f"**Monthly Take-Home Pay:** ₹{take_home/12:,.0f}")

    with st.expander("💡 Money-Saving Tips"):
        if GEMINI_API_KEY:
            suggestion_prompt = f"Give 4 practical investment or money saving tips for a person earning ₹{take_home//12:.0f} monthly."
            gemini = genai.GenerativeModel("gemini-pro")
            suggestions = gemini.generate_content(suggestion_prompt).text
            st.markdown(suggestions)

            user_prompt = st.text_input("🧠 Ask Gemini for tailored advice (e.g., tax saving, budgeting, investments):")
            if user_prompt:
                custom = gemini.generate_content(user_prompt).text
                st.markdown(custom)
        else:
            st.markdown("""
            - Invest in **80C options**: ELSS, PPF, Term Insurance  
            - Use **80D** for health insurance (self & parents)  
            - Consider **NPS** for additional ₹50K deduction  
            - Track expenses with apps like Jupiter, Fi, Walnut  
            """)

# --- Guide Section ---
with st.expander("📌 How to Read Your Salary Slip?"):
    st.markdown("""
    - **Basic Pay**: Core salary used for PF & gratuity  
    - **HRA**: Tax benefit if rent is paid (40% or 50%)  
    - **Special Allowance**: Fully taxable  
    - **Bonus**: Performance-based and taxable  
    - **EPF**: Retirement saving (12% of basic)  
    - **Professional Tax**: Small state deduction  
    - **Other Income**: Any additional payments outside fixed salary, e.g., reimbursements or medical allowance.
    """)