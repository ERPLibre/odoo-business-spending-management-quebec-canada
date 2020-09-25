# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import _, api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init_hook(cr, e):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
