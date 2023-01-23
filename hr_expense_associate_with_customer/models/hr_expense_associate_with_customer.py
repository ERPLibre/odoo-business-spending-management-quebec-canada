# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrExpenseAssociateWithCustomer(models.Model):
    _inherit = "hr.expense"

    customer_ids = fields.Many2many(
        "res.partner",
        string="Customers",
        readonly=True,
        states={
            "draft": [("readonly", False)],
            "reported": [("readonly", False)],
            "refused": [("readonly", False)],
        },
        domain=[("customer", "=", True)],
    )
