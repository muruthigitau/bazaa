# Copyright (c) 2025, David Gitau and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.xlsxutils import make_xlsx
from frappe.utils.file_manager import save_file
import io

class CuttingList(Document):
	def on_submit(self):
		self.send_cutting_list_excel()

	def send_cutting_list_excel(self):
		# Get default email from Sales Settings
		default_email = frappe.db.get_single_value("Sales Settings", "default_email")
		if not default_email:
			frappe.msgprint("No default email configured in Sales Settings.")
			return

		# Prepare top section - customer data
		customer_data = [
			["Customer Name", self.customer_name or ""],
			["Phone", self.customer_phone or ""],
			["Email", self.customer_email or ""],
			["Board Type", self.board_type or ""]
		]

		# Prepare item headers
		item_headers = ["Length", "Width", "Qty", "Description",
						"Edging L1", "Edging L2", "Edging W1", "Edging W2",
						"Grooves L1", "Grooves L2", "Grooves W1", "Grooves W2"]

		# Prepare item data rows
		item_rows = []
		for item in self.items:
			item_rows.append([
				item.length,
				item.width,
				item.qty,
				item.description,
				1 if item.edging_l1 else 0,
				1 if item.edging_l2 else 0,
				1 if item.edging_w1 else 0,
				1 if item.edging_w2 else 0,
				1 if item.grooves_l1 else 0,
				1 if item.grooves_l2 else 0,
				1 if item.grooves_w1 else 0,
				1 if item.grooves_w2 else 0
			])

		# Combine all into one sheet
		data = customer_data + [[""]] + [item_headers] + item_rows

		# Create Excel file as BytesIO
		file_content = make_xlsx(data, "Cutting List")

		# Save to File doctype
		file_name = f"Cutting List - {self.name}.xlsx"
		saved_file = save_file(file_name, file_content.getvalue(), self.doctype, self.name, is_private=True)

		# Send email immediately
		frappe.sendmail(
			recipients=[default_email],
			subject=f"Cutting List: {self.name}",
			message="Please find the attached cutting list.",
			attachments=[{
				"fname": file_name,
				"fcontent": file_content.getvalue()
			}],
			delayed=False  # <-- This makes it send immediately
		)

		frappe.msgprint(f"Cutting list sent to {default_email}")
