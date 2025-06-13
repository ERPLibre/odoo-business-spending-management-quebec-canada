#!/usr/bin/env python3
# © 2025 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import json
import logging
import os.path
import random
import subprocess
import tempfile
from datetime import datetime
from pprint import pprint

import requests

from odoo import _, api, fields, models
from odoo.http import Response, request

_logger = logging.getLogger(__name__)


class AgendrixSession(models.Model):
    _name = "agendrix.session"
    _description = "agendrix_session"

    name = fields.Char()

    client_id = fields.Char(help="Client ID to use Agendrix")

    client_secret = fields.Char(help="Client Secret to use Agendrix")

    access_token = fields.Char(help="Token to send command by api to Agendrix")

    refresh_token = fields.Char(
        help="Token to refresh token by command by api to Agendrix"
    )

    production_enabled = fields.Boolean(default=False)

    workspace_name = fields.Char(help="The workspace name.")

    workspace_gid = fields.Char(
        help="The workspace number identity to works with."
    )

    def get_prefix_api_url(self, is_api=True):
        if is_api:
            if self.production_enabled:
                return "https://api.agendrix.com"
            return "https://api.sandbox.agendrix.net"
        if self.production_enabled:
            return ""
        return "https://sandbox.agendrix.net"

    def refresh_access_token(self, force=False):
        """curl --request POST 'https://app.agendrix.com/oauth/token' \
--header 'Content-Type: application/json' \
--data-raw '{
  "client_id": "{CLIENT_ID}",
  "client_secret": "{CLIENT_SECRET}",
  "redirect_uri": "{REDIRECT_URI}",
  "grant_type": "refresh_token",
  "refresh_token": "{REFRESH_TOKEN}",
}'"""
        if force or not self.access_token:
            with tempfile.NamedTemporaryFile() as tmp:
                _logger.info(
                    "Run automation script to extract Agendrix token."
                )
                script = f"./.venv/bin/python ./script/selenium/selenium_agendrix.py --agendrix_test --scenario all --url https://developers.agendrix.com/fr/sign-in --is_sandbox --filepath_output_token {tmp.name} --headless"
                process = subprocess.Popen(
                    script,
                    shell=True,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                stdout, stderr = process.communicate()
                status_code = process.returncode
                if stderr:
                    _logger.error(stderr)
                    _logger.error(f"status_code={status_code}")
                if os.path.isfile(tmp.name):
                    with open(tmp.name) as f:
                        data_token = json.load(f)
                    if not data_token:
                        _logger.error(
                            f"Cannot read or extract json from temp file Agendrix token."
                        )
                    else:
                        self.client_id = data_token["client_id"]
                        self.client_secret = data_token["client_secret"]
                        self.access_token = data_token["token"]
                        self.refresh_token = data_token["refresh_token"]
                else:
                    _logger.error(
                        f"Automation Agendrix generate token didn't create data file."
                    )

    def create_resources(
        self, resource_name, resource_address, type_job_site=True
    ):
        if not self.access_token:
            self.refresh_access_token(force=True)
            if not self.access_token:
                _logger.error(f"Cannot get access token Agendrix.")
                return

        def request_ressources():
            url = f"{self.get_prefix_api_url()}/v1/resources"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
            }
            data_json = {
                "name": resource_name,
                "address": resource_address,
                "type_job_site": type_job_site,
            }
            response = requests.post(url, headers=headers, json=data_json)
            return response

        response = request_ressources()

        # Pour obtenir le JSON de la réponse
        json_response = response.json()
        if json_response.get("errors"):
            errors = json_response.get("errors")
            if errors == [
                {
                    "short_message": "Your token is expired. Refresh it using the refresh token.",
                    "source": "unauthorized",
                }
            ]:
                # Refresh it
                self.refresh_access_token(force=True)
                response = request_ressources()
                if json_response.get("errors"):
                    errors = json_response.get("errors")
                    _logger.error(errors)
                    return
        json_data = json_response.get("data")

        created_at = json_data.get("created_at")
        if created_at.endswith("Z"):
            created_at = created_at[:-1]
        parse_created_at = datetime.strptime(
            created_at, "%Y-%m-%dT%H:%M:%S.%f"
        )

        updated_at = json_data.get("updated_at")
        if updated_at.endswith("Z"):
            updated_at = updated_at[:-1]
        parse_updated_at = datetime.strptime(
            updated_at, "%Y-%m-%dT%H:%M:%S.%f"
        )

        resource_values = {
            "name": json_data.get("name"),
            "address": json_data.get("address"),
            "agendrix_id_no": json_data.get("id"),
            "type_job_site": json_data.get("type_job_site"),
            "agendrix_create_at": parse_created_at,
            "agendrix_update_at": parse_updated_at,
        }
        resource_id = self.env["agendrix.resource"].create(resource_values)
        return resource_id
