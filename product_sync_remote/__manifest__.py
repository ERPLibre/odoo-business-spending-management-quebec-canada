{
    "name": "Product Sync Remote",
    "summary": "Synchronise les product.template et variantes depuis une autre instance Odoo via XML-RPC",
    "version": "16.0.1.0.0",
    "category": "Product",
    "author": "MathBenTech",
    "license": "AGPL-3",
    "depends": ["product"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_sync_views.xml",
        "views/product_sync_wizard_views.xml",
        "views/menu.xml",
    ],
    "application": True,
}
