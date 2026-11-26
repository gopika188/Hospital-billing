def validate_patient_record(patient, policy):
    """Validate required fields, non-negative charges, and policy constraints."""
    errors = []

    required_fields = ["patient_id", "name", "age", "category", "consultation", "diagnostics", "treatment", "amount_paid"]
    for field in required_fields:
        if field not in patient:
            errors.append(f"Missing field: {field}")

    if errors:
        return False, errors

    if patient["age"] < 0 or patient["age"] > 120:
        errors.append("Age must be between 0 and 120.")

    for charge_field in ["consultation", "diagnostics", "treatment", "amount_paid"]:
        if patient[charge_field] < 0:
            errors.append(f"{charge_field} cannot be negative.")

    if patient["category"] not in policy["concession_rates"]:
        errors.append(f"Unknown patient category: {patient['category']}")

    gross_bill = patient["consultation"] + patient["diagnostics"] + patient["treatment"]
    if gross_bill <= 0:
        errors.append("Total service charges must be greater than zero.")

    if patient["amount_paid"] > gross_bill:
        errors.append("Amount paid cannot exceed gross bill.")

    return len(errors) == 0, errors


def calculate_concession(patient, gross_bill, policy):
    """Apply conditional concessions based on category, age, and bill threshold."""
    category = patient["category"]
    base_rate = policy["concession_rates"].get(category, 0.0)

    # Extra senior citizen concession if age >= 60 and not already senior category
    extra_rate = 0.0
    if patient["age"] >= 60 and category != "senior":
        extra_rate += policy["senior_extra_rate"]

    # High-bill relief if gross bill exceeds threshold
    if gross_bill >= policy["high_bill_threshold"]:
        extra_rate += policy["high_bill_extra_rate"]

    total_rate = min(base_rate + extra_rate, policy["max_concession_cap"])
    concession_amount = round(gross_bill * total_rate, 2)
    net_payable = round(gross_bill - concession_amount, 2)

    return total_rate, concession_amount, net_payable


def classify_patient(net_payable, amount_paid, days_overdue, policy):
    """Classify patient payment status according to supplied payment policy."""
    balance_due = round(net_payable - amount_paid, 2)

    if balance_due <= 0.0:
        classification = "Settled / Fully Paid"
    elif amount_paid == 0.0 and days_overdue > policy["overdue_grace_days"]:
        classification = "Defaulter - Unpaid Overdue"
    elif amount_paid == 0.0:
        classification = "Pending - Zero Payment"
    elif days_overdue > policy["overdue_grace_days"]:
        classification = "Partial Payment - Overdue"
    elif amount_paid >= net_payable * policy["partial_threshold_ratio"]:
        classification = "Partial Payment - On Track"
    else:
        classification = "Partial Payment - Low Installment"

    return max(balance_due, 0.0), classification


def process_patients(patients, policy):
    """Process a list of patient records, print reports, and return structured results."""
    results = []

    for patient in patients:
        is_valid, errors = validate_patient_record(patient, policy)
        if not is_valid:
            print(f"\n[INVALID RECORD] ID: {patient.get('patient_id', 'N/A')} | Errors: {', '.join(errors)}")
            continue

        gross_bill = round(patient["consultation"] + patient["diagnostics"] + patient["treatment"], 2)
        rate, concession, net_payable = calculate_concession(patient, gross_bill, policy)
        days_overdue = patient.get("days_overdue", 0)
        balance_due, status = classify_patient(net_payable, patient["amount_paid"], days_overdue, policy)

        record = {
            "patient_id": patient["patient_id"],
            "name": patient["name"],
            "gross_bill": gross_bill,
            "concession_pct": round(rate * 100, 1),
            "concession": concession,
            "net_payable": net_payable,
            "amount_paid": round(patient["amount_paid"], 2),
            "balance_due": balance_due,
            "classification": status,
        }
        results.append(record)

    print("\n--- Hospital Billing & Patient Classification Summary ---")
    print(f"{'ID':<7} {'Name':<14} {'Gross':>8} {'Conc%':>6} {'NetPay':>9} {'Paid':>8} {'Due':>8} {'Classification'}")
    print("-" * 92)
    for r in results:
        print(
            f"{r['patient_id']:<7} {r['name']:<14} {r['gross_bill']:>8.2f} "
            f"{r['concession_pct']:>5.1f}% {r['net_payable']:>9.2f} {r['amount_paid']:>8.2f} "
            f"{r['balance_due']:>8.2f} {r['classification']}"
        )

    return results


def main():
    payment_policy = {
        "concession_rates": {
            "general": 0.00,
            "senior": 0.15,
            "ews": 0.30,        # Economically Weaker Section
            "staff": 0.25,
        },
        "senior_extra_rate": 0.05,
        "high_bill_threshold": 25000.0,
        "high_bill_extra_rate": 0.05,
        "max_concession_cap": 0.40,
        "overdue_grace_days": 15,
        "partial_threshold_ratio": 0.50,
    }

    sample_patients = [
        {
            "patient_id": "P101",
            "name": "Ananya Rao",
            "age": 29,
            "category": "general",
            "consultation": 800,
            "diagnostics": 2200,
            "treatment": 4000,
            "amount_paid": 7000,
            "days_overdue": 0,
        },
        {
            "patient_id": "P102",
            "name": "Rameshwar Nair",
            "age": 68,
            "category": "senior",
            "consultation": 600,
            "diagnostics": 5400,
            "treatment": 22000,
            "amount_paid": 14000,
            "days_overdue": 5,
        },
        {
            "patient_id": "P103",
            "name": "Kiran Das",
            "age": 42,
            "category": "ews",
            "consultation": 500,
            "diagnostics": 1500,
            "treatment": 8000,
            "amount_paid": 0,
            "days_overdue": 22,
        },
        {
            "patient_id": "P104",
            "name": "Meera Kulkarni",
            "age": 35,
            "category": "staff",
            "consultation": 400,
            "diagnostics": 1600,
            "treatment": 6000,
            "amount_paid": 1500,
            "days_overdue": 4,
        },
        {
            "patient_id": "P105",
            "name": "Invalid Entry",
            "age": 30,
            "category": "general",
            "consultation": -200,
            "diagnostics": 1000,
            "treatment": 2000,
            "amount_paid": 500,
            "days_overdue": 0,
        },
    ]

    process_patients(sample_patients, payment_policy)


if __name__ == "__main__":
    main()
