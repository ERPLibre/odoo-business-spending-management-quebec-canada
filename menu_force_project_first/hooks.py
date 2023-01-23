# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, e):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        menus = env["ir.ui.menu"].search(
            [("parent_id", "=", False), ("name", "=", "Project")]
        )
        menus.write({"sequence": -10})
