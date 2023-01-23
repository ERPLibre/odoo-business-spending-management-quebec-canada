{
    "name": "Res Partner Supplier Own MRP work centers",
    "category": "Partner",
    "summary": "Add MRP in res_partner",
    "version": "12.0.0.0",
    "description": """

    """,
    "depends": [
        "mrp",
        "contacts",
    ],
    "data": [
        "views/res_partner_views.xml",
        "views/mrp_workcenter_views.xml",
    ],
    "qweb": [],
    "installable": True,
    "auto_install": False,
}
