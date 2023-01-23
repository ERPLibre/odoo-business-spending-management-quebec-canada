{
    "name": "Manufacturer model in Sales Orders Line",
    "version": "1.0",
    "category": "Sales",
    "description": """
This module adds the 'Manufacturer model' on sales order.
=========================================================

Manufacturer model is show in sales orders line in readonly
    """,
    "depends": [
        "sale",
        "sale_product_manufacturer",
        "product_manufacturer_model",
    ],
    "data": ["views/sale_manufacturer_view.xml"],
}
