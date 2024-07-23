import frappe
from frappe.utils import flt, getdate, add_months
#Aqiq solution
@frappe.whitelist()
def get_payment_terms_customized(payment_method, payment_period_in_months, monthly_payment,terms_template, posting_date=None, start_date=None, period_frequency=None, grand_total=None, base_grand_total=None, deposit_amount=None, bill_date=None):
    term_details_object = get_payment_term_details_customized(
        payment_method, payment_period_in_months, monthly_payment, terms_template, posting_date, start_date, period_frequency, grand_total, base_grand_total, deposit_amount, bill_date
    )
    return term_details_object

@frappe.whitelist()
def get_payment_term_details_customized(payment_method, payment_period_in_months, monthly_payment, terms_template, posting_date=None, start_date=None, period_frequency=None, grand_total=None, base_grand_total=None, deposit_amount=None, bill_date=None):
    term_details_object = []
    total = 0.0
    next_payment_date = start_date
    
    grand_total = flt(grand_total)
    base_grand_total = flt(base_grand_total)
    deposit_amount = flt(deposit_amount)
    monthly_payment = flt(monthly_payment)
    period_frequency = int(period_frequency)

    if payment_method == "Payment Terms Template":
        terms_doc = frappe.get_doc("Payment Terms Template", terms_template)
        for term in terms_doc.get("terms"):
            term_details = frappe._dict()
            term_details.description = term.description
            term_details.invoice_portion = term.invoice_portion
            term_details.payment_amount = flt(term.invoice_portion) * grand_total / 100
            term_details.base_payment_amount = flt(term.invoice_portion) * base_grand_total / 100
            term_details.discount_type = term.discount_type
            term_details.discount = term.discount
            term_details.outstanding = term_details.payment_amount
            term_details.mode_of_payment = term.mode_of_payment

            if bill_date:
                term_details.due_date = get_due_date(term, bill_date)
                term_details.discount_date = get_discount_date(term, bill_date)
            elif posting_date:
                term_details.due_date = get_due_date(term, posting_date)
                term_details.discount_date = get_discount_date(term, posting_date)

            # Ensure due_date is not earlier than posting_date
            if posting_date and getdate(term_details.due_date) < getdate(posting_date):
                term_details.due_date = posting_date

            term_details_object.append(term_details)

    elif payment_method == "Pay Fixed Amount per Period":
        term_details = frappe._dict()
        term_details.payment_amount = deposit_amount
        term_details.base_payment_amount = deposit_amount
        term_details.outstanding = deposit_amount
        term_details.due_date = posting_date
        term_details_object.append(term_details)

        next_payment_date = add_months(posting_date, period_frequency)
        remaining = grand_total - deposit_amount
        while remaining > 0:
            term_details = frappe._dict()
            payment_amount = min(monthly_payment, remaining)
            remaining -= payment_amount

            term_details.payment_amount = payment_amount
            term_details.base_payment_amount = payment_amount
            term_details.outstanding = payment_amount
            term_details.due_date = next_payment_date
            term_details_object.append(term_details)
            
            next_payment_date = add_months(next_payment_date, period_frequency)
            total += payment_amount

    elif payment_method == "Pay Over Number of Periods":
        term_details = frappe._dict()
        term_details.payment_amount = deposit_amount
        term_details.base_payment_amount = deposit_amount
        term_details.outstanding = deposit_amount
        term_details.due_date = posting_date
        term_details_object.append(term_details)
        
        remaining = grand_total - deposit_amount
        no_of_periods = int(payment_period_in_months)
        installments_amount = remaining
        while remaining > 0:
            term_details = frappe._dict()
            payment_amount = installments_amount / no_of_periods
            remaining -= payment_amount

            term_details.payment_amount = payment_amount
            term_details.base_payment_amount = payment_amount
            term_details.outstanding = payment_amount
            term_details.due_date = next_payment_date
            term_details_object.append(term_details)

            next_payment_date = add_months(next_payment_date, period_frequency)

    return term_details_object

def get_due_date(term, base_date):
    # Implement your logic here to calculate the due date based on the term and base_date
    # Example logic:
    return add_months(base_date, term.months)

def get_discount_date(term, base_date):
    # Implement your logic here to calculate the discount date based on the term and base_date
    # Example logic:
    return add_months(base_date, term.months)
