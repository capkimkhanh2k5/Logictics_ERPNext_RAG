frappe.ui.form.on("Shipment Tracking", {
    refresh: function(frm) {
        if (!frm.is_new()) {
            let btn = frm.add_custom_button(__('Sync AfterShip'), function() {
                frappe.call({
                    method: 'logistics_wizard.api.sync_aftership',
                    args: {
                        tracking_number: frm.doc.tracking_number || 'TRACK123',
                        shipment_name: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __('Đang đồng bộ hành trình từ AfterShip...'),
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint(r.message);
                            frm.reload_doc();
                        }
                    }
                });
            });
            btn.addClass('btn-primary');
        }
    }
});
