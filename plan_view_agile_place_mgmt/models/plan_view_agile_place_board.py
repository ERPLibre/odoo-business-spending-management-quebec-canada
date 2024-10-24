#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

from odoo import _, api, fields, models


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
                    }
                    card_type_id = self.env[
                        "plan.view.agile.place.card.type"
                    ].create(value)

            # Create Lanes
            # for dct_lane in response.get("lanes"):
            #     card_type_id_pvap = dct_card_types.get("id")
            #     card_type_name = dct_card_types.get("name")
            #     color_hex = dct_card_types.get("colorHex")
            #     is_card_type = dct_card_types.get("isCardType")
            #     is_task_type = dct_card_types.get("isTaskType")
            #     card_type_id = self.env["plan.view.agile.place.card.type"].search(
            #         [("card_type_id_pvap", "=", card_type_id_pvap)], limit=1
            #     )
            #     if card_type_id:
            #         # Update it
            #         card_type_id.name = card_type_name
            #     else:
            #         value = {
            #             "name": card_type_name,
            #             "card_type_id_pvap": card_type_id_pvap,
            #             "color_hex": color_hex,
            #             "is_card_type": is_card_type,
            #             "is_task_type": is_task_type,
            #         }
            #         card_type_id = self.env["plan.view.agile.place.card.type"].create(value)

            print(status)
