# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    @api.multi
    def write(self, values):
        if (
            values.get("parent_id") is False
            and values.get("name") == "Project"
        ) or (self.name == _("Project") and self.parent_id.id is False):
            values["sequence"] = -10

        return super(IrUiMenu, self).write(values)
