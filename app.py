import streamlit as st

# Title and intro
st.title("💰 Salary Simplified – Understand Your Payslip & Tax Liability")
st.markdown("This tool helps you break down your salary, compare Old vs New tax regimes, and estimate your take-home.")

# Sidebar – Inputs
st.sidebar.header("Enter Your Monthly Salary Details")
basic = st.sidebar.number_input("Basic Pay", min_value=0)
hra = st.sidebar.number_input("House Rent Allowance (HRA)", min_value=0)
special = st.sidebar.number_input("Special Allowance", min_value=0)
bonus = st.sidebar.number_input("Bonus / Variable Pay", min_value=0)
other = st.sidebar.number_input("Other Income", min_value=0)

epf = st.sidebar.number_input("EPF Deduction (Monthly)", min_value=0)
prof_tax = st.sidebar.number_input("Professional Tax (Monthly)", min_value=0)
age = st.sidebar.selectbox("Your Age Bracket", ["<60", "60-80", ">80"])
regime_choice = st.sidebar.radio("Choose Tax Regime", ["Old", "New", "Compare Both"])

if st.sidebar.button("Calculate Tax"):
    # Convert to annual values
    gross = 12 * (basic + hra + special + bonus + other)
    deductions = 12 * (epf + prof_tax)
    std_deduction = 50000
    total_deductions = deductions + std_deduction
    taxable_income = max(0, gross - total_deductions)

    # Define slabs
    def tax_old(income):
        tax = 0
        if age == "<60":
            slabs = [(250000, 0), (500000, 0.05), (1000000, 0.2), (float('inf'), 0.3)]
        elif age == "60-80":
            slabs = [(300000, 0), (500000, 0.05), (1000000, 0.2), (float('inf'), 0.3)]
        else:
            slabs = [(500000, 0), (1000000, 0.2), (float('inf'), 0.3)]

        prev = 0
        for limit, rate in slabs:
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
    st.write(f"**Total Deductions (EPF + Prof Tax + Standard ₹50K):** ₹{total_deductions:,.0f}")
    st.write(f"**Taxable Income:** ₹{taxable_income:,.0f}")

    # Compare Regimes
    if regime_choice == "Old":
        tax = tax_old(taxable_income)
        st.success(f"Estimated Tax Payable under **Old Regime**: ₹{tax:,.0f}")
    elif regime_choice == "New":
        tax = tax_new(gross)
        st.success(f"Estimated Tax Payable under **New Regime**: ₹{tax:,.0f}")
    else:
        tax_old_val = tax_old(taxable_income)
        tax_new_val = tax_new(gross)
        st.info(f"Old Regime Tax: ₹{tax_old_val:,.0f}")
        st.info(f"New Regime Tax: ₹{tax_new_val:,.0f}")
        if tax_old_val < tax_new_val:
            st.success("💡 Better to go with **Old Regime** ✅")
        else:
            st.success("💡 Better to go with **New Regime** ✅")

    # Take-home estimation
    final_tax = min(tax_old_val, tax_new_val) if regime_choice == "Compare Both" else tax
    in_hand_annual = gross - final_tax - deductions
    st.subheader("🪙 Estimated Take-Home")
    st.write(f"**Annual Take-Home Pay:** ₹{in_hand_annual:,.0f}")
    st.write(f"**Monthly Take-Home Pay:** ₹{in_hand_annual/12:,.0f}")
