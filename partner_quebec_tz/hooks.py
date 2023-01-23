# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, _, api

_logger = logging.getLogger(__name__)

default_tz = "America/Montreal"


def post_init_hook(cr, e):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Update all partner
        partners = env["res.partner"].search(
            [("tz", "=", False), ("active", "=", True)]
        )
        for partner in partners:
            partner.tz = default_tz

        # Update default tz
        field = env["ir.model.fields"].search(
            [("name", "=", "tz"), ("model", "=", "res.users")]
        )
        if len(field) != 1:
            if not field:
                raise Exception("Missing field tz in model res.partner.")
            raise Exception("Find too many fields tz in model res.partner.")

        # Validate it's an insert
        json_value = '"%s"' % default_tz
        check_default = env["ir.default"].search([("field_id", "=", field.id)])
        if check_default:
            if len(check_default) > 1:
                for field_id in check_default[1:]:
                    field_id.unlink()
                check_default = check_default[0]
            # Update default timezone
            check_default.json_value = json_value
        else:
            # Insert new timezone
            status = env["ir.default"].create(
                {"field_id": field.id, "json_value": json_value}
            )

            if not status:
                raise Exception(
                    "Error occur when insert default timezone to res.users."
                )
