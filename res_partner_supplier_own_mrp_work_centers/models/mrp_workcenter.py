# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    partner_id = fields.Many2one("res.partner", "Proprietary")
