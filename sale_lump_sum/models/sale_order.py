from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    lump_sum = fields.Boolean(
        string="Lump Sum",
        help="Enable the payment condition of lump sum for invoice.",
    )

    lump_sum_entry = fields.Monetary(
        string="Lump Sum entry", store=True, help="Lump sum for the invoice."
    )
