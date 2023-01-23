# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "HR expense tip included",
    "version": "1.0.0",
    "author": "MathBenTech",
    "website": "https://mathben.tech",
    "license": "AGPL-3",
    "category": "Human Resources",
    "summary": "Support tip in hr_expense",
    "description": """
Support tip in module hr_expense
=================================
This module tip in expense and enable the refund to the employee including tip.
""",
    "depends": ["hr_expense"],
    "data": [
        "views/hr_expense_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
