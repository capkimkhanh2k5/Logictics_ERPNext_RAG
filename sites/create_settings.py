import frappe

def execute():
    if not frappe.db.exists('DocType', 'Logistics Wizard Settings'):
        doc = frappe.get_doc({
            'doctype': 'DocType',
            'name': 'Logistics Wizard Settings',
            'module': 'Logistics Wizard',
            'custom': 1,
            'issingle': 1,
            'fields': [
                {
                    'fieldname': 'aftership_api_key',
                    'fieldtype': 'Password',
                    'label': 'AfterShip API Key'
                }
            ],
            'permissions': [
                {
                    'role': 'System Manager',
                    'read': 1,
                    'write': 1,
                    'create': 1
                }
            ]
        })
        doc.insert()
        frappe.db.commit()
        print('Logistics Wizard Settings DocType created!')
    else:
        print('Logistics Wizard Settings DocType already exists.')
