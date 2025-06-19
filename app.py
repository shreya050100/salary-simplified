import streamlit as st
import matplotlib.pyplot as plt

# Page configuration
st.set_page_config(page_title="Salary Simplified", page_icon="💰", layout="centered")

# App header
with st.container():
    st.markdown("<h1 style='text-align: center;'>💰 Salary Simplified – Understand Your Payslip & Tax Liability</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>This tool helps you break down your salary, compare Old vs New tax regimes, and estimate your take-home.</p>", unsafe_allow_html=True)

# Sidebar inputs
with st.sidebar:
    st.header("📥 Enter Your Monthly Salary Details")
    basic = st.number_input("Basic Pay", min_value=0)
    
    # Auto-calculated HRA
    hra = 0.4 * basic
    st.caption(f"HRA auto-calculated as 40% of Basic Pay: ₹{hra:,.0f}")
    
    special = st.number_input("Special Allowance", min_value=0)
    bonus = st.number_input("Bonus / Variable Pay", min_value=0)
    other = st.number_input("Other Income", min_value=0)
    
    epf = st.number_input("EPF Deduction (Monthly)", min_value=0)
    prof_tax = st.number_input("Professional Tax (Monthly)", min_value=0)
    
    age = st.selectbox("Your Age Bracket", ["<60", "60-80", ">80"])
    regime_choice = st.radio("Choose Tax Regime", ["Old", "New", "Compare Both"])
    calculate = st.button("💡 Calculate Tax")

# Main logic
if calculate:
    gross = 12 * (basic + hra + special + bonus + other)
    deductions = 12 * (epf + prof_tax)
    std_deduction = 50000
    total_deductions = deductions + std_deduction
    taxable_income = max(0, gross - total_deductions)

    def tax_old(income):
        tax = 0
        slabs = {
            "<60": [(250000, 0), (500000, 0.05), (1000000, 0.2), (float('inf'), 0.3)],
            "60-80": [(300000, 0), (500000, 0.05), (1000000, 0.2), (float('inf'), 0.3)],
            ">80": [(500000, 0), (1000000, 0.2), (float('inf'), 0.3)]
        }
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
        slabs = [(300000, 0), (600000, 0.05), (900000, 0.1),
                 (1200000, 0.15), (1500000, 0.2), (float('inf'), 0.3)]
        prev = 0
        tax = 0
        for limit, rate in slabs:
            if income > limit:
                tax += (limit - prev) * rate
                prev = limit
            else:
                tax += (income - prev) * rate
                break
        return round(tax)

    st.subheader("📊 Breakdown")

    col1, col2 = st.columns(2)
    col1.metric("Gross Annual Income", f"₹{gross:,.0f}")
    col2.metric("Taxable Income", f"₹{taxable_income:,.0f}")

    if regime_choice == "Old":
        tax = tax_old(taxable_income)
        st.success(f"Estimated Tax under Old Regime: ₹{tax:,.0f}")
    elif regime_choice == "New":
        tax = tax_new(gross)
        st.success(f"Estimated Tax under New Regime: ₹{tax:,.0f}")
    else:
        tax_old_val = tax_old(taxable_income)
        tax_new_val = tax_new(gross)
        st.info(f"Old Regime: ₹{tax_old_val:,.0f} | New Regime: ₹{tax_new_val:,.0f}")
        better = "Old" if tax_old_val < tax_new_val else "New"
        st.success(f"✅ Better Option: **{better} Regime**")

        # Bar Chart
        fig, ax = plt.subplots()
        ax.bar(["Old Regime", "New Regime"], [tax_old_val, tax_new_val], color=["green", "orange"])
        ax.set_ylabel("Tax Amount (₹)")
        ax.set_title("Old vs New Regime Tax Comparison")
        st.pyplot(fig)
        tax = min(tax_old_val, tax_new_val)

    take_home = gross - tax - deductions

    st.subheader("💸 Estimated Take-Home")
    st.write(f"**Annual Take-Home Pay:** ₹{take_home:,.0f}")
    st.write(f"**Monthly Take-Home Pay:** ₹{take_home / 12:,.0f}")

    # Expanders for extra help
    with st.expander("💡 Money-Saving Tips"):
        st.markdown("""
        - Invest in **Section 80C** instruments (ELSS, PPF, etc.)
        - Maximize **EPF** and **NPS** contributions
        - Use **HRA exemptions** if you're renting
        - Consider **medical insurance** (Section 80D)
        """)

    with st.expander("📘 How to Read Your Salary Slip?"):
        st.markdown("""
        - **Basic Pay**: Fixed core salary
        - **HRA**: For renting house accommodation (exemptions available)
        - **Special Allowance**: Miscellaneous compensation
        - **EPF**: Mandatory employee retirement contribution
        - **Professional Tax**: State-based deduction
        """)

