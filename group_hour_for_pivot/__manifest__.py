# -*- coding: utf-8 -*-
{
    "name": "Group by Hour for Pivot",
    "summary": """
        Allows to expand date groups by hours""",
    "description": """
        Long description of module's purpose
    """,
    "images": ["images/screen.png"],
    "author": "VuTruong",
    "development_status": "Alpha",
    "website": "http://www.vieterp.net",
    "license": "AGPL-3",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    "category": "Uncategorized",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["base"],
    # always loaded
    "data": [
        # 'security/ir.model.access.csv',
    ],
    "qweb": [
        "static/src/xml/basic.xml",
    ],
}
