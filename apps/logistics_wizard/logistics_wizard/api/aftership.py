import frappe
import requests
import os

@frappe.whitelist()
def get_shipment_tracking(tracking_number, slug=None):
    """
    Fetches real-time shipment tracking from AfterShip.
    """
    api_key = os.environ.get("AFTERSHIP_API_KEY") or frappe.conf.get("aftership_api_key")
    
    if not api_key or api_key == "ENTER_API_KEY_HERE":
        return {
            "status": "error",
            "message": "AfterShip API Key is not configured. Vui lòng thêm vào site_config.json bằng lệnh: bench --site logistics.local set-config aftership_api_key YOUR_KEY"
        }
        
    url = f"https://api.aftership.com/v4/trackings"
    if slug:
        url += f"/{slug}/{tracking_number}"
    else:
        url += f"?tracking_number={tracking_number}"
        
    headers = {
        "aftership-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"AfterShip API Error: {response.json().get('meta', {}).get('message', 'Unknown Error')}"
            }
        
        data = response.json()
        return {
            "status": "success",
            "data": data.get("data", {})
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "AfterShip API Error")
        return {
            "status": "error",
            "message": f"Lỗi kết nối AfterShip: {str(e)}"
        }
