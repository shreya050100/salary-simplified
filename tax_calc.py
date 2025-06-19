def calculate_tax_old(income, deductions, age):
    taxable = income - deductions - 50000  # Standard deduction
    tax = 0

    if age == "<60":
        slabs = [(250000, 0), (500000, 0.05), (1000000, 0.2), (float('inf'), 0.3)]
    elif age == "60-80":
        slabs = [(300000, 0), (500000, 0.05), (1000000, 0.2), (float('inf'), 0.3)]
    else:
        slabs = [(500000, 0), (1000000, 0.2), (float('inf'), 0.3)]

    prev = 0
    for limit, rate in slabs:
        if taxable > limit:
            tax += (limit - prev) * rate
            prev = limit
        else:
            tax += (taxable - prev) * rate
            break

    return round(tax)

def calculate_tax_new(income, age):
    slabs = [(300000, 0), (600000, 0.05), (900000, 0.10), (1200000, 0.15), (1500000, 0.20), (float('inf'), 0.30)]
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
