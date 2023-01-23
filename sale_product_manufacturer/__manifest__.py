{
    "name": "Manufacturer in Sales Orders Line",
    "version": "1.0",
    "category": "Sales",
    "description": """
This module adds the 'Manufacturer' on sales order.
===================================================

Manufacturer is show in sales orders line in readonly
    """,
    "depends": ["sale", "product_manufacturer"],
    "data": ["views/sale_manufacturer_view.xml"],
}
