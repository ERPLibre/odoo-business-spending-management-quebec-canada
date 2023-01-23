# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Sale custom order in lines and regroup",
    "version": "1.0.0",
    "author": "MathBenTech",
    "website": "https://mathben.tech",
    "license": "AGPL-3",
    "category": "Sales",
    "summary": "Custom order in lines of sales and regroup",
    "description": """
Custom order in lines of sales and regroup
==========================================
This module adds the following section to sales: material and services.
If enabled, it will regroup the lines under the appropriate sections.
""",
    "depends": ["sale", "product_lump_sum", "stock"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/sale_views.xml",
    ],
    "installable": True,
}
