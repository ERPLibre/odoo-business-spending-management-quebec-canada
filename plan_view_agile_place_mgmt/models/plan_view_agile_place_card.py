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

    root_lane_id = fields.Many2one(
        related="lane_id.root_lane_id",
        # comodel_name="plan.view.agile.place.lane",
        # string="Root Lane",
        # compute="_compute_root_lane_id",
        # group_expand="_read_group_lane_ids",
        # default=lambda self: self._default_stage(),
    )

    lane_parent_id = fields.Many2one(
        string="Lane parent",
        related="lane_id.parent_lane_id",
        store=True,
    )

    lane_parent_name = fields.Char(
        string="Lane parent name",
        related="lane_id.parent_lane_id.title",
    )

    lane_name = fields.Char(
        string="Lane name",
        related="lane_id.title",
    )

    moved_on = fields.Datetime()

    session_id = fields.Many2one(
        comodel_name="plan.view.agile.place.session",
        string="Session",
    )

    entete = fields.Char()

    external_link = fields.Char()

    card_details = fields.Text()

    description = fields.Html()

    custom_fields = fields.Text()

    size = fields.Integer()

    version = fields.Integer()

    @api.returns("self")
    def _default_stage(self):
        return self.env["plan.view.agile.place.lane"].search([], limit=1)

    # @api.depends("title", "parent_lane_id")
    # def _compute_root_lane_id(self):
    #     for rec in self:

    @api.model
    def _read_group_lane_ids(self, stages, domain, order):
        # TODO this is so wrong, replace lane_parent_name by title
        # Why we receive domain from card, but we are in lane?
        # if not card_ids:
        if not domain:
            return (
                self.env["plan.view.agile.place.lane"]
                .search([], order=order, limit=80)
                .sorted("name")
            )
        card_ids = self.env["plan.view.agile.place.card"].search(domain)
        lane_ids = self.env["plan.view.agile.place.lane"]
        for card_id in card_ids:
            lane_ids += card_id.lane_id
        return lane_ids
        # return (
        #     self.env["plan.view.agile.place.lane"]
        #     .search(eval(str(domain).replace("lane_parent_name", "title")), order=order)
        #     .sorted("name")
        # )

    def update_card_details(self):
        for rec in self:
            status, response = rec.session_id.request_api_get(
                f"/io/card/{rec.card_id_pvap}"
            )
            if status != 200:
                rec.card_details = ""
                continue
            rec.card_details = json.dumps(response)
            if response.get("customFields"):
                rec.custom_fields = json.dumps(response.get("customFields"))

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
