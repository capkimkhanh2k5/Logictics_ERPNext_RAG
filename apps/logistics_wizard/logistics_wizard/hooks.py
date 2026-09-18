app_name = "logistics_wizard"
app_title = "Logistics Wizard"
app_publisher = "Khanh"
app_description = "Import-Export Workflow Widget and AfterShip API integration"
app_email = "khanh@logistics.local"
app_license = "mit"

app_include_js = "smart_workflow_widget.bundle.js"
app_include_css = "smart_workflow_widget.bundle.css"

# Overriding Whitelisted methods
override_whitelisted_methods = {
    "logistics_wizard.api.sync_aftership": "logistics_wizard.api.sync_aftership"
}

doctype_js = {
    "Shipment Tracking": "public/js/shipment_tracking.js"
}
