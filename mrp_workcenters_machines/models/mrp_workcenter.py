# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    workcenter_machine_type_id = fields.Many2one(
        "mrp.workcenter.machine.type", "Machine type"
    )
    workcenter_category_id = fields.Many2one(
        comodel_name="mrp.workcenter.category", string="Machine categories"
    )
    dimension_inner_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
        domain="[('category_id', '=', 4)]",
    )
    enable_dimension = fields.Boolean(
        compute="_enable_dimension", readonly=True, string="Enable dimension"
    )
    dimension_inner_x = fields.Float(string="Dimension inner x")
    dimension_inner_y = fields.Float(string="Dimension inner y")
    dimension_inner_z = fields.Float(string="Dimension inner z")

    @api.multi
    @api.depends("workcenter_machine_type_id")
    def _enable_dimension(self):
        if self.workcenter_machine_type_id:
            self.enable_dimension = (
                self.workcenter_machine_type_id.enable_dimension
            )
        else:
            self.enable_dimension = False
