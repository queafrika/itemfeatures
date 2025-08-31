
frappe.ui.form.on("Stock Entry", {


	set_basic_rate: function (frm, cdt, cdn) {
		console.log("Setting basic rate from new Hoooray!!!!!!!!")
		const item = locals[cdt][cdn];
		item.transfer_qty = flt(item.qty) * flt(item.conversion_factor);

		const args = {
			item_code: item.item_code,
			posting_date: frm.doc.posting_date,
			posting_time: frm.doc.posting_time,
			warehouse: cstr(item.s_warehouse) || cstr(item.t_warehouse),
			serial_no: item.serial_no,
			batch_no: item.batch_no,
			company: frm.doc.company,
			qty: item.s_warehouse ? -1 * flt(item.transfer_qty) : flt(item.transfer_qty),
			voucher_type: frm.doc.doctype,
			voucher_no: item.name,
			allow_zero_valuation: 1,
			custom_feature: item.custom_feature,
		};

		if (item.item_code || item.serial_no) {
			frappe.call({
				method: "erpnext.stock.utils.get_incoming_rate",
				args: {
					args: args,
				},
				callback: function (r) {
					frappe.model.set_value(cdt, cdn, "basic_rate", r.message || 0.0);
					frm.events.calculate_basic_amount(frm, item);
				},
			});
		}
	},

});


frappe.ui.form.on("Stock Entry Detail", {
	custom_feature(frm, cdt, cdn) {
		frm.events.set_basic_rate(frm, cdt, cdn);
	},

	item_code(frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (d.item_code) {
			var args = {
				item_code: d.item_code,
				warehouse: cstr(d.s_warehouse) || cstr(d.t_warehouse),
				transfer_qty: d.transfer_qty,
				custom_feature: d.custom_feature,
				serial_no: d.serial_no,
				batch_no: d.batch_no,
				bom_no: d.bom_no,
				expense_account: d.expense_account,
				cost_center: d.cost_center,
				company: frm.doc.company,
				qty: d.qty,
				voucher_type: frm.doc.doctype,
				voucher_no: d.name,
				allow_zero_valuation: 1,
			};

			return frappe.call({
				doc: frm.doc,
				method: "get_item_details",
				args: args,
				callback: function (r) {
					if (r.message) {
						var d = locals[cdt][cdn];
						$.each(r.message, function (k, v) {
							if (v) {
								// set_value trigger barcode function and barcode set qty to 1 in stock_controller.js, to avoid this set value manually instead of set value.
								if (k != "barcode") {
									frappe.model.set_value(cdt, cdn, k, v); // qty and it's subsequent fields weren't triggered
								} else {
									d.barcode = v;
								}
							}
						});
						refresh_field("items");

						let no_batch_serial_number_value = false;
						if (d.has_serial_no || d.has_batch_no) {
							no_batch_serial_number_value = true;
						}

						if (
							no_batch_serial_number_value &&
							!frappe.flags.hide_serial_batch_dialog &&
							!frappe.flags.dialog_set
						) {
							frappe.flags.dialog_set = true;
							erpnext.stock.select_batch_and_serial_no(frm, d);
						} else {
							frappe.flags.dialog_set = false;
						}
					}
				},
			});
		}
	},
});