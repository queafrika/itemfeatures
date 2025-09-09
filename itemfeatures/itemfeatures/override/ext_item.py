#import Item
from erpnext.stock.doctype.item.item import Item, DuplicateReorderRows, get_child_warehouses
from webshop.webshop.doctype.override_doctype.item import WebshopItem
import frappe
from frappe import _, bold

class ExtItem(WebshopItem):

	def recalculate_bin_qty(self, new_name):
		from erpnext.stock.stock_balance import repost_stock

		existing_allow_negative_stock = frappe.db.get_value("Stock Settings", None, "allow_negative_stock")
		frappe.db.set_single_value("Stock Settings", "allow_negative_stock", 1)

		repost_stock_for_warehouses = frappe.get_all(
			"Stock Ledger Entry",
			"warehouse",
			filters={"item_code": new_name},
			pluck="warehouse",
			distinct=True,
		)

		# Delete all existing bins to avoid duplicate bins for the same item and warehouse
		frappe.db.delete("Bin", {"item_code": new_name})

		for warehouse in repost_stock_for_warehouses:
			repost_stock(new_name, warehouse, None)

		frappe.db.set_single_value("Stock Settings", "allow_negative_stock", existing_allow_negative_stock)

	def validate_warehouse_for_reorder(self):
		"""Validate Reorder level table for duplicate and conditional mandatory"""
		warehouse_material_request_type_feature: list[tuple[str, str, str]] = []

		_warehouse_before_save = frappe._dict()
		if not self.is_new() and self._doc_before_save:
			_warehouse_before_save = {
				d.name: d.warehouse for d in self._doc_before_save.get("reorder_levels") or []
			}

		for d in self.get("reorder_levels"):
			if not d.warehouse_group:
				d.warehouse_group = d.warehouse

			# include custom_feature in uniqueness check
			key = (d.get("warehouse"), d.get("material_request_type"), d.get("custom_feature"))

			if key not in warehouse_material_request_type_feature:
				warehouse_material_request_type_feature.append(key)
			else:
				frappe.throw(
					_(
						"Row #{0}: A reorder entry already exists for warehouse {1} with reorder type {2} and custom feature {3}."
					).format(d.idx, d.warehouse, d.material_request_type, d.custom_feature or _("(empty)")),
					DuplicateReorderRows,
				)

			if d.warehouse_reorder_level and not d.warehouse_reorder_qty:
				frappe.throw(_("Row #{0}: Please set reorder quantity").format(d.idx))

			if d.warehouse_group and d.warehouse:
				if _warehouse_before_save.get(d.name) == d.warehouse:
					continue

				child_warehouses = get_child_warehouses(d.warehouse_group)
				if d.warehouse not in child_warehouses:
					frappe.throw(
						_(
							"Row #{0}: The warehouse {1} is not a child warehouse of a group warehouse {2}"
						).format(d.idx, bold(d.warehouse), bold(d.warehouse_group)),
						title=_("Incorrect Check in (group) Warehouse for Reorder"),
					)
