#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class PlanViewAgilePlaceBoard(models.Model):
    _name = "plan.view.agile.place.board"
    _description = "plan_view_agile_place_board"

    name = fields.Char()

    board_id_pvap = fields.Char(
        required=True, help="Plan View Agile Plane - Board ID"
    )

    session_id = fields.Many2one(
        comodel_name="plan.view.agile.place.session",
        string="Session",
    )

    @api.multi
    def action_sync(self):
        for rec in self:
            status, response = rec.session_id.request_api_get(
                f"/io/board/{rec.board_id_pvap}"
            )
            # Create Card Types
            for dct_card_types in response.get("cardTypes"):
                card_type_id_pvap = dct_card_types.get("id")
                card_type_name = dct_card_types.get("name")
                color_hex = dct_card_types.get("colorHex")
                is_card_type = dct_card_types.get("isCardType")
                is_task_type = dct_card_types.get("isTaskType")
                card_type_id = self.env[
                    "plan.view.agile.place.card.type"
                ].search(
                    [("card_type_id_pvap", "=", card_type_id_pvap)], limit=1
                )
                if card_type_id:
                    # Update it
                    card_type_id.name = card_type_name
                else:
                    value = {
                        "name": card_type_name,
                        "card_type_id_pvap": card_type_id_pvap,
                        "color_hex": color_hex,
                        "is_card_type": is_card_type,
                        "is_task_type": is_task_type,
                        "session_id": rec.session_id.id,
                        "board_id": rec.id,
                    }
                    card_type_id = self.env[
                        "plan.view.agile.place.card.type"
                    ].create(value)

            # Create Lanes
            dct_lane_id_no_lane_id = {}
            for dct_lane in response.get("lanes"):
                lane_id_pvap = dct_lane.get("id")
                lane_name = dct_lane.get("name")
                active = dct_lane.get("active")
                is_collapsed = dct_lane.get("isCollapsed")
                lane_class_type = dct_lane.get("laneClassType")
                lane_type = dct_lane.get("laneType")
                orientation = dct_lane.get("orientation")
                sequence = dct_lane.get("index")
                columns = dct_lane.get("columns")
                # activityId
                # archiveCardCount
                # cardCount
                # cardLimit
                # cardSize
                # cardStatus
                # columns
                # creationDate
                # description
                # isConnectionDoneLane
                # isDefaultDropLane
                # sortBy
                # subscriptionId
                # wipLimit

                lane_id = self.env["plan.view.agile.place.lane"].search(
                    [("lane_id_pvap", "=", lane_id_pvap)], limit=1
                )
                if lane_id:
                    # Update it
                    lane_id.name = lane_name
                else:
                    value = {
                        "title": lane_name,
                        "lane_id_pvap": lane_id_pvap,
                        "active": active,
                        "is_collapsed": is_collapsed,
                        "lane_class_type": lane_class_type,
                        "lane_type": lane_type,
                        "orientation": orientation,
                        "sequence": sequence,
                        "columns": columns,
                        "board_id": rec.id,
                        "session_id": rec.session_id.id,
                    }
                    lane_id = self.env["plan.view.agile.place.lane"].create(
                        value
                    )
                    dct_lane_id_no_lane_id[lane_id.lane_id_pvap] = lane_id

            # Rebuild parent lane
            for dct_lane in response.get("lanes"):
                lane_id_pvap = dct_lane.get("id")
                lane_id = self.env["plan.view.agile.place.lane"].search(
                    [("lane_id_pvap", "=", lane_id_pvap)], limit=1
                )
                if not lane_id:
                    _logger.error(f"Cannot find lane {lane_id_pvap}")
                    continue

                parent_lane_id_no = dct_lane.get("parentLaneId")
                if parent_lane_id_no:
                    parent_lane_id = dct_lane_id_no_lane_id.get(
                        parent_lane_id_no
                    )
                    if parent_lane_id:
                        lane_id.parent_lane_id = parent_lane_id.id
