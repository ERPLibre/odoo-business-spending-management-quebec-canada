# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    lang_to_order = fields.Char(
        string="Lang name",
        help="When reorder from label, use this lang.",
        default="fr_CA",
    )

    algorithm_lang_to_order = fields.Selection(
        string="Algorithm to choose when compute reorder",
        selection=[
            ("by_alpha", "By alpha order"),
            ("by_label", "By custom label"),
        ],
        default="by_alpha",
    )

    menu_order_labels = fields.Text(
        string="Menu Order Labels",
        help="Enter menu labels in French, one per line.",
    )

    def set_values(self):
        """Set the configuration values."""
        super().set_values()
        param = self.env["ir.config_parameter"].sudo()
        menu_order_labels = (
            self.menu_order_labels and self.menu_order_labels or False
        )
        algorithm_lang_to_order = (
            self.algorithm_lang_to_order
            and self.algorithm_lang_to_order
            or False
        )
        lang_to_order = self.lang_to_order and self.lang_to_order or False
        param.set_param(
            "menu_reorder_settings.menu_order_labels", menu_order_labels
        )
        param.set_param(
            "menu_reorder_settings.algorithm_lang_to_order",
            algorithm_lang_to_order,
        )
        param.set_param("menu_reorder_settings.lang_to_order", lang_to_order)

    @api.model
    def get_values(self):
        """Get the current configuration values."""
        res = super().get_values()
        res.update(
            menu_order_labels=self.env["ir.config_parameter"]
            .sudo()
            .get_param("menu_reorder_settings.menu_order_labels"),
            algorithm_lang_to_order=self.env["ir.config_parameter"]
            .sudo()
            .get_param("menu_reorder_settings.algorithm_lang_to_order"),
            lang_to_order=self.env["ir.config_parameter"]
            .sudo()
            .get_param("menu_reorder_settings.lang_to_order"),
        )
        return res

    def execute_menu_reorder(self):
        menu_ids = (
            self.env["ir.ui.menu"]
            .sudo()
            .with_context(lang=self.lang_to_order)
            .search([("parent_id", "=", False)])
        )
        if self.algorithm_lang_to_order == "by_label":
            menu_labels = self.menu_order_labels.split("\n")

            lst_menu_id_reorder = []
            sequence = 10
            for idx_i, label_fr in enumerate(menu_labels):
                sequence = 10 + idx_i
                lst_menu = [a for a in menu_ids if label_fr == a.display_name]
                for menu_id in lst_menu:
                    menu_id.sequence = sequence
                    lst_menu_id_reorder.append(menu_id)

            last_sequence = sequence
            lst_menu = sorted(
                [a for a in menu_ids if a not in lst_menu_id_reorder],
                key=lambda menu_id: menu_id.display_name,
            )
            for sequence, menu_id in enumerate(lst_menu):
                menu_id.sequence = sequence + last_sequence

        elif self.algorithm_lang_to_order == "by_alpha":
            lst_menu = sorted(
                menu_ids, key=lambda menu_id: menu_id.display_name
            )
            for sequence, menu_id in enumerate(lst_menu):
                menu_id.sequence = sequence + 10

        _logger.info(
            f"End of reorder menu from algorithm {self.algorithm_lang_to_order}"
        )
