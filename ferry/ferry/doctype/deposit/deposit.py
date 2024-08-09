# Copyright (c) 2024, Royalsmb and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint
from frappe.model.document import Document


class Deposit(Document):
	def after_insert(self):
		total_amount = cint(frappe.db.get_value("Customer", self.customer, "custom_customer_balance")) + cint(self.amount)
		frappe.db.set_value("Customer", self.customer, "custom_customer_balance", total_amount)
		frappe.db.commit()

