#!/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

from odoo import _, api, fields, models


class PlanViewAPCustomfield(models.Model):
    _name = "planviewap.customfield"
    _description = "planviewap_customfield"
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
        comodel_name="planviewap.board",
        required=True,
        string="Board",
    )

    session_id = fields.Many2one(
        comodel_name="planviewap.session",
        string="Session",
        related="board_id.session_id",
    )
