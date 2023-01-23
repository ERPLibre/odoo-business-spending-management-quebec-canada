# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import namedtuple
from functools import partial

from odoo import fields, models
from odoo.tools.misc import formatLang


class SaleOrder(models.Model):
    _inherit = "sale.order"

    amount_by_group = fields.Binary(
        string="Tax amount by group",
        compute="_amount_by_group",
        help="type: [(name, amount, base, formated amount, formated base)]",
    )

    def _amount_by_group(self):
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(
                formatLang,
                self.with_context(lang=order.partner_id.lang).env,
                currency_obj=currency,
            )
            res = {}
            for line in order.order_line:
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                taxes = line.tax_id.compute_all(
                    price_reduce,
                    quantity=line.product_uom_qty,
                    product=line.product_id,
                    partner=order.partner_shipping_id,
                )["taxes"]
                for tax in line.tax_id:
                    for t in taxes:
                        group = namedtuple("MyStruct", ("sequence", "name"))(
                            sequence=t.get("sequence"), name=t.get("name")
                        )
                        res.setdefault(group, {"amount": 0.0, "base": 0.0})
                        if (
                            t["id"] == tax.id
                            or t["id"] in tax.children_tax_ids.ids
                        ):
                            res[group]["amount"] += t["amount"]
                            res[group]["base"] += t["base"]
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            order.amount_by_group = [
                (
                    l[0].name,
                    l[1]["amount"],
                    l[1]["base"],
                    fmt(l[1]["amount"]),
                    fmt(l[1]["base"]),
                    len(res),
                )
                for l in res
            ]
