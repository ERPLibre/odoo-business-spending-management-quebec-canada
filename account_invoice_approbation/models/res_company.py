# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = "res.company"

    portal_invoice_confirmation_sign = fields.Boolean(string='Online Signature Invoice')
