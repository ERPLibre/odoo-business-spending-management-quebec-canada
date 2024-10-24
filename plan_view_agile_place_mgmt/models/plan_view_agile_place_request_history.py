#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

from odoo import _, api, fields, models


class PlanViewAgilePlaceRequestHistory(models.Model):
    _name = "plan.view.agile.place.request_history"
    _description = "plan_view_agile_place_request_history"

    name = fields.Char(string="URL", readonly=True, required=True)

    send_data = fields.Char(readonly=True)

    response_data = fields.Char(readonly=True)

    session_id = fields.Many2one(
        comodel_name="plan.view.agile.place.session",
        string="Session",
        readonly=True,
    )

    is_success = fields.Boolean(
        string="Is success",
        help="Is success when got response status_code 200",
        readonly=True,
    )

    status_code = fields.Integer(readonly=True)

    type = fields.Selection(
        selection=[
            ("get", "GET"),
            ("post", "POST"),
            ("delete", "DELETE"),
        ],
        required=True,
        default="get",
        readonly=True,
    )

    request_server_date = fields.Datetime(readonly=True)
