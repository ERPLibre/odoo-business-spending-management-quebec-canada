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
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_token,
        }
        url = self.name + path
        json_data = None
        if data:
            json_data = json.dumps(data)
            response = requests.get(url, headers=headers, data=json_data)
        else:
            response = requests.get(url, headers=headers)

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

        # print(response)
        # print(response.status_code)  # Affiche le code de statut (ex: 200, 404)
        # print(response.text)  # Affiche le contenu de la réponse
        # print(response.headers)  # Affiche les en-têtes de la réponse
        return response.status_code, response_data

    def request_api_post(self, path, data):
        pass

    @api.multi
    def action_sync(self):
        for rec in self:
            # Get all board
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

            rec.has_first_sync = True
