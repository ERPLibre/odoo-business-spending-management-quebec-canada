from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_manufacturer_model = fields.Char(
        "Manufacturer model",
        related="product_id.manufacturer_model",
        store=False,
        readonly=True,
    )
