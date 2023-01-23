# -*- coding: utf-8 -*-
# Copyright 2021 Apulia Software s.r.l. (<info@apuliasoftware.it>)
# License AGPL-3 or later (https://www.gnu.org/licenses/agpl-3.0).

{
    "name": "IOhub - Industry 4.0 devices management",
    "summary": (
        "IOhub Odoo connector Build Industry 4.0 applications by integrating"
        " heterogenous machines and smart sensors with a simple interface."
        " IOhubTM preconfigured modules allow you to compose applications in"
        " just a few minutes"
    ),
    "version": "12.0.1.0.0",
    "category": "Manufacture",
    "author": "Apulia Software s.r.l.",
    "website": "https://www.apuliasoftware.it",
    "license": "AGPL-3",
    "support": "info@apuliasoftware.it",
    "depends": [
        "base",
        "base_setup",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/iohub_view.xml",
    ],
    "images": ["static/description/main_screenshot.jpg"],
    "installable": True,
    "external_dependencies": {
        "python": [
            "paho",
        ],
    },
    "application": True,
}
