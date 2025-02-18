# !/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

from odoo import _, api, fields, models


class PlanViewAPCardType(models.Model):
    _name = "planviewap.card.type"
    _description = "planviewap_card_type"

    name = fields.Char()

    card_type_id_pvap = fields.Char(
        readonly=True, help="Plan View Agile Plane - Card type ID"
    )

    color_hex = fields.Char()

    is_card_type = fields.Boolean()

    is_default = fields.Boolean()

    is_default_task_type = fields.Boolean()

    is_task_type = fields.Boolean()

    session_id = fields.Many2one(
        comodel_name="planviewap.session",
        string="Session",
    )

    board_id = fields.Many2one(
        comodel_name="planviewap.board",
        required=True,
        string="Board",
    )
