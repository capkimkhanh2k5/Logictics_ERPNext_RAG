import re
with open("apps/logistics_wizard/logistics_wizard/public/js/smart_workflow_widget.bundle.js", "r") as f:
    code = f.read()
code = re.sub(r'function load_leaflet\(callback\) \{.*?\n\s+function render_shipment_timeline', r'function render_shipment_timeline', code, flags=re.DOTALL)
code = re.sub(r'load_leaflet\(function\(\) \{', r'// load_leaflet removed', code)
code = re.sub(r'\}\); // load leaflet end', r'', code)
with open("apps/logistics_wizard/logistics_wizard/public/js/smart_workflow_widget.bundle.js", "w") as f:
    f.write(code)
