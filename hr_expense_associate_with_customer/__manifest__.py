# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "HR expense associate with customer",
    "version": "1.0.0",
    "author": "MathBenTech",
    "website": "https://mathben.tech",
    "license": "AGPL-3",
    "category": "Human Resources",
    "summary": "Associate an HR expense with a customer",
    "description": """
Associate an HR expense with a customer
=======================================
""",
    "depends": ["hr_expense", "contacts"],
    "data": [
        "views/hr_expense_views.xml",
    ],
    "installable": True,
}
