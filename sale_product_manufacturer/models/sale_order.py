from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_manufacturer_name = fields.Char(
        "Manufacturer",
        related="product_id.manufacturer.name",
        store=False,
        readonly=True,
    )
