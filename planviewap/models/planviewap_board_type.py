#!/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

from odoo import _, api, fields, models


class PlanViewAPBoardType(models.Model):
    _name = "planviewap.board.type"
    _description = "planviewap_board_type"

    name = fields.Char()

    session_id = fields.Many2one(
        comodel_name="planviewap.session",
        string="Session",
    )
