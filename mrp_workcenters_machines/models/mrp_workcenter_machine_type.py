# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models


class MrpWorkcenterMachineType(models.Model):
    _name = "mrp.workcenter.machine.type"
    _description = "MRP workcenter machine type"

    active = fields.Boolean(string="Active", default=True)
    name = fields.Char(string="Name", required=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env["res.company"]._company_default_get(),
    )
    workcenter_category_ids = fields.One2many(
        comodel_name="mrp.workcenter.category",
        inverse_name="workcenter_machine_type_id",
        string="Machine categories",
    )
    enable_dimension = fields.Boolean("Enable dimension")
