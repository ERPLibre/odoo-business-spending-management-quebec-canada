# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange("product_uom_qty")
    def product_uom_change(self):
        previous_price_unit = self.price_unit
        status = super(SaleOrderLine, self).product_uom_change()
        self.price_unit = previous_price_unit
        return status
