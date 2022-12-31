# Copyright 2020 TechnoLibre. (https://technolibre.ca)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalAccount(CustomerPortal):

    @http.route(['/my/invoices/<int:invoice_id>/accept'], type='json', auth="public",
                website=True)
    def portal_invoice_accept(self, res_id, access_token=None,
                              partner_name=None, signature=None, invoice_id=None):
        try:
            invoice_sudo = self._document_check_access('account.invoice', res_id,
                                                       access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid invoice')}

        if not invoice_sudo.has_to_be_signed(also_in_draft=True):
            return {
                'error': _('Invoice is not in a state requiring customer signature.')}
        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            invoice_sudo.action_invoice_open()
        except Exception as e:
            error = _("Internal error occur : %s") % e
            return {'error': error}

        invoice_sudo.signature = signature
        invoice_sudo.signed_by = partner_name

        pdf = request.env.ref('account.account_invoices').sudo().render_qweb_pdf(
            [invoice_sudo.id])[0]
        _message_post_helper(
            res_model='account.invoice',
            res_id=invoice_sudo.id,
            message=_('Order signed by %s') % (partner_name,),
            attachments=[('%s.pdf' % invoice_sudo.name, pdf)],
            **({'token': access_token} if access_token else {}))

        return {
            'force_refresh': True,
            'redirect_url': invoice_sudo.get_portal_url(
                query_string='&message=sign_ok'),
        }

    @http.route(['/my/invoices/<int:invoice_id>/decline'], type='http', auth='public',
                methods=['POST'], website=True, csrf=False)
    def decline(self, invoice_id, access_token=None, *args, **post):
        try:
            invoice_sudo = self._document_check_access('account.invoice', invoice_id,
                                                       access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        message = post.get('decline_message')

        query_string = False
        if invoice_sudo.has_to_be_signed() and message:
            # TODO add rejected state in invoice
            # invoice_sudo.action_cancel()
            _message_post_helper(message=message, res_id=invoice_id,
                                 res_model='account.invoice',
                                 **{'token': access_token} if access_token else {})
        else:
            query_string = "&message=cant_reject"

        return request.redirect(invoice_sudo.get_portal_url(query_string=query_string))
