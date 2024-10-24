# !/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

from odoo import _, api, fields, models


class PlanViewAgilePlaceCardType(models.Model):
    _name = "plan.view.agile.place.card_type"
    _description = "plan_view_agile_place_card_type"

    name = fields.Char()

    card_type_id_pvap = fields.Char(
        readonly=True, help="Plan View Agile Plane - Card type ID"
    )

    color_hex = fields.Char()

    is_card_type = fields.Boolean()

    is_default = fields.Boolean()

    is_default_task_type = fields.Boolean()

    is_task_type = fields.Boolean()
