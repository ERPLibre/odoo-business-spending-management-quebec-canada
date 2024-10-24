#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import json

import requests

from odoo import _, api, fields, models


class PlanViewAgilePlaceSession(models.Model):
    _name = "plan.view.agile.place.session"
    _description = "plan_view_agile_place_session"

    name = fields.Char(
        string="URL", required=True, default="https://myaccount.leankit.com"
    )

    api_token = fields.Char(required=True)

    has_first_sync = fields.Boolean(
        default=False, readonly=True, help="Will be True when first sync done."
    )

    board_ids = fields.One2many(
        comodel_name="plan.view.agile.place.board",
        inverse_name="session_id",
        string="Boards",
    )

    request_history_ids = fields.One2many(
        comodel_name="plan.view.agile.place.request_history",
        inverse_name="session_id",
        string="Requests",
    )

    def request_api_get(self, path, data=None):
        return self._request_api(path, requests.get, data=data)

    def request_api_post(self, path, data=None):
        return self._request_api(path, requests.post, data=data)

    def _request_api(self, path, cb_type_request, data=None):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_token,
        }
        url = self.name + path
        json_data = None
        if data:
            json_data = json.dumps(data)
            response = cb_type_request(url, headers=headers, data=json_data)
        else:
            response = cb_type_request(url, headers=headers)

        response_data = json.loads(response.text)

        request_history_value = {
            "name": url,
            "type": "get",
            "session_id": self.id,
            "is_success": response.status_code == requests.codes.ok,
            "status_code": response.status_code,
            "request_server_date": response.headers.get("Date"),
            "response_data": response_data,
        }

        if data:
            request_history_value["send_data"] = json_data

        request_history_id = self.env[
            "plan.view.agile.place.request_history"
        ].create(request_history_value)

        return response.status_code, response_data

    @api.multi
    def action_sync(self):
        for rec in self:
            # Get all board
            # TODO configuration board
            # champs personnalisés champs telephone
            # effacer une carte
            status, response = rec.request_api_get("/io/board")
            if status != 200:
                continue
            lst_boards = response.get("boards")
            # Generate boards
            for dct_board in lst_boards:
                board_id_pvap = dct_board.get("id")
                # TODO add this field into board
                board_role = dct_board.get("boardRole")
                board_role_id_no = dct_board.get("boardRoleId")
                board_description = dct_board.get("description")
                board_iswelcome = dct_board.get("isWelcome")
                board_title = dct_board.get("title")
                # Search if exist or create it
                board_id = self.env["plan.view.agile.place.board"].search(
                    [("board_id_pvap", "=", board_id_pvap)], limit=1
                )
                if board_id:
                    # Update it
                    board_id.name = board_title
                else:
                    board_value = {
                        "name": board_title,
                        "session_id": rec.id,
                        "board_id_pvap": board_id_pvap,
                    }
                    board_id = self.env["plan.view.agile.place.board"].create(
                        board_value
                    )
                # Refresh all board information
                board_id.action_sync()

            # Get all cards
            status, response = rec.request_api_get("/io/card")

            rec.has_first_sync = True
            lst_cards = response.get("cards")
            # Generate cards
            for dct_card in lst_cards:
                card_id_pvap = dct_card.get("id")
                archived_on = dct_card.get("archivedOn")
                lane_id_pvap = dct_card.get("lane").get("id")
                board_id_pvap = dct_card.get("board").get("id")
                moved_on = dct_card.get("movedOn")
                type_id_pvap = dct_card.get("type").get("id")
                title = dct_card.get("title")
                size = dct_card.get("size")
                version = dct_card.get("version")

                card_type_id = self.env[
                    "plan.view.agile.place.card.type"
                ].search([("card_type_id_pvap", "=", type_id_pvap)], limit=1)

                lane_id = self.env["plan.view.agile.place.lane"].search(
                    [("lane_id_pvap", "=", lane_id_pvap)], limit=1
                )

                board_id = self.env["plan.view.agile.place.board"].search(
                    [("board_id_pvap", "=", board_id_pvap)], limit=1
                )

                card_value = {
                    "card_id_pvap": card_id_pvap,
                    "active": True if archived_on is None else False,
                    "card_type_id": card_type_id.id if card_type_id else False,
                    "lane_id": lane_id.id if lane_id else False,
                    "board_id": board_id.id if board_id else False,
                    "moved_on": moved_on,
                    "name": title,
                    "size": size,
                    "version": version,
                    "session_id": rec.id,
                }

                # Search if exist or create it
                card_id = self.env["plan.view.agile.place.card"].search(
                    [("card_id_pvap", "=", card_id_pvap)], limit=1
                )
                if card_id:
                    # Update it
                    card_id.name = title
                else:
                    card_id = self.env["plan.view.agile.place.card"].create(
                        card_value
                    )
            # TODO update employe information
            # TODO faire une configuration de la lane qui contient les cartes d'employés
