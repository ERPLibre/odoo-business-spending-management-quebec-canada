#!/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import json
import logging

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


# class EmployeePublic(models.Model):
#     _inherit = "hr.employee.public"
#
#     enable_sms_rappel_horaire_gestionnaire = fields.Boolean(readonly=True)
#
#     enable_sms_rappel_horaire_employee = fields.Boolean(readonly=True)
#
#     pvap_card_id = fields.Many2one(
#         comodel_name="planviewap.card",
#         string="Card",
#         readonly=True
#     )


class HREmployee(models.Model):
    _inherit = "hr.employee"

    enable_sms_rappel_horaire_gestionnaire = fields.Boolean()

    enable_sms_rappel_horaire_employee = fields.Boolean()

    pvap_card_id = fields.Many2one(
        comodel_name="planviewap.card",
        string="Card",
    )

    def generate_inherit_pvap_card(self, card_value, board_id, process_id):
        self.ensure_one()
        # Inherit this method to add value into card at creation
        pass

    def generate_pvap_card(self, process_id):
        if not process_id:
            _logger.warning(
                "Cannot retrieve processus to create card for hr.employee."
            )
            return
        lst_card_value = []
        for rec in self:
            if not process_id.board_id:
                process_id.fill_board_id()
            board_id = process_id.board_id
            if not board_id:
                _logger.warning("You need to select a board.")
                continue

            lane_ids = process_id.search_lanes_from_processus(sync_cards=False)

            if not lane_ids:
                _logger.warning(
                    f"Cannot find lane with root name '{process_id.lane_root_name}' and lane name '{process_id.lane_name}'."
                )
                continue
            # TODO use bind field
            card_value = {
                "name": rec.name,
                "board_id": board_id.id,
                "session_id": process_id.session_id.id,
            }

            lst_custom_fields = []
            # Bind value
            custom_field_items = json.loads(
                process_id.bind_custom_field
            ).items()
            for (
                bind_field_key,
                bind_pvap_key,
            ) in custom_field_items:
                value_bind = getattr(rec, bind_field_key)
                # TODO this depend of his type, but pvap don't support boolean
                if value_bind not in [None, False]:
                    custom_field_id = self.env[
                        "planviewap.customfield"
                    ].search(
                        [
                            ("label", "=", bind_pvap_key),
                            ("board_id", "=", board_id.id),
                        ],
                        limit=1,
                    )
                    if not custom_field_id:
                        _logger.warning(
                            f"Cannot find custom field '{bind_pvap_key}', need is ID to create employee"
                        )
                        continue
                    dct_custom_field = {
                        "fieldId": custom_field_id.id_pvap,
                        "value": value_bind,
                    }
                    lst_custom_fields.append(dct_custom_field)

            if lst_custom_fields:
                card_value["custom_fields"] = lst_custom_fields

            card_type_id = self.env["planviewap.card.type"].search(
                [
                    ("name", "=", process_id.type_card),
                    ("board_id", "=", board_id.id),
                ]
            )
            if card_type_id:
                card_value["card_type_id"] = card_type_id.id
                card_value["entete"] = card_type_id.name

            rec.generate_inherit_pvap_card(card_value, board_id, process_id)

            if "lane_id" not in card_value.keys():
                for i in range(process_id.duplicate_multiple_time):
                    for lane_id in lane_ids:
                        card_value["lane_id"] = lane_id.id
                        lst_card_value.append(card_value.copy())
            else:
                lst_card_value.append(card_value.copy())

        self.env["planviewap.card"].create(lst_card_value)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        process_id = self.env["planviewap.processus"].search(
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
            for rec in res:
                if not rec.pvap_card_id:
                    rec.generate_pvap_card(process_id)
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
        process_id = self.env["planviewap.processus"].search(
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
            card_ids = self.env["planviewap.card"]
            for rec in self:
                card_id = self.env["planviewap.card"].search(
                    [
                        ("lane_root_name", "=", process_id.lane_root_name),
                        ("lane_name", "=", process_id.lane_name),
                        ("name", "=", rec.name),
                        ("board_id", "=", process_id.board_id.id),
                    ],
                    limit=1,
                )

                if not card_id:
                    _logger.warning(
                        f"Cannot find card name '{rec.name}' to delete it."
                    )
                else:
                    card_ids += card_id.id
            if card_ids.exists():
                card_ids.enabled_bind = True
                card_ids.unlink()
