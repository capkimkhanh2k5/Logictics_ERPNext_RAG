import frappe

def create_doctype():
    frappe.init(site="logistics.local")
    frappe.connect()

    if not frappe.db.exists("DocType", "Logistics Wizard Settings"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Logistics Wizard Settings",
            "module": "Logistics Wizard",
            "custom": 1,
            "issingle": 1, # This makes it a Single DocType (like settings)
            "fields": [
                {
                    "fieldname": "aftership_api_key",
                    "fieldtype": "Password",
                    "label": "AfterShip API Key",
                    "reqd": 0
                }
            ],
            "permissions": [
                {
                    "role": "System Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1
                }
            ]
        })
        doc.insert()
        frappe.db.commit()
        print("Logistics Wizard Settings DocType created!")
    else:
        print("Logistics Wizard Settings DocType already exists.")

if __name__ == "__main__":
    create_doctype()
