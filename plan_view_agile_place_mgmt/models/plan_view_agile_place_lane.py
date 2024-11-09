#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

from odoo import _, api, fields, models


class PlanViewAgilePlaceLane(models.Model):
    _name = "plan.view.agile.place.lane"
    _description = "plan_view_agile_place_lane"
    _order = "name,id"

    name = fields.Char(readonly=True)

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

    orientation = fields.Char()

    parent_lane_id = fields.Many2one(
        string="Parent Lane", comodel_name="plan.view.agile.place.lane"
    )

    parent_lane_name = fields.Char(
        string="Parent Lane name", related="parent_lane_id.title"
    )

    breadcrumb_middle_name = fields.Text(
        help="Will be use to search sub_lane", readonly=True
    )

    child_lane_ids = fields.One2many(
        comodel_name="plan.view.agile.place.lane",
        inverse_name="parent_lane_id",
        string="Childs Lane",
    )

    root_lane_id = fields.Many2one(
        string="Root Lane",
        comodel_name="plan.view.agile.place.lane",
        readonly=True,
        # compute="_compute_root_lane_id",
        # store=True,
    )

    root_lane_name = fields.Char(
        string="Root Lane name", related="root_lane_id.title"
    )

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

    @api.depends("title", "parent_lane_id")
    def _compute_name(self):
        for rec in self:
            # seq = f"{rec.columns}.{rec.sequence} "
            # seq = f"{rec.sequence} "
            if rec.parent_lane_id:
                # rec.name = (
                #     f"{rec.parent_lane_id.name}/{rec.title}"
                # )
                rec.name = f"/[{rec.parent_lane_id.sequence}]{rec.parent_lane_id.title}/[{rec.sequence}]{rec.title}"
            else:
                rec.name = f"/[{rec.sequence}]{rec.title}"

    @api.depends("card_ids")
    def _compute_count_card(self):
        for rec in self:
            rec.count_card = len(rec.card_ids)

    @api.depends("parent_lane_id")
    def _compute_root_lane_id(self):
        for rec in self:
            if not rec.parent_lane_id:
                rec.root_lane_id = False
            lane_id = False
            parent_lane_id = rec.parent_lane_id
            breadcrumb_middle_name = ""
            while parent_lane_id:
                breadcrumb_middle_name += f"{parent_lane_id.title}\n"
                lane_id = parent_lane_id
                parent_lane_id = parent_lane_id.parent_lane_id

            rec.breadcrumb_middle_name = breadcrumb_middle_name
            rec.root_lane_id = False if not lane_id else lane_id.id

    def action_sync_cards(self):
        for rec in self:
            self.env["plan.view.agile.place.card"].sync_pvap_cards(
                rec.board_id, from_lane=rec
            )

    def get_list_child_lane_from_lane(self, add_itself=False):
        lane_ids = self.env["plan.view.agile.place.lane"]
        for rec in self:
            if rec.child_lane_ids:
                # Recursive add
                lane_ids += rec.child_lane_ids.get_list_child_lane_from_lane(
                    add_itself=True
                )
            # Note, ignore lane with child, cause error on server
            if add_itself and not rec.child_lane_ids:
                lane_ids += rec
        return lane_ids

    def get_list_pvap_child_lane_from_lane(self, add_itself=False):
        lane_ids = self.get_list_child_lane_from_lane(add_itself=add_itself)
        return [a.lane_id_pvap for a in lane_ids]
