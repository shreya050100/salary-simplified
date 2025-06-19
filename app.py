import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pdfplumber

# Set wide layout for full-width containers
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

# --- File Upload (optional) ---
uploaded_file = st.file_uploader("📤 Upload Salary Slip (.csv or .pdf)", type=["csv", "pdf"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
        st.success("CSV File Uploaded Successfully!")
        st.dataframe(df.head())

    elif uploaded_file.name.endswith(".pdf"):
        st.success("PDF File Uploaded Successfully!")
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        st.text_area("📄 Extracted Text from PDF", text, height=300)
# After reading the CSV and displaying df.head(), extract highlights
if uploaded_file.name.endswith(".csv"):
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
    
    st.success("✅ File Uploaded Successfully!")

    # Optional preview
    with st.expander("📄 View Uploaded Data"):
        st.dataframe(df.head())

    # Extract and show salary summary (replace with exact column names from your CSV)
    st.markdown("### 📌 Payslip Summary")
    st.markdown("""
    <div style="background-color:#1e1e1e;padding:20px;border-radius:10px">
    <h4 style='color:#ffcc00'>👤 Name:</h4>
    <p style='margin-left:10px;'>Shreya Verma</p>

    <h4 style='color:#ffcc00'>💼 Designation:</h4>
    <p style='margin-left:10px;'>Global Marketing Associate</p>

    <h4 style='color:#ffcc00'>🏦 Bank A/C:</h4>
    <p style='margin-left:10px;'>HDFC - ****7222</p>

    <h4 style='color:#ffcc00'>🧾 Earnings:</h4>
    <p style='margin-left:10px;'>Basic: ₹23,269 | HRA: ₹11,635 | Conv. Allow.: ₹800 | Medical: ₹1,250 | Other: ₹9,344</p>

    <h4 style='color:#ffcc00'>💸 Deductions:</h4>
    <p style='margin-left:10px;'>EPF: ₹2,792 | PT: ₹200 | Other: ₹0</p>

    <h4 style='color:#4CAF50'>🟢 Net Take-Home: ₹67,480</h4>
    </div>
    """, unsafe_allow_html=True)


st.info("👉 Click '💡 Calculate Tax' to compute your estimate.")

# --- Tax Calculation ---
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

    # --- Output ---
    st.markdown("### 📊 Salary & Tax Breakdown")
    st.write(f"**Gross Annual Income:** ₹{gross:,.0f}")
    st.write(f"**Total Deductions (incl. ₹50K std):** ₹{total_deductions:,.0f}")
    st.write(f"**Taxable Income:** ₹{taxable_income:,.0f}")

    if regime_choice == "Old":
        tax = tax_old(taxable_income)
        st.success(f"Estimated Tax under Old Regime: ₹{tax:,.0f}")
    elif regime_choice == "New":
        tax = tax_new(gross)
        st.success(f"Estimated Tax under New Regime: ₹{tax:,.0f}")
    else:
        tax_old_val = tax_old(taxable_income)
        tax_new_val = tax_new(gross)
        better = "Old" if tax_old_val < tax_new_val else "New"
        st.info(f"Old Regime: ₹{tax_old_val:,.0f} | New Regime: ₹{tax_new_val:,.0f}")
        st.success(f"✅ Better Option: **{better} Regime**")
        tax = min(tax_old_val, tax_new_val)

        # --- Bar Chart ---
        fig, ax = plt.subplots()
        ax.bar(["Old Regime", "New Regime"], [tax_old_val, tax_new_val], color=["#4CAF50", "#FF9800"])
        ax.set_title("Old vs New Regime Tax Comparison")
        ax.set_ylabel("Tax Amount (₹)")
        st.pyplot(fig)

    take_home = gross - tax - deductions
    st.markdown("### 💸 Estimated Take-Home")
    st.write(f"**Annual Take-Home Pay:** ₹{take_home:,.0f}")
    st.write(f"**Monthly Take-Home Pay:** ₹{take_home/12:,.0f}")

    with st.expander("💡 Money-Saving Tips"):
        st.markdown("""
        - Invest in **80C options**: ELSS, PPF, Term Insurance  
        - Use **80D** for health insurance (self & parents)  
        - Consider **NPS** for additional ₹50K deduction  
        - Track expenses with apps like Jupiter, Fi, Walnut  
        """)

# --- Guide Section ---
with st.expander("🧾 How to Read Your Salary Slip?"):
    st.markdown("""
    - **Basic Pay**: Core salary used for PF & gratuity  
    - **HRA**: Tax benefit if rent is paid (40% or 50%)  
    - **Special Allowance**: Fully taxable  
    - **Bonus**: Performance-based and taxable  
    - **EPF**: Retirement saving (12% of basic)  
    - **Professional Tax**: Small state deduction  
    """)
