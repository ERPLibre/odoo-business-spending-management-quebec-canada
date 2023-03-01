# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, models

default_tz = "America/Montreal"


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("tz"):
                vals["tz"] = default_tz
        return super(ResUsers, self).create(vals_list)

    def write(self, vals):
        if "tz" not in vals and not self.tz:
            vals["tz"] = default_tz
        return super(ResUsers, self).write(vals)
