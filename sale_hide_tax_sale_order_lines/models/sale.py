# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    hide_tax_sale_order = fields.Boolean(
        String="Hide Sale Order Lines taxes",
        default=True,
        help="Hide by default different tax per sale order line.",
    )
