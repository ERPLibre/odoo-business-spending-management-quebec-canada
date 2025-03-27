#!/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import datetime
import json
import logging
import time

import requests

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class PlanViewAPSession(models.Model):
    _name = "planviewap.session"
    _description = "planviewap_session"

    name = fields.Char(
        string="URL", required=True, default="https://myaccount.leankit.com"
    )

    api_token = fields.Char(required=True)

    sms_api_url = fields.Char()

    sms_api_token = fields.Char()

    sms_from_number_phone_default = fields.Char()

    sms_from_country_default = fields.Char(default="+1")

    sms_enable = fields.Boolean(
        default=False, help="Ignore this functionality if not enable."
    )

    extract_archive = fields.Boolean(help="Get list with archive.")

    bind_rh_employee_create_enabled = fields.Boolean(
        default=False, help="Will create employe in kanban agile place."
    )

    bind_rh_employee_delete_enabled = fields.Boolean(
        default=False, help="Will delete employe in kanban agile place."
    )

    production_enabled = fields.Boolean(
        default=False,
        help="Informe user this instance is ready for production.",
    )

    sms_to_number_phone_default = fields.Char(help="Separate multiple with ;")

    sms_to_country_default = fields.Char(default="+1")

    has_first_sync = fields.Boolean(
        default=False, readonly=True, help="Will be True when first sync done."
    )

    board_ids = fields.One2many(
        comodel_name="planviewap.board",
        inverse_name="session_id",
        string="Boards",
    )

    request_history_ids = fields.One2many(
        comodel_name="planviewap.request_history",
        inverse_name="session_id",
        string="Requests",
    )

    has_board_with_type = fields.Boolean(
        readonly=True, help="Will be filled by board when type is choose."
    )

    def request_api_get(self, path, data=None):
        return self._request_api(path, "get", data=data, is_param=True)

    def request_api_get_unlimited(self, path, data_name, data=None):
        return self._request_api_unlimited(
            path, "get", data_name, data=data, is_param=True
        )

    def request_api_patch(self, path, data=None):
        return self._request_api(path, "patch", data=data)

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
            if "pageMeta" in response.keys():
                end_row = response.get("pageMeta").get("endRow")
                data["offset"] = end_row
                total_records = response.get("pageMeta").get("totalRecords")
            else:
                # Force to finish it
                end_row = 0
                total_records = 0
            lst_data.extend(response.get(data_name))
        return lst_data

    def _request_api(self, path, type_request, data=None, is_param=False):
        if type_request == "get":
            cb_type_request = requests.get
        elif type_request == "post":
            cb_type_request = requests.post
        elif type_request == "delete":
            cb_type_request = requests.delete
        elif type_request == "patch":
            cb_type_request = requests.patch
        else:
            raise ValueError(f"Cannot support type request '{type_request}'")

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
                if total_second_to_wait > 0:
                    time.sleep(total_second_to_wait)
                else:
                    # sometime, the difference is lesser than a second
                    time.sleep(1)

                _logger.info(f"Wait done, continue!")
                continue
            has_finish = True

        reason = response.reason

        if response.status_code != 503 and response.text:
            try:
                response_data = json.loads(response.text)
            except Exception as e:
                response_data = ""
                _logger.error(e)
                reason += ";" + str(e)
        else:
            response_data = ""

        request_server_date = datetime.datetime.strptime(
            response.headers.get("Date"), "%a, %d %b %Y %H:%M:%S %Z"
        )

        request_history_value = {
            "name": url,
            "type": type_request,
            "session_id": self.id,
            "is_success": response.status_code == requests.codes.ok,
            "status_code": response.status_code,
            "reason": response.reason,
            "request_server_date": request_server_date,
            "response_data": response_data,
        }

        if data:
            request_history_value["send_data"] = json_data

        request_history_id = self.env["planviewap.request_history"].create(
            request_history_value
        )

        return response.status_code, response_data

    def action_clear_all(self):
        for rec in self:
            self.env["planviewap.customfield"].search(
                [("session_id", "=", rec.id)]
            ).unlink()
            self.env["planviewap.card"].search(
                [("session_id", "=", rec.id)]
            ).unlink()
            self.env["planviewap.card"].search(
                [("session_id", "=", rec.id), ("active", "=", False)]
            ).unlink()
            self.env["planviewap.card.type"].search(
                [("session_id", "=", rec.id)]
            ).unlink()
            self.env["planviewap.lane"].search(
                [("session_id", "=", rec.id)]
            ).unlink()
            self.env["planviewap.board"].search(
                [("session_id", "=", rec.id)]
            ).unlink()

    def action_production(self):
        is_first_execution = False
        for rec in self:
            rec.production_enabled = not rec.production_enabled
            rec.sms_enable = rec.production_enabled
            rec.bind_rh_employee_create_enabled = rec.production_enabled
            rec.bind_rh_employee_delete_enabled = rec.production_enabled

            if not is_first_execution:
                is_first_execution = True
                # Enable process over cron
                ir_cron_ids = self.env["ir.cron"].search(
                    [
                        ("model_name", "=", "planviewap.processus"),
                        ("active", "!=", rec.production_enabled),
                    ]
                )
                for ir_cron_id in ir_cron_ids:
                    ir_cron_id.active = rec.production_enabled

    def action_sync_board_info(self):
        board_ids = self.env["planviewap.board"]
        for rec in self:
            # Get all board
            # TODO configuration board
            # champs personnalisés champs telephone
            # effacer une carte
            if rec.extract_archive:
                data = {"archived": True}
            else:
                data = None
            status, response = rec.request_api_get("/io/board", data=data)
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
                board_id = self.env["planviewap.board"].search(
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
                    board_id = self.env["planviewap.board"].create(board_value)
                    board_ids += board_id
        return board_ids

    def action_sync_all(self):
        for rec in self:
            for board_id in rec.board_ids:
                # Refresh all board information
                board_id.action_sync()

    def action_sync_board(self):
        for rec in self:
            # Sync board with associate type
            for board_id in rec.board_ids:
                if board_id.type_board_ids:
                    board_id.action_sync()

    def search_board_with_type(self):
        for rec in self:
            has_type = False
            for board_id in rec.board_ids:
                has_type += bool(board_id.type_board_ids)
            rec.has_board_with_type = has_type
