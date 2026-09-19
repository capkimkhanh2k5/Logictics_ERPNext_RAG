frappe.ui.form.on("Shipment Tracking", {
    refresh: function(frm) {
        frm.add_custom_button('Sync AfterShip', function() {
            frappe.call({
                method: 'logistics_wizard.api.sync_aftership',
                args: {
                    tracking_number: 'TRACK123',
                    shipment_name: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(r.message);
                        frm.reload_doc();
                    }
                }
            });
        }, 'Tracking');
    }
});
