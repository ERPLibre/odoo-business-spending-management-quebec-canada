# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    active = fields.Boolean(string="Active", default=True)
