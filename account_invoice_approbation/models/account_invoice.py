# Copyright 2020 TechnoLibre. (https://technolibre.ca)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _get_default_require_signature(self):
        return self.env.user.company_id.portal_invoice_confirmation_sign

    # def _get_default_require_payment(self):
    #     return self.env.user.company_id.portal_confirmation_pay

    require_signature = fields.Boolean('Online Signature',
                                       default=_get_default_require_signature,
                                       readonly=True,
                                       states={'draft': [('readonly', False)]},
                                       help='Request a online signature to the customer in invoice to confirm invoices automatically.')
    # require_payment = fields.Boolean('Online Payment',
    #                                  default=_get_default_require_payment,
    #                                  readonly=True,
    #                                  states={'draft': [('readonly', False)],
    #                                          'sent': [('readonly', False)]},
    #                                  help='Request an online payment to the customer in invoice to confirm invoices automatically.')

    confirmation_date = fields.Datetime(string='Confirmation Date', readonly=True,
                                        index=True,
                                        help="Date on which the sales order is confirmed.",
                                        oldname="date_confirm", copy=False)

    signature = fields.Binary('Signature',
                              help='Signature received through the portal.', copy=False,
                              attachment=True)
    signed_by = fields.Char('Signed by', help='Name of the person that signed the SO.',
                            copy=False)

    def has_to_be_signed(self, also_in_draft=False):
        return self.state == 'draft' and also_in_draft and self.require_signature and not self.signature
