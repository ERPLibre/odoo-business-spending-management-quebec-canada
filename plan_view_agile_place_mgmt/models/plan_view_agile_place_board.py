#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import datetime
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

    type_board_ids = fields.Many2many(
        comodel_name="plan.view.agile.place.board.type",
        relation="type_board_ids_plan_view_agile_place_board_rel",
        string="Type Board",
    )

    url_board = fields.Char(compute="_compute_url_board")

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            rec.session_id.search_board_with_type()
        return res

    def write(self, vals):
        res = super().write(vals)
        if "type_board_ids" in vals.keys():
            self.session_id.search_board_with_type()
        return res

    @api.depends("board_id_pvap", "session_id.name")
    def _compute_url_board(self):
        for rec in self:
            url = ""
            if rec.session_id and rec.board_id_pvap:
                url = f"{rec.session_id.name}/board/{rec.board_id_pvap}"
            rec.url_board = url

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

            # Create custom field
            lst_custom_field = rec.session_id.request_api_get_unlimited(
                f"/io/board/{rec.board_id_pvap}/customfield", "customFields"
            )

            for dct_custom_field in lst_custom_field:
                created_on = datetime.datetime.strptime(
                    dct_custom_field.get("createdOn"),
                    "%Y-%m-%dT%H:%M:%S%z",
                ).replace(tzinfo=None)
                custom_field_value = {
                    "label": dct_custom_field.get("label"),
                    "type": dct_custom_field.get("type"),
                    "index": dct_custom_field.get("index"),
                    "icon_color": dct_custom_field.get("iconColor"),
                    "icon_name": dct_custom_field.get("iconName"),
                    "help_text": dct_custom_field.get("helpText"),
                    "id_pvap": dct_custom_field.get("id"),
                    "created_by_pvap": dct_custom_field.get("createdBy"),
                    "created_on": created_on,
                }
                if "choiceConfiguration" in dct_custom_field.keys():
                    custom_field_value["choices"] = "\n".join(
                        dct_custom_field.get("choiceConfiguration").get(
                            "choices"
                        )
                    )
                self.env["plan.view.agile.place.customfield"].create(
                    custom_field_value
                )

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
                    if lane_name != lane_id.title:
                        lane_id.title = lane_name
                        lane_id.need_update_compute = True
                    # TODO check another parameter into lane

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

                lane_parent_id_no = dct_lane.get("parentLaneId")
                if lane_parent_id_no:
                    lane_parent_id = dct_lane_id_no_lane_id.get(
                        lane_parent_id_no
                    )
                    if lane_parent_id:
                        lane_id.lane_parent_id = lane_parent_id.id

            # Force recompute, cause wrong programmation
            lane_ids = self.env["plan.view.agile.place.lane"].search(
                [("board_id", "=", rec.id)]
            )
            for lane_id in lane_ids:
                if lane_id.need_update_compute:
                    # lane_id.lane_root_id.compute()
                    lane_id._compute_lane_root_id()
                    # The name need to be computed at the end, depend on lane_root_id
                    lane_id._compute_name()
                    lane_id.need_update_compute = False

            self.env["plan.view.agile.place.card"].sync_pvap_cards(rec)
