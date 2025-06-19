import streamlit as st

st.set_page_config(page_title="Salary Simplified", page_icon="💰")

st.title("💰 Salary Simplified – Understand Your Payslip & Tax Liability")
st.markdown("This tool helps you break down your salary, compare Old vs New tax regimes, and estimate your take-home.")

st.sidebar.header("📥 Enter Your Monthly Salary Details")
basic = st.sidebar.number_input("Basic Pay", min_value=0)
hra = st.sidebar.number_input("House Rent Allowance (HRA)", min_value=0)
special = st.sidebar.number_input("Special Allowance", min_value=0)
bonus = st.sidebar.number_input("Bonus / Variable Pay", min_value=0)
other = st.sidebar.number_input("Other Income", min_value=0)

epf = st.sidebar.number_input("EPF Deduction (Monthly)", min_value=0)
prof_tax = st.sidebar.number_input("Professional Tax (Monthly)", min_value=0)
age = st.sidebar.selectbox("Your Age Bracket", ["<60", "60-80", ">80"])
regime_choice = st.sidebar.radio("Choose Tax Regime", ["Old", "New", "Compare Both"])

if st.sidebar.button("💡 Calculate Tax"):
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

    take_home = gross - tax - deductions
    st.subheader("💸 Estimated Take-Home")
    st.write(f"**Annual Take-Home Pay:** ₹{take_home:,.0f}")
    st.write(f"**Monthly Take-Home Pay:** ₹{take_home/12:,.0f}")


