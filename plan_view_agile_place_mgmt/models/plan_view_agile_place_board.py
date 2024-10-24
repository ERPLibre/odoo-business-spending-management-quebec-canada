#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

from odoo import _, api, fields, models


class PlanViewAgilePlaceBoard(models.Model):
    _name = "plan.view.agile.place.board"
    _description = "plan_view_agile_place_board"

    name = fields.Char()

    board_id_pvap = fields.Char(help="Plan View Agile Plane - Board ID")

    session_id = fields.Many2one(
        comodel_name="plan.view.agile.place.session",
        string="Session",
    )
