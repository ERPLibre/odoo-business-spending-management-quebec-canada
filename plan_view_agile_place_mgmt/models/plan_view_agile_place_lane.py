#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

from odoo import _, api, fields, models


class PlanViewAgilePlaceLane(models.Model):
    _name = "plan.view.agile.place.lane"
    _description = "plan_view_agile_place_lane"
    _order = "name,id"

    name = fields.Char(compute="_compute_name")

    title = fields.Char()

    description = fields.Char()

    active = fields.Boolean()

    is_collapsed = fields.Boolean()

    lane_class_type = fields.Char()

    lane_id_pvap = fields.Char(help="Plan View Agile Plane - Lane ID")

    lane_type = fields.Char()

    orientation = fields.Char()

    parent_lane_id = fields.Many2one(
        string="Parent Lane", comodel_name="plan.view.agile.place.lane"
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
