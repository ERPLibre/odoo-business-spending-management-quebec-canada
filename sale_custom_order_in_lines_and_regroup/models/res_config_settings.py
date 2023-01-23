# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    automatic_group_sale_order_at_save = fields.Boolean(
        "Group sales order automatically at save",
        config_parameter=(
            "sale_custom_order_in_lines_and_regroup."
            "automatic_group_sale_order_at_save"
        ),
        help="Regroup automatically sales order lines at save.",
    )
