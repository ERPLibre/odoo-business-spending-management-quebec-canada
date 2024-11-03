#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import datetime
import json
import logging
import time

import requests

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class PlanViewAgilePlaceSession(models.Model):
    _name = "plan.view.agile.place.session"
    _description = "plan_view_agile_place_session"

    name = fields.Char(
        string="URL", required=True, default="https://myaccount.leankit.com"
    )

    api_token = fields.Char(required=True)

    sms_api_url = fields.Char()

    sms_api_token = fields.Char()

    sms_from_number_phone = fields.Char()

    sms_from_country = fields.Char(default="+1")

    sms_enable = fields.Boolean(
        default=False, help="Ignore this functionality if not enable."
    )

    sms_to_number_phone_default = fields.Char(help="Separate multiple with ;")

    sms_to_country_default = fields.Char(default="+1")

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
        return self._request_api(path, "get", data=data, is_param=True)

    def request_api_get_unlimited(self, path, data_name, data=None):
        return self._request_api_unlimited(
            path, "get", data_name, data=data, is_param=True
        )

    def request_api_post(self, path, data=None):
        return self._request_api(path, "post", data=data)

    def request_api_delete(self, path, data=None):
        return self._request_api(path, "delete", data=data)

    def request_api_post_unlimited(self, path, data_name, data=None):
        return self._request_api_unlimited(path, "post", data_name, data=data)

    def _request_api_unlimited(
        self, path, type_request, data_name, data=None, is_param=True
    ):
        # Will loop to extract all information
        end_row = 0
        total_records = 0
        is_started = True
        lst_data = []
        while is_started or end_row < total_records:
            is_started = False
            status, response = self._request_api(
                path, type_request, data=data, is_param=True
            )
            if response.get("message") == "Server error":
                raise exceptions.Warning(
                    f"Unknown error from server with request '{path}' type"
                    f" '{type_request}' data '{data}'"
                )
            end_row = response.get("pageMeta").get("endRow")
            data["offset"] = end_row
            total_records = response.get("pageMeta").get("totalRecords")
            lst_data.extend(response.get(data_name))
        return lst_data

    def _request_api(self, path, type_request, data=None, is_param=False):
        if type_request == "get":
            cb_type_request = requests.get
        elif type_request == "post":
            cb_type_request = requests.post
        elif type_request == "delete":
            cb_type_request = requests.delete
        else:
            raise exceptions.Warning(
                f"Cannot support type request '{type_request}'"
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_token,
        }
        has_finish = False
        while not has_finish:
            url = self.name + path
            json_data = None
            if data:
                json_data = json.dumps(data)
                if is_param:
                    response = cb_type_request(
                        url, headers=headers, params=data
                    )
                else:
                    response = cb_type_request(
                        url, headers=headers, data=json_data
                    )
            else:
                response = cb_type_request(url, headers=headers)

            if response.status_code == 429:
                # Detect too much request
                retry_after = response.headers.get("retry-after")
                timestamp_retry_after = datetime.datetime.strptime(
                    retry_after,
                    "%a, %d %b %Y %H:%M:%S %Z",
                )
                diff_time = timestamp_retry_after - datetime.datetime.now()
                total_second_to_wait = diff_time.total_seconds()
                _logger.info(
                    f"Wait {total_second_to_wait} seconds after 120 requests"
                    " over API Plan View Agile Place."
                )
                time.sleep(total_second_to_wait)
                _logger.info(f"Wait done, continue!")
                continue
            has_finish = True

        if response.text:
            response_data = json.loads(response.text)
        else:
            response_data = ""

        request_history_value = {
            "name": url,
            "type": type_request,
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
    def action_clear_all(self):
        for rec in self:
            self.env["plan.view.agile.place.card"].search(
                [("session_id", "=", rec.id)]
            ).unlink()
            self.env["plan.view.agile.place.card.type"].search(
                [("session_id", "=", rec.id)]
            ).unlink()
            self.env["plan.view.agile.place.lane"].search(
                [("session_id", "=", rec.id)]
            ).unlink()
            self.env["plan.view.agile.place.board"].search(
                [("session_id", "=", rec.id)]
            ).unlink()

    @api.multi
    def action_sync(self, ctx=None, partial_root_lane_name=None):
        for rec in self:
            # Get all board
            # TODO configuration board
            # champs personnalisés champs telephone
            # effacer une carte
            status, response = rec.request_api_get("/io/board")
            if str(status)[0] != "2":
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

                self.env["plan.view.agile.place.card"].sync_pvap_cards(
                    rec, board_id
                )
