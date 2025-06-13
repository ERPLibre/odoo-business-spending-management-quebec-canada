#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import json
import logging
import os
import uuid

import requests
import werkzeug.utils
import werkzeug.wrappers
from werkzeug.utils import redirect

from odoo import http
from odoo.http import Response, request
from odoo.tools import config

_logger = logging.getLogger(__name__)


class AgendrixController(http.Controller):

    pass
