# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    refund_total_tip_amount_included_to_employee = fields.Boolean(
        string="Add tip when refunding the employee expenses.",
        config_parameter=(
            "hr_expense.refund_total_tip_amount_included_to_employee"
        ),
    )
