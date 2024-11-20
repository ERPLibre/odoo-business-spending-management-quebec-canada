#!/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class PlanViewAgilePlaceLane(models.Model):
    _name = "plan.view.agile.place.lane"
    _description = "plan_view_agile_place_lane"
    _order = "name,id"

    name = fields.Char(readonly=True)

    breadcrumb_middle_name = fields.Text(
        help="Will be use to search sub_lane", readonly=True
    )

    title = fields.Char()

    description = fields.Char()

    active = fields.Boolean(default=True)

    need_update_compute = fields.Boolean(
        default=True,
        help="Will be False when updating algorithm compute this record.",
    )

    is_collapsed = fields.Boolean()

    lane_class_type = fields.Char()

    lane_id_pvap = fields.Char(help="Plan View Agile Plane - Lane ID")

    lane_type = fields.Char()

    lane_parent_id = fields.Many2one(
        string="Parent Lane", comodel_name="plan.view.agile.place.lane"
    )

    lane_parent_name = fields.Char(
        string="Parent Lane name", related="lane_parent_id.title"
    )

    lane_child_ids = fields.One2many(
        comodel_name="plan.view.agile.place.lane",
        inverse_name="lane_parent_id",
        string="Childs Lane",
    )

    lane_root_id = fields.Many2one(
        string="Root Lane",
        comodel_name="plan.view.agile.place.lane",
        readonly=True,
        # compute="_compute_lane_root_id",
        # store=True,
    )

    lane_root_name = fields.Char(
        string="Root Lane name", related="lane_root_id.title"
    )

    orientation = fields.Char()

    sequence = fields.Integer()

    columns = fields.Integer()

    board_id = fields.Many2one(
        comodel_name="plan.view.agile.place.board",
        required=True,
        string="Board",
    )

    session_id = fields.Many2one(
        comodel_name="plan.view.agile.place.session",
        string="Session",
    )

    card_ids = fields.One2many(
        comodel_name="plan.view.agile.place.card",
        inverse_name="lane_id",
        string="Cards",
    )

    count_card = fields.Integer(compute="_compute_count_card", store=True)

    @api.depends("title", "lane_parent_id")
    def _compute_name(self):
        for rec in self:
            # seq = f"{rec.columns}.{rec.sequence} "
            # seq = f"{rec.sequence} "
            if rec.lane_parent_id:
                # rec.name = (
                #     f"{rec.lane_parent_id.name}/{rec.title}"
                # )
                rec.name = f"/[{rec.lane_parent_id.sequence}]{rec.lane_parent_id.title}/[{rec.sequence}]{rec.title}"
            else:
                rec.name = f"/[{rec.sequence}]{rec.title}"

    @api.depends("card_ids")
    def _compute_count_card(self):
        for rec in self:
            rec.count_card = len(rec.card_ids)

    @api.depends("lane_parent_id")
    def _compute_lane_root_id(self):
        for rec in self:
            if not rec.lane_parent_id:
                rec.lane_root_id = False
            lane_id = False
            lane_parent_id = rec.lane_parent_id
            breadcrumb_middle_name = ""
            while lane_parent_id:
                breadcrumb_middle_name += f"{lane_parent_id.title}\n"
                lane_id = lane_parent_id
                lane_parent_id = lane_parent_id.lane_parent_id

            rec.breadcrumb_middle_name = breadcrumb_middle_name
            rec.lane_root_id = False if not lane_id else lane_id.id

    def action_sync_cards(self):
        for rec in self:
            self.env["plan.view.agile.place.card"].sync_pvap_cards(
                rec.board_id, from_lane=rec
            )

    def get_list_child_lane_from_lane(self, add_itself=False):
        lane_ids = self.env["plan.view.agile.place.lane"]
        for rec in self:
            if rec.lane_child_ids:
                # Recursive add
                lane_ids += rec.lane_child_ids.get_list_child_lane_from_lane(
                    add_itself=True
                )
            # Note, ignore lane with child, cause error on server
            if add_itself and not rec.lane_child_ids:
                lane_ids += rec
        return lane_ids

    def get_list_pvap_child_lane_from_lane(self, add_itself=False):
        lane_ids = self.get_list_child_lane_from_lane(add_itself=add_itself)
        return [a.lane_id_pvap for a in lane_ids]

    def write(self, vals):
        status = super().write(vals)
        if not status:
            return status
        for rec in self:
            if not rec.lane_id_pvap:
                continue
            if not self.env.context.get("enable_sync_lane"):
                continue
            data = {
                "title": rec.title,
            }
            status, response = rec.session_id.request_api_patch(
                f"/io/board/{rec.board_id.board_id_pvap}/lane/{rec.lane_id_pvap}",
                data=data,
            )
            if str(status)[0] != "2":
                _logger.error(
                    f"Cannot rename lane status {status} : " + str(response)
                )
                continue
        return status
