#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import logging

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class PlanViewAgilePlaceBoard(models.Model):
    _inherit = "hr.employee"

    enable_sms_rappel_horaire_gestionnaire = fields.Boolean()

    enable_sms_rappel_horaire_employee = fields.Boolean()

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            process_id = self.env["plan.view.agile.place.processus"].search(
                [
                    ("algo_key", "=", "bind_create_card"),
                    ("model_name", "=", "hr.employee"),
                ],
                limit=1,
            )
            if not process_id:
                _logger.warning(
                    "Cannot retrieve processus to create card for hr.employee."
                )
            elif process_id.session_id.bind_rh_employee_create_enabled:
                board_id = process_id.session_id.board_selected_id
                if board_id:
                    # TODO maybe check it exist before create it
                    lane_id = self.env["plan.view.agile.place.lane"].search(
                        [
                            ("root_lane_name", "=", process_id.root_lane_name),
                            ("title", "=", process_id.lane_name),
                        ],
                        limit=1,
                    )
                    if not lane_id:
                        _logger.warning(
                            f"Cannot find lane with root name '{process_id.root_lane_name}' and lane name '{process_id.lane_name}'."
                        )
                    else:
                        # TODO missing custom_field, check json
                        custom_fields = ""
                        card_value = {
                            "name": rec.name,
                            "board_id": board_id.id,
                            "session_id": process_id.session_id.id,
                            "lane_id": lane_id.id,
                        }
                        card_type_id = self.env[
                            "plan.view.agile.place.card.type"
                        ].search(
                            [("name", "=", process_id.type_card)], limit=1
                        )
                        if card_type_id:
                            card_value["card_type_id"] = card_type_id.id
                            card_value["entete"] = card_type_id.name
                        self.env["plan.view.agile.place.card"].create(
                            card_value
                        )
                else:
                    _logger.warning("You need to select a board.")
        return res

    def write(self, vals):
        res = super().write(vals)
        if "active" in vals.keys() and not vals["active"]:
            # Delete it
            self.delete_remote_employee()
        return res

    def unlink(self):
        self.delete_remote_employee()
        res = super().unlink()
        return res

    def delete_remote_employee(self):
        process_id = self.env["plan.view.agile.place.processus"].search(
            [
                ("algo_key", "=", "bind_delete_card"),
                ("model_name", "=", "hr.employee"),
            ],
            limit=1,
        )
        if not process_id:
            _logger.warning(
                "Cannot retrieve processus to create card for hr.employee."
            )
        elif process_id.session_id.bind_rh_employee_create_enabled:
            for rec in self:
                card_id = self.env["plan.view.agile.place.card"].search(
                    [
                        ("root_lane_name", "=", process_id.root_lane_name),
                        ("lane_name", "=", process_id.lane_name),
                        ("name", "=", rec.name),
                    ],
                    limit=1,
                )
                if not card_id:
                    _logger.warning(
                        f"Cannot find card name '{rec.name}' to delete it."
                    )
                else:
                    # This will delete the employee card
                    data_delete = {"cardIds": [card_id.card_id_pvap]}
                    result = process_id.session_id.request_api_delete(
                        "/io/card/", data=data_delete
                    )
                    if str(result[0])[0] != "2":
                        raise exceptions.Warning(
                            f"Receive request {result[0]} from delete card employee."
                        )
