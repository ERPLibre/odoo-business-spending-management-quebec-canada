# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    workcenter_ids = fields.One2many(
        comodel_name="mrp.workcenter",
        inverse_name="partner_id",
        string="Workcenter",
    )
