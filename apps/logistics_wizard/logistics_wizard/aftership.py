import frappe

@frappe.whitelist()
def sync_aftership(tracking_number, shipment_name):
    if not tracking_number or not shipment_name:
        frappe.throw("Thiếu mã vận đơn (tracking_number)")

    mock_data = {
        "data": {
            "tracking": {
                "tag": "InTransit",
                "checkpoints": [
                    {
                        "checkpoint_time": "2026-09-15T10:00:00",
                        "location": "US Port",
                        "message": "Export Customs Cleared",
                    },
                    {
                        "checkpoint_time": "2026-09-15T12:00:00",
                        "location": "Ocean",
                        "message": "Departed (Loaded on Vessel/Flight)",
                    },
                    {
                        "checkpoint_time": "2026-09-15T15:00:00",
                        "location": "Pacific Ocean",
                        "message": "Ocean/Air Transit",
                    },
                ],
            }
        }
    }

    shipment = frappe.get_doc("Shipment Tracking", shipment_name)
    shipment.set("transit_route", [])

    for cp in mock_data["data"]["tracking"]["checkpoints"]:
        shipment.append(
            "transit_route",
            {
                "activity": cp.get("message"),
                "location": cp.get("location"),
                "date": cp.get("checkpoint_time").split("T")[0],
            },
        )

    shipment.save(ignore_permissions=True)
    frappe.db.commit()
    return f"Đã đồng bộ thành công {len(mock_data['data']['tracking']['checkpoints'])} trạm hành trình!"
