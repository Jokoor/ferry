import frappe
from frappe.utils import cint
from frappe.utils.print_format import download_pdf, download_multi_pdf
import requests
import os
from frappe.utils import get_files_path
from frappe import _
import json
from frappe.utils import random_string

from frappe.utils.file_manager import save_file

@frappe.whitelist()
def get_pdf_url(file_url):
    url = frappe.utils.get_url(file_url)
    return url


@frappe.whitelist()
def generate_multi_pdf_url(doctype, no_letterhead=0, letterhead=None, options=None):
    # Check if doctype is a dictionary
    name = "POS Invoice"  # Adjust if needed
    if isinstance(doctype, str):
        # If doctype is a JSON string, load it as a dictionary
        try:
            doctype = json.loads(doctype)
        except json.JSONDecodeError:
            frappe.throw("Invalid JSON format for 'doctype'")
    
    # Ensure 'doctype' is a dictionary with the correct format
    if not isinstance(doctype, dict) or len(doctype) != 1:
        frappe.throw("Invalid 'doctype' format. Expected a dictionary with one key-value pair.")
    
    key, names = next(iter(doctype.items()))
    
    if not isinstance(key, str) or not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        frappe.throw("Invalid 'doctype' value. The key should be a string and the value should be a list of strings.")
    
    # Ensure 'name' is a string
    if not isinstance(name, str):
        frappe.throw("Invalid type for 'name', expected a string.")
    
    # Generate the combined PDF content by calling the download_multi_pdf function
    try:
        format = "POS Invoice"  # Adjust if needed
        download_multi_pdf(doctype, name, format, no_letterhead, letterhead, options)
        pdf_content = frappe.local.response.filecontent
        
        if not pdf_content:
            raise ValueError("PDF content is empty or not generated correctly.")
        
        # Construct the filename
        name_str = name.replace(" ", "-").replace("/", "-")
        filename = f"combined_{name_str}.pdf"
        
        # Save the PDF content as a File document in the database
        _file = frappe.get_doc({
            "doctype": "File",
            "file_name": filename,
            "is_private": 0,
            "content": pdf_content
        })
        _file.save()
        frappe.db.commit()
        
    
    except Exception as e:
        frappe.log_error(f"Error generating PDF URL: {str(e)}")
        frappe.throw(f"Failed to generate PDF: {str(e)}")


@frappe.whitelist()
def generate_pdf_url(doctype, name, format=None, no_letterhead=0, language=None, letterhead=None):
    # Call the existing download_pdf function
    download_pdf(doctype, name, format, None, no_letterhead, language, letterhead)

    # Access the PDF content from the response
    pdf_content = frappe.local.response.filecontent

    # Construct the filename and filepath
    filename = "{name}.pdf".format(name=name.replace(" ", "-").replace("/", "-"))
    filepath = os.path.join(get_files_path(), filename)

    _file = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        "is_private": 0,
        "content": pdf_content
    })
    _file.save()
    frappe.db.commit()

    # Return the file URL
    file_url = _file.file_url
    return {
        "status": "success",
        "message": _("PDF generated successfully"),
        "file_url": file_url
    }




#create sales invoice
@frappe.whitelist()
def make_sales_invoice(customer, qty, rate):
    # check if ticket id exists
    if not frappe.db.exists("Customer", customer):
         return 0
    customer_doc = frappe.get_doc("Customer", customer)
       
    customer_balance = cint(customer_doc.custom_customer_balance)
    if customer_balance < (float(rate) * cint(qty)):
        return 1
    else:
        doc = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": customer,
            "items": [
                {
                    "item_code": "Passenger Ticket",
                    "qty": qty,
                    "rate": rate
                }
            ]
        })
        doc.insert()
        doc.submit()
        remaining_balance = customer_balance - (float(rate) * cint(qty))

        frappe.db.set_value("Customer", customer, "custom_customer_balance", remaining_balance)
        frappe.db.commit()
        make_payment(doc.name)
        pdf_url = generate_pdf_url("Sales Invoice", doc.name, format="POS Invoice")
        # impor
        return "success"
#create payment entry
def make_payment(inv):
    inv = frappe.get_doc("Sales Invoice", inv)
    doc = frappe.get_doc({
        "doctype": "Payment Entry",
        "payment_type": "Receive",
        "posting_date": inv.posting_date,
        "party_type": "Customer",
        "party": inv.customer,
        "paid_amount": inv.grand_total,
        "received_amount": inv.grand_total,
        "mode_of_payment": "Cash",
        "paid_from": "Debtors - GFS",
        "paid_to": "Bank Account - GFS",
        "reference_no": inv.name,
        "reference_date":inv.posting_date,
        "references": [
            {
                "reference_doctype": "Sales Invoice",
                "reference_name": inv.name,
                "total_amount": inv.grand_total,
                "outstanding_amount": 0,
                "allocated_amount": inv.grand_total
            }
        ]
        


        })
    doc.insert()
    doc.submit()
    frappe.db.commit()
#validte custome rbalanc
@frappe.whitelist()
def validate_balance(customer, amount):
    balance = frappe.db.get_value("Customer", customer, "custom_customer_balance")
    if float(balance) < float(amount):
        return "Customer is low in balance, please refill your card"

