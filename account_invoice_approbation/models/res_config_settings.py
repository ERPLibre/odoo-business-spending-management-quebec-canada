# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_account_invoice_approbation = fields.Boolean(
        related="company_id.portal_invoice_confirmation_sign",
        string="Draft Invoice Online Signature",
        readonly=False,
    )
