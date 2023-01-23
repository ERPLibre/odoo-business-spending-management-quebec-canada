# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, _, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, e):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        companies = env["res.company"].search([])
        for company in companies:
            company.account_sale_tax_id = (
                env["account.tax"]
                .search(
                    [
                        ("company_id", "=", company.id),
                        ("name", "=", env.ref("l10n_ca.gstqst_sale_en").name),
                    ]
                )
                .id
            )
            company.account_purchase_tax_id = (
                env["account.tax"]
                .search(
                    [
                        ("company_id", "=", company.id),
                        ("name", "=", env.ref("l10n_ca.gstqst_purc_en").name),
                    ]
                )
                .id
            )
