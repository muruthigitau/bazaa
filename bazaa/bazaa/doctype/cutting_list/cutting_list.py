# Copyright (c) 2025, David Gitau and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.file_manager import save_file
import io
import csv
from datetime import datetime

class CuttingList(Document):
	def autoname(self):
		# Get current date and time in format DDMMYYhhmm
		current_datetime = datetime.now().strftime("%d%m%y%H%M")
		
		# Create document name according to format Name#BoardType#dayandtime
		document_name = f"{self.customer_name}#{self.board_type or ''}#{self.customer_phone}#{current_datetime}"
		self.name = document_name  # Set the name of the document

	def on_submit(self):
		self.send_cutting_list_csv()

	def send_cutting_list_csv(self):
		# Get default email from Sales Settings
		default_email = frappe.db.get_single_value("Sales Settings", "default_email")
		if not default_email:
			frappe.msgprint("No default email configured in Sales Settings.")
			return


		# Prepare item headers
		item_headers = ["Length", "Width", "Qty",
						"Edging L1", "Edging L2", "Edging W1", "Edging W2",
						"Grooves L1", "Grooves L2", "Grooves W1", "Grooves W2", "Description"]

		# Prepare item data rows
		item_rows = []
		for item in self.items:
			item_rows.append([
				item.length,
				item.width,
				item.qty,
				1 if item.edging_l1 else 0,
				1 if item.edging_l2 else 0,
				1 if item.edging_w1 else 0,
				1 if item.edging_w2 else 0,
				1 if item.grooves_l1 else 0,
				1 if item.grooves_l2 else 0,
				1 if item.grooves_w1 else 0,
				1 if item.grooves_w2 else 0,
				item.description,
			])

		# Create CSV file as StringIO
		csv_buffer = io.StringIO()
		csv_writer = csv.writer(csv_buffer)
		csv_writer.writerow(item_headers)
		csv_writer.writerows(item_rows)
		
		# Convert to bytes for file saving
		file_content = io.BytesIO(csv_buffer.getvalue().encode('utf-8'))

		# Save to File doctype
		file_name = f"{self.name}.csv"
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
