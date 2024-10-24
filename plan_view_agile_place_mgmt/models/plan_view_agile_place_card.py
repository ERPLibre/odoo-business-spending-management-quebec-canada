#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import json

import requests

from odoo import _, api, fields, models

LEANKIT_URL = "https://MYACCOUNT.leankit.com"
LEANKIT_API_TOKEN = ""


class PlanViewAgilePlaceCard(models.Model):
    _name = "plan.view.agile.place.card"
    _description = "plan_view_agile_place_card"

    name = fields.Char(required=True)

    active = fields.Boolean(
        default=True,
        help="Set active to false to hide the card without deleting it.",
    )

    board_id = fields.Many2one(
        comodel_name="plan.view.agile.place.board",
        required=True,
        string="Board",
    )

    card_id_pvap = fields.Char(
        readonly=True, help="Plan View Agile Plane - Card ID"
    )

    lane_id = fields.Many2one(
        comodel_name="plan.view.agile.place.lane",
        string="Lane",
        group_expand="_read_group_lane_ids",
        default=lambda self: self._default_stage(),
    )

    @api.returns("self")
    def _default_stage(self):
        return self.env["plan.view.agile.place.lane"].search([], limit=1)

    @api.model
    def _read_group_lane_ids(self, stages, domain, order):
        return self.env["plan.view.agile.place.lane"].search([], order=order)

    @api.model_create_multi
    def create(self, vals_list):
        rec_ids = super().create(vals_list)
        for rec in rec_ids:
            url = LEANKIT_URL + "/io/card"
            data = {
                "boardId": rec.board_id.board_id_pvap,
                "title": rec.name,
                "laneId": rec.lane_id.lane_id_pvap,
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + LEANKIT_URL,
            }
            response = requests.post(
                url, headers=headers, data=json.dumps(data)
            )
            # print(response)
            # print(response.status_code)  # Affiche le code de statut (ex: 200, 404)
            # print(response.text)  # Affiche le contenu de la réponse
            # print(response.headers)  # Affiche les en-têtes de la réponse
            rec.card_id_pvap = json.loads(response.text).get("id")
        return rec_ids

    def write(self, values):
        status = super().write(values)
        if not status:
            return status
        for rec in self:
            if "lane_id" in values:
                url = LEANKIT_URL + "/io/card/move"
                data = {
                    "cardIds": [rec.card_id_pvap],
                    "destination": {"laneId": rec.lane_id.lane_id_pvap},
                }
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + LEANKIT_URL,
                }
                response = requests.post(
                    url, headers=headers, data=json.dumps(data)
                )
                if response.status_code != 200:
                    return False
        return status
