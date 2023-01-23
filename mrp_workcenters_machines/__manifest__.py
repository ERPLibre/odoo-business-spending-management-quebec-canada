{
    "name": "MRP workcenters machines",
    "category": "Partner",
    "summary": "Add machines in workcenters",
    "version": "12.0.0.0",
    "description": """

    """,
    "depends": [
        "mrp",
        "uom",
        "res_partner_supplier_own_mrp_work_centers",
    ],
    "data": [
        "views/mrp_menu.xml",
        "views/mrp_workcenter_category_views.xml",
        "views/mrp_workcenter_machine_type_views.xml",
        "views/mrp_workcenter_views.xml",
        "security/ir.model.access.csv",
    ],
    "qweb": [],
    "installable": True,
    "auto_install": False,
}
