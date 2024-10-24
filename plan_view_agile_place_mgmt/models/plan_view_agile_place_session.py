#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

from odoo import _, api, fields, models


class PlanViewAgilePlaceSession(models.Model):
    _name = "plan.view.agile.place.session"
    _description = "plan_view_agile_place_session"

    name = fields.Char(
        string="URL", required=True, default="https://myaccount.leankit.com"
    )

    api_token = fields.Char(required=True)
