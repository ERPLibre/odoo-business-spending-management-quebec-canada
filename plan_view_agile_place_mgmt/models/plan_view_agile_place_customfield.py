#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

from odoo import _, api, fields, models


class PlanViewAgilePlaceCustomfield(models.Model):
    _name = "plan.view.agile.place.customfield"
    _description = "plan_view_agile_place_customfield"
    _rec_name = "label"

    label = fields.Char()

    created_by_pvap = fields.Char()

    created_on = fields.Datetime()

    help_text = fields.Char()

    icon_color = fields.Char()

    icon_name = fields.Char()

    id_pvap = fields.Char()

    index = fields.Integer()

    type = fields.Char()

    choices = fields.Text(help="Separate list by \n")

    board_id = fields.Many2one(
        comodel_name="plan.view.agile.place.board",
        required=True,
        string="Board",
    )
