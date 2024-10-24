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

    card_type_id = fields.Many2one(
        comodel_name="plan.view.agile.place.card.type",
        string="Card Type",
    )

    lane_id = fields.Many2one(
        comodel_name="plan.view.agile.place.lane",
        string="Lane",
        group_expand="_read_group_lane_ids",
        default=lambda self: self._default_stage(),
    )

    lane_parent_name = fields.Char(
        string="Lane parent name",
        related="lane_id.parent_lane_id.name",
        store=True,
    )

    lane_name_unique = fields.Char(
        compute="_compute_lane_name_unique", store=True
    )

    moved_on = fields.Datetime()

    session_id = fields.Many2one(
        comodel_name="plan.view.agile.place.session",
        string="Session",
    )

    size = fields.Integer()

    version = fields.Integer()

    @api.returns("self")
    def _default_stage(self):
        return self.env["plan.view.agile.place.lane"].search([], limit=1)

    @api.depends("lane_id")
    def _compute_lane_name_unique(self):
        for rec in self:
            if not rec.lane_id:
                rec.lane_name_unique = ""
            elif rec.lane_id.parent_lane_id:
                rec.lane_name_unique = (
                    f"{rec.lane_id.parent_lane_id.name}/{rec.lane_id.name}"
                )
            else:
                rec.lane_name_unique = f"/{rec.lane_id.name}"

    @api.model
    def _read_group_lane_ids(self, stages, domain, order):
        return self.env["plan.view.agile.place.lane"].search([], order=order)

    @api.model_create_multi
    def create(self, vals_list):
        # Ignore creation if already exist with card_id_pvap
        rec_ids = super().create(vals_list)
        for rec in rec_ids:
            if rec.card_id_pvap:
                # Ignore, already exist in remote
                continue
            data = {
                "boardId": rec.board_id.board_id_pvap,
                "title": rec.name,
                "laneId": rec.lane_id.lane_id_pvap,
            }
            status, response = rec.session_id.request_api_post(
                "/io/card", data=data
            )
            if status != 200:
                continue
            rec.card_id_pvap = json.loads(response.text).get("id")
        return rec_ids

    def write(self, values):
        status = super().write(values)
        if not status:
            return status
        for rec in self:
            if "lane_id" in values:
                data = {
                    "cardIds": [rec.card_id_pvap],
                    "destination": {"laneId": rec.lane_id.lane_id_pvap},
                }
                status, response = rec.session_id.request_api_post(
                    "/io/card/move", data=data
                )
                if status != 200:
                    continue
        return status
