import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Salary Simplified", page_icon="💰")

st.title("💰 Salary Simplified – Understand Your Payslip & Tax Liability")
st.markdown("This tool helps you break down your salary, compare Old vs New tax regimes, and estimate your take-home.")

with st.expander("📥 Enter Your Monthly Salary Details"):
    basic = st.number_input("Basic Pay", min_value=0, value=30000)
    metro = st.checkbox("🏙️ I live in a Metro City (for higher HRA exemption)", value=False)
    auto_hra = round(0.5 * basic) if metro else round(0.4 * basic)

    use_auto_hra = st.checkbox(f"🧮 Auto-calculate HRA ({'50%' if metro else '40%'} of Basic)", value=True)
    hra = st.number_input("House Rent Allowance (HRA)", min_value=0, value=auto_hra if use_auto_hra else 0)

    special = st.number_input("Special Allowance", min_value=0, value=5000)
    bonus = st.number_input("Bonus / Variable Pay", min_value=0, value=2000)
    other = st.number_input("Other Income", min_value=0, value=1000)

with st.expander("📉 Monthly Deductions"):
    epf = st.number_input("EPF Contribution", min_value=0, value=1800)
    prof_tax = st.number_input("Professional Tax", min_value=0, value=200)

st.markdown("### 📊 Choose Your Tax Regime & Age Bracket")
col1, col2 = st.columns(2)
with col1:
    age = st.selectbox("Your Age", ["<60", "60-80", ">80"])
with col2:
    regime_choice = st.radio("Tax Regime", ["Old", "New", "Compare Both"])

uploaded_file = st.file_uploader("📤 Upload your salary slip (.csv)", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("File Uploaded Successfully!")
    st.dataframe(df.head())

st.info("👈 Enter values above and click '💡 Calculate Tax' to see your results.")

_, center, _ = st.columns([1, 2, 1])
with center:
    if st.button("💡 Calculate Tax"):
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

        st.subheader("📊 Salary & Tax Breakdown")
        st.write(f"**Gross Annual Income:** ₹{gross:,.0f}")
        st.write(f"**Total Deductions (incl. Std ₹50K):** ₹{total_deductions:,.0f}")
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
            st.info(f"Old Regime: ₹{tax_old_val:,.0f} | New Regime: ₹{tax_new_val:,.0f}")
            better = "Old" if tax_old_val < tax_new_val else "New"
            st.success(f"✅ Better Option: **{better} Regime**")
            tax = min(tax_old_val, tax_new_val)

            # Chart
            fig, ax = plt.subplots()
            ax.bar(["Old Regime", "New Regime"], [tax_old_val, tax_new_val], color=["#4CAF50", "#FF9800"])
            ax.set_ylabel("Tax Amount (₹)")
            ax.set_title("Old vs New Regime Tax Comparison")
            st.pyplot(fig)

        take_home = gross - tax - deductions
        st.subheader("💸 Estimated Take-Home")
        st.write(f"**Annual Take-Home Pay:** ₹{take_home:,.0f}")
        st.write(f"**Monthly Take-Home Pay:** ₹{take_home/12:,.0f}")

        with st.expander("💡 Money-Saving Tips"):
            st.markdown("""
            - Invest in **80C options**: ELSS, PPF, Term Insurance
            - Use **80D** for health insurance (self & parents)
            - Consider **NPS** for additional ₹50K deduction
            - Track expenses with apps like Jupiter, Fi, Walnut
            """)

with st.expander("🧾 How to Read Your Salary Slip?"):
    st.markdown("""
    - **Basic Pay**: Core salary used for PF & gratuity calculations.
    - **HRA**: House Rent Allowance — partially tax-free if you pay rent. Usually:
        - 40% of Basic Pay for non-metro cities
        - 50% of Basic Pay for metro cities (Mumbai, Delhi, Chennai, Kolkata, Bengaluru, Hyderabad)
    - **Special Allowance**: Fully taxable portion of salary.
    - **Bonus**: May be variable or performance-based; taxable.
    - **Deductions**:
      - **EPF**: Contributes to your retirement fund (12% basic).
      - **Professional Tax**: State-based small tax deducted monthly.
      - **Income Tax**: Based on regime selected and income.
    """)
