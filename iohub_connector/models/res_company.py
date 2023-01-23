# -*- coding: utf-8 -*-
# Copyright 2021 Apulia Software s.r.l. (<info@apuliasoftware.it>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    iohub_box_ids = fields.Many2many(
        comodel_name="iohub.box",
        string="IOhub boxes",
        help="Link boxes to the company",
    )
