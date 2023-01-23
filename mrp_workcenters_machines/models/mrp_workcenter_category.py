# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models


class MrpWorkcenterCategory(models.Model):
    _name = "mrp.workcenter.category"
    _description = "MRP workcenter Category"

    active = fields.Boolean(string="Active", default=True)
    name = fields.Char(string="Name", required=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env["res.company"]._company_default_get(),
    )
    workcenter_machine_type_id = fields.Many2one(
        comodel_name="mrp.workcenter.machine.type", string="Machine type"
    )
