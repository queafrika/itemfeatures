from erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle import SerialandBatchBundle, get_available_serial_nos, SerialNoWarehouseError, SerialNoDuplicateError
import frappe
from frappe.utils import bold

class ExtSerialandBatchBundle(SerialandBatchBundle):

	def validate_serial_nos_inventory(self):
		if not (self.has_serial_no and self.type_of_transaction == "Outward"):
			return

		serial_nos = [d.serial_no for d in self.entries if d.serial_no]
		kwargs = {
			"item_code": self.item_code,
			"warehouse": self.warehouse,
			"check_serial_nos": True,
			"serial_nos": serial_nos,
			"ignore_feature": 1
		}

		if self.voucher_type == "POS Invoice":
			kwargs["ignore_voucher_nos"] = [self.voucher_no]

		available_serial_nos = get_available_serial_nos(frappe._dict(kwargs))

		serial_no_warehouse = {}
		for data in available_serial_nos:
			if data.serial_no not in serial_nos:
				continue

			serial_no_warehouse[data.serial_no] = data.warehouse

		for serial_no in serial_nos:
			if not serial_no_warehouse.get(serial_no) or serial_no_warehouse.get(serial_no) != self.warehouse:
				self.throw_error_message(
					f"Serial No {bold(serial_no)} is not present in the warehouse {bold(self.warehouse)}.",
					SerialNoWarehouseError,
				)


	def validate_serial_nos_duplicate(self):
		# Don't inward same serial number multiple times
		if self.voucher_type in ["POS Invoice", "Pick List"]:
			return

		if not self.warehouse:
			return

		if self.voucher_type in ["Stock Reconciliation", "Stock Entry"] and self.docstatus != 1:
			return

		if not (self.has_serial_no and self.type_of_transaction == "Inward"):
			return

		serial_nos = [d.serial_no for d in self.entries if d.serial_no]
		kwargs = frappe._dict(
			{
				"item_code": self.item_code,
				"posting_date": self.posting_date,
				"posting_time": self.posting_time,
				"serial_nos": serial_nos,
				"check_serial_nos": True,
				"ignore_feature": 1
			}
		)

		if self.returned_against and self.docstatus == 1:
			kwargs["ignore_voucher_detail_no"] = self.voucher_detail_no

		if self.docstatus == 1:
			kwargs["voucher_no"] = self.voucher_no

		available_serial_nos = get_available_serial_nos(kwargs)
		for data in available_serial_nos:
			if data.serial_no in serial_nos:
				self.throw_error_message(
					f"Serial No {bold(data.serial_no)} is already present in the warehouse {bold(data.warehouse)}.",
					SerialNoDuplicateError,
				)
