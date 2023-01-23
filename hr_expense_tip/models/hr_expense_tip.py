# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp


class HrExpenseTip(models.Model):
    _inherit = "hr.expense"

    unit_amount_compute = fields.Float(
        "Unit Price Compute",
        compute="_compute_unit_amount_compute",
        digits=dp.get_precision("Product Price"),
        store=False,
    )

    tip = fields.Float(
        "Tip",
        readonly=True,
        required=False,
        states={
            "draft": [("readonly", False)],
            "reported": [("readonly", False)],
            "refused": [("readonly", False)],
        },
        digits=dp.get_precision("Product Price"),
    )

    total_tip_amount_included = fields.Float(
        "Total tip included",
        readonly=True,
        compute="_compute_tip_amount",
        digits=dp.get_precision("Product Price"),
    )

    total_tip_amount_included_company = fields.Monetary(
        "Total tip included (Company Currency)",
        compute="_compute_total_tip_amount_included_company",
        store=True,
        currency_field="company_currency_id",
        digits=dp.get_precision("Account"),
    )

    total_tip_amount_included_entry = fields.Float(
        "Total tip included entry",
        readonly=True,
        required=False,
        states={
            "draft": [("readonly", False)],
            "reported": [("readonly", False)],
            "refused": [("readonly", False)],
        },
        digits=dp.get_precision("Product Price"),
        help="Enter your total tip included to compute tip automatic.",
    )

    @api.depends(
        "quantity",
        "unit_amount",
        "tax_ids",
        "currency_id",
        "tip",
        "total_tip_amount_included_entry",
    )
    def _compute_unit_amount_compute(self):
        for expense in self:
            # Must not compute if missing total_tip_amount_included_entry or when missing product
            # when choosing product, it overwrite price
            if (
                not expense.total_tip_amount_included_entry
                or not expense.product_id
            ):
                continue

            if not expense.unit_amount and expense.tip:
                # Sequence (tax,total_tip_amount_included_entry,tip)
                # Support unit amount without taxes. Recompute when taxes is chosen
                expense.unit_amount_compute = expense.tip
                total = expense.total_tip_amount_included_entry - expense.tip

                # To find the unit_amount, calculate the reversed taxes and subtract from total
                # The bigger the magic number the more precision you get
                magic_number = 1000000
                taxes = expense.tax_ids.compute_all(
                    magic_number,
                    None,
                    1.0,
                    expense.product_id,
                    expense.employee_id.user_id.partner_id,
                )
                calculate_reverse_taxes = (
                    taxes.get("total_included", 1.0) / magic_number
                )

                expense.unit_amount = total / calculate_reverse_taxes
            elif not expense.unit_amount and not expense.tip:
                # Sequence (total_tip_amount_included_entry,tax or no tax)
                # Nothing to compute with only one number
                continue
            elif not expense.tip and expense.unit_amount:
                # Sequence (total_tip_amount_included_entry,(tax,unit_amount|unit_amount,tax))
                expense.tip = (
                    expense.total_tip_amount_included_entry
                    - expense.total_amount
                )

    @api.depends("total_amount", "tip", "total_tip_amount_included_entry")
    def _compute_tip_amount(self):
        for expense in self:
            expense.total_tip_amount_included = (
                expense.total_amount + expense.tip
            )

    @api.depends(
        "date",
        "total_amount",
        "company_currency_id",
        "tip",
        "total_tip_amount_included_entry",
    )
    def _compute_total_tip_amount_included_company(self):
        for expense in self:
            tip_amount_included = 0
            if expense.company_currency_id:
                date_expense = expense.date
                tip_amount_included = expense.currency_id._convert(
                    expense.total_tip_amount_included,
                    expense.company_currency_id,
                    expense.company_id,
                    date_expense or fields.Date.today(),
                )
            expense.total_tip_amount_included_company = tip_amount_included


class HrExpenseTipSheet(models.Model):
    _inherit = "hr.expense.sheet"

    default_amount = fields.Monetary(
        "Default amount when register payment",
        compute="_compute_default_amount",
        store=False,
        currency_field="currency_id",
        digits=dp.get_precision("Account"),
    )

    total_tip_amount_included = fields.Monetary(
        "Total tip included",
        compute="_compute_tip_amount_included",
        store=True,
        currency_field="currency_id",
        digits=dp.get_precision("Account"),
    )

    @api.depends(
        "expense_line_ids.total_amount",
        "expense_line_ids.total_tip_amount_included_company",
    )
    def _compute_default_amount(self):
        refund_total_tip_amount_included_to_employee = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "hr_expense.refund_total_tip_amount_included_to_employee"
            )
        )

        for sheet in self:
            if refund_total_tip_amount_included_to_employee:
                sheet.default_amount = sheet.total_tip_amount_included
            else:
                sheet.default_amount = sheet.total_amount

    @api.depends("expense_line_ids.total_tip_amount_included_company")
    def _compute_tip_amount_included(self):
        for sheet in self:
            sheet.total_tip_amount_included = sum(
                sheet.expense_line_ids.mapped(
                    "total_tip_amount_included_company"
                )
            )
