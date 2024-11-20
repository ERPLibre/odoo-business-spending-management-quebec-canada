#!/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

from odoo import _, api, fields, models


class PlanViewAgilePlaceBoardType(models.Model):
    _name = "plan.view.agile.place.board.type"
    _description = "plan_view_agile_place_board_type"

    name = fields.Char()

    session_id = fields.Many2one(
        comodel_name="plan.view.agile.place.session",
        string="Session",
    )
