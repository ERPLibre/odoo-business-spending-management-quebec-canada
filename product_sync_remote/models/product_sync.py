# Copyright 2025 MathBenTech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import math
import xmlrpc.client

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductSyncJob(models.Model):
    _name = "product.sync.job"
    _description = "Product Sync Job"

    name = fields.Char(default=lambda self: _("Synchronisation de produits"))
    remote_url = fields.Char(
        required=True,
        help="URL racine de l'instance source, ex: https://source.example.com",
    )
    remote_db = fields.Char(
        required=True, help="Nom de la base de données source"
    )
    remote_user = fields.Char(required=True)
    remote_password = fields.Char(required=True)

    state = fields.Selection(
        [
            ("draft", "Brouillon"),
            ("running", "En cours"),
            ("done", "Terminé"),
            ("failed", "Échec"),
        ],
        default="draft",
    )

    last_log = fields.Text(readonly=True)
    create_missing_attributes = fields.Boolean(
        default=True,
        help="Créer automatiquement les attributs/valeurs manquants",
    )
    update_existing = fields.Boolean(
        default=True,
        help="Mettre à jour les produits existants (match par default_code ou nom)",
    )
    limit = fields.Integer(
        default=0,
        help="Limiter le nombre de templates à synchroniser (0 = tous)",
    )
    processed_count = fields.Integer(readonly=True)

    def _rpc(self, path):
        self.ensure_one()
        url = self.remote_url.rstrip("/") + path
        return xmlrpc.client.ServerProxy(url, allow_none=True)

    def _connect(self):
        self.ensure_one()
        try:
            common = self._rpc("/xmlrpc/2/common")
            uid = common.authenticate(
                self.remote_db, self.remote_user, self.remote_password, {}
            )
            if not uid:
                raise UserError(_("Échec d'authentification sur la source."))
            models_obj = self._rpc("/xmlrpc/2/object")
            return uid, models_obj
        except Exception as e:
            raise UserError(_("Connexion XML-RPC échouée: %s") % e)

    def action_run(self):
        for job in self:
            job.write(
                {
                    "state": "running",
                    "last_log": _("Démarrage..."),
                    "processed_count": 0,
                }
            )
            try:
                uid, models_obj = job._connect()

                # 0) website
                website_ids = models_obj.execute_kw(
                    job.remote_db,
                    uid,
                    job.remote_password,
                    "website",
                    "search",
                    [[]],
                )
                websites = models_obj.execute_kw(
                    job.remote_db,
                    uid,
                    job.remote_password,
                    "website",
                    "read",
                    [website_ids],
                    {"fields": ["name", "domain", "logo"]},
                )
                website_by_id = {}
                for dct_website in websites:
                    website_id = self.env["website"].search(
                        [("domain", "=", dct_website.get("domain"))]
                    )
                    if website_id:
                        website_id.name = dct_website.get("name")
                        website_id.logo = dct_website.get("logo")
                    else:
                        website_id = self.env["website"].create(
                            {
                                "name": dct_website.get("name"),
                                "domain": dct_website.get("domain"),
                                "logo": dct_website.get("logo"),
                            }
                        )
                    website_by_id[dct_website.get("id")] = website_id

                # 1) Charger attributs/valeurs (pour map id -> nom)
                attr_ids = models_obj.execute_kw(
                    job.remote_db,
                    uid,
                    job.remote_password,
                    "product.attribute",
                    "search",
                    [[("active", "=", True)]],
                )
                attributes = models_obj.execute_kw(
                    job.remote_db,
                    uid,
                    job.remote_password,
                    "product.attribute",
                    "read",
                    [attr_ids],
                    {"fields": ["name", "create_variant", "display_type"]},
                )
                # attr_by_id = {a["id"]: a for a in attributes}

                product_att_id_by_id = {}
                for dct_attr_value in attributes:
                    existing_product_attr_id = self.env[
                        "product.attribute"
                    ].search([("name", "=", dct_attr_value["name"])])
                    if not existing_product_attr_id:
                        existing_product_attr_id = self.env[
                            "product.attribute"
                        ].create(
                            {
                                "name": dct_attr_value["name"],
                                "display_type": dct_attr_value["display_type"],
                                "create_variant": dct_attr_value[
                                    "create_variant"
                                ],
                            }
                        )
                    else:
                        existing_product_attr_id.name = dct_attr_value["name"]
                        existing_product_attr_id.display_type = dct_attr_value[
                            "display_type"
                        ]
                    product_att_id_by_id[dct_attr_value.get("id")] = (
                        existing_product_attr_id
                    )

                val_ids = models_obj.execute_kw(
                    job.remote_db,
                    uid,
                    job.remote_password,
                    "product.attribute.value",
                    "search",
                    [[("active", "=", True)]],
                )
                values = models_obj.execute_kw(
                    job.remote_db,
                    uid,
                    job.remote_password,
                    "product.attribute.value",
                    "read",
                    [val_ids],
                    {
                        "fields": [
                            "name",
                            "attribute_id",
                            "html_color",
                            "color",
                        ]
                    },
                )
                # val_by_id = {v["id"]: v for v in values}

                product_att_value_id_by_id = {}
                for dct_attr_value in values:
                    parent_att_id_remote = dct_attr_value["attribute_id"][0]
                    parent_att_id = product_att_id_by_id.get(
                        parent_att_id_remote
                    )
                    if parent_att_id is None:
                        continue
                    existing_product_attr_value_id = self.env[
                        "product.attribute.value"
                    ].search(
                        [
                            ("name", "=", dct_attr_value["name"]),
                            ("attribute_id", "=", parent_att_id.id),
                        ]
                    )
                    if not existing_product_attr_value_id:
                        existing_product_attr_value_id = self.env[
                            "product.attribute.value"
                        ].create(
                            {
                                "name": dct_attr_value["name"],
                                "attribute_id": parent_att_id.id,
                                "color": dct_attr_value["color"],
                                "html_color": dct_attr_value["html_color"],
                            }
                        )
                    else:
                        existing_product_attr_value_id.name = dct_attr_value[
                            "name"
                        ]
                        existing_product_attr_value_id.color = dct_attr_value[
                            "color"
                        ]
                        existing_product_attr_value_id.html_color = (
                            dct_attr_value["html_color"]
                        )
                    product_att_value_id_by_id[dct_attr_value.get("id")] = (
                        existing_product_attr_value_id
                    )

                # 2) Compter les templates
                domain = [("sale_ok", "in", [True, False])]
                total = models_obj.execute_kw(
                    job.remote_db,
                    uid,
                    job.remote_password,
                    "product.template",
                    "search_count",
                    [domain],
                )
                if job.limit and job.limit < total:
                    total = job.limit

                batch = 10
                processed = 0
                page_count = math.ceil(total / batch) if total else 0

                for page in range(page_count):
                    # ids page
                    ids = models_obj.execute_kw(
                        job.remote_db,
                        uid,
                        job.remote_password,
                        "product.template",
                        "search",
                        [domain],
                        {
                            "offset": page * batch,
                            "limit": min(batch, total - processed),
                            "order": "id",
                        },
                    )
                    if not ids:
                        break
                    fields_to_read = [
                        "name",
                        "default_code",
                        "type",
                        "list_price",
                        "standard_price",
                        "uom_id",
                        "uom_po_id",
                        "categ_id",
                        "barcode",
                        "image_1920",
                        "attribute_line_ids",
                        "description",
                        "description_sale",
                        "product_template_image_ids",
                        "public_categ_ids",
                        "website_id",
                    ]
                    templates = models_obj.execute_kw(
                        job.remote_db,
                        uid,
                        job.remote_password,
                        "product.template",
                        "read",
                        [ids],
                        {"fields": fields_to_read},
                    )

                    # Read attribute lines so we can recreate matrix
                    line_fields = [
                        "attribute_id",
                        "value_ids",
                        "product_template_value_ids",
                    ]
                    line_map = {}
                    for t in templates:
                        if t["attribute_line_ids"]:
                            lines = models_obj.execute_kw(
                                job.remote_db,
                                uid,
                                job.remote_password,
                                "product.template.attribute.line",
                                "read",
                                [t["attribute_line_ids"]],
                                {"fields": line_fields},
                            )
                            line_map[t["id"]] = lines
                        else:
                            line_map[t["id"]] = []

                    # Fetch variants for each template
                    for t in templates:
                        # get products (variants)
                        prod_ids = models_obj.execute_kw(
                            job.remote_db,
                            uid,
                            job.remote_password,
                            "product.product",
                            "search",
                            [[("product_tmpl_id", "=", t["id"])]],
                        )
                        variants = []
                        if prod_ids:
                            step = 1000
                            nombre_limit = len(prod_ids)
                            lst_result_to_fetch = [
                                a for a in range(step, nombre_limit + 1, step)
                            ]
                            if nombre_limit not in lst_result_to_fetch:
                                lst_result_to_fetch.append(nombre_limit)
                            last_i = 0
                            for nombre in lst_result_to_fetch:
                                variants1 = models_obj.execute_kw(
                                    job.remote_db,
                                    uid,
                                    job.remote_password,
                                    "product.product",
                                    "read",
                                    [prod_ids[last_i:nombre]],
                                    {
                                        "fields": [
                                            "name",
                                            "default_code",
                                            "barcode",
                                            "list_price",
                                            "standard_price",
                                            "attribute_line_ids",
                                            "product_template_variant_value_ids",
                                            # "attribute_value_line_ids",
                                            "image_1920",
                                            "active",
                                        ]
                                    },
                                )
                                variants.extend(variants1)
                                last_i = nombre
                        self.env.cr.commit()  # avoid long tx
                        _logger.info(f"Sync product #{processed}/{total}")
                        self._sync_single_template(
                            t,
                            line_map[t["id"]],
                            variants,
                            website_by_id,
                            product_att_id_by_id,
                            product_att_value_id_by_id,
                            job,
                            uid,
                            models_obj,
                        )
                        processed += 1
                        job.write(
                            {
                                "processed_count": processed,
                                "last_log": _("%s / %s traités")
                                % (processed, total),
                            }
                        )

                job.write(
                    {
                        "state": "done",
                        "last_log": _("Terminé: %s templates synchronisés")
                        % processed,
                    }
                )
            except Exception as e:
                job.write({"state": "failed", "last_log": str(e)})

    def _sync_single_template(
        self,
        tmpl,
        lines,
        variants,
        website_by_id,
        product_att_id_by_id,
        product_att_value_id_by_id,
        job,
        uid,
        models_obj,
    ):
        # 1) Category, UoM
        categ_id = False
        if tmpl.get("categ_id"):
            categ = (
                self.env["product.category"]
                .sudo()
                .search([("name", "=", tmpl["categ_id"][1])], limit=1)
            )
            if not categ:
                categ = (
                    self.env["product.category"]
                    .sudo()
                    .create({"name": tmpl["categ_id"][1]})
                )
            categ_id = categ.id

        def _find_uom(uom_tuple):
            if not uom_tuple:
                return False
            # INFO not working because translation not supported
            # name = uom_tuple[1]
            # uom = self.env["uom.uom"].search([("name", "=", name)], limit=1)
            # return uom.id if uom else False
            return uom_tuple[0]

        def _find_website(website_tuple):
            if not website_tuple:
                return False
            return_status = website_by_id.get(website_tuple[0])
            if return_status:
                return return_status.id
            return False

        vals_tmpl = {
            "name": tmpl["name"],
            "type": tmpl.get("type") or "product",
            "list_price": tmpl.get("list_price") or 0.0,
            "standard_price": tmpl.get("standard_price") or 0.0,
            "barcode": tmpl.get("barcode") or False,
            "default_code": tmpl.get("default_code") or False,
            "uom_id": _find_uom(tmpl.get("uom_id")),
            "uom_po_id": _find_uom(tmpl.get("uom_po_id")),
            "categ_id": categ_id,
            "description": tmpl.get("description") or False,
            "description_sale": tmpl.get("description_sale") or False,
            "image_1920": tmpl.get("image_1920") or False,
            "website_id": _find_website(tmpl.get("website_id")),
        }

        # Find existing template by default_code or name
        if vals_tmpl["default_code"]:
            domain = [
                "|",
                ("default_code", "=", vals_tmpl["default_code"]),
                ("name", "=", vals_tmpl["name"]),
            ]
        else:
            domain = [("name", "=", vals_tmpl["name"])]
        dest_tmpl = self.env["product.template"].sudo().search(domain, limit=1)

        if dest_tmpl:
            if self.update_existing:
                dest_tmpl.write(vals_tmpl)
        else:
            dest_tmpl = self.env["product.template"].sudo().create(vals_tmpl)

        # Associate image
        product_image_ids = models_obj.execute_kw(
            job.remote_db,
            uid,
            job.remote_password,
            "product.image",
            "search",
            [[("product_tmpl_id", "=", tmpl.get("id"))]],
        )
        if product_image_ids:
            lst_dct_image = models_obj.execute_kw(
                job.remote_db,
                uid,
                job.remote_password,
                "product.image",
                "read",
                [product_image_ids],
                {"fields": ["sequence", "image_1920", "name"]},
            )
            lst_copy_dct_image = []
            for dct_image in lst_dct_image:
                dct_image["product_tmpl_id"] = dest_tmpl.id
                # del dct_image["id"]
                product_image_id = self.env["product.image"].search(
                    [
                        ("image_1920", "=", dct_image["image_1920"]),
                        ("product_tmpl_id", "=", dct_image["product_tmpl_id"]),
                    ]
                )
                if not product_image_id:
                    # Ignore doublon
                    lst_copy_dct_image.append(
                        {
                            "sequence": dct_image["sequence"],
                            "image_1920": dct_image["image_1920"],
                            "name": dct_image["name"],
                            "product_tmpl_id": dct_image["product_tmpl_id"],
                        }
                    )
            self.env["product.image"].create(lst_copy_dct_image)

        # 2) Build attribute lines on template
        attr_line_commands = []
        for l in lines:
            attribute_id_i = l["attribute_id"][0]
            pa_id = product_att_id_by_id.get(attribute_id_i)
            lst_value_ids_to_remove = []
            for ptal in dest_tmpl.attribute_line_ids:
                if pa_id.id == ptal.attribute_id.id:
                    lst_value_ids_to_remove.extend(ptal.value_ids.ids)
                    break

            value_ids_b = [
                product_att_value_id_by_id[a].id for a in l["value_ids"]
            ]
            value_ids = list(set(value_ids_b) - set(lst_value_ids_to_remove))
            if value_ids:
                attr_line_commands.append(
                    (
                        0,
                        0,
                        {
                            "attribute_id": pa_id.id,
                            "value_ids": [(6, 0, value_ids)],
                        },
                    )
                )

        if attr_line_commands:
            dest_tmpl.write({"attribute_line_ids": attr_line_commands})

        dct_mapping_product_template_attribute_value = {}
        for att_line_id in dest_tmpl.attribute_line_ids:
            dct_att_line_value = {}
            dct_mapping_product_template_attribute_value[
                att_line_id.display_name
            ] = dct_att_line_value
            for att_value_id in att_line_id.product_template_value_ids:
                dct_att_line_value[att_value_id.name] = att_value_id

        dct_association_product_template_attribute_value = {}
        # Update fees
        for l in lines:
            lst_product_tav = models_obj.execute_kw(
                job.remote_db,
                uid,
                job.remote_password,
                "product.template.attribute.value",
                "read",
                [l.get("product_template_value_ids")],
                {
                    "fields": [
                        "name",
                        "price_extra",
                        "attribute_id",
                        "attribute_line_id",
                        "color",
                        "html_color",
                        "is_custom",
                    ]
                },
            )
            if not lst_product_tav:
                continue
            str_attr = lst_product_tav[0].get("attribute_id")[1]
            dct_attribute = dct_mapping_product_template_attribute_value.get(
                str_attr
            )
            for product_tav in lst_product_tav:
                ptav_id = dct_attribute.get(product_tav.get("name"))
                ptav_id.html_color = product_tav.get("html_color")
                ptav_id.price_extra = product_tav.get("price_extra")
                ptav_id.is_custom = product_tav.get("is_custom")
                ptav_id.color = product_tav.get("color")
                dct_association_product_template_attribute_value[
                    product_tav.get("id")
                ] = ptav_id

        # 3) Sync variants (product.product)
        ProductProduct = self.env["product.product"]
        for v in variants:
            # find variant by default_code or barcode under template
            lst_ids_ptvv = v.get("product_template_variant_value_ids")
            lst_associate_ids_ptvv = sorted(
                [
                    dct_association_product_template_attribute_value[a].id
                    for a in lst_ids_ptvv
                ]
            )
            str_associate_ids_ptvv = ",".join(
                [str(a) for a in lst_associate_ids_ptvv]
            )
            v_domain = [
                ("product_tmpl_id", "=", dest_tmpl.id),
                ("combination_indices", "=", str_associate_ids_ptvv),
            ]
            if v.get("default_code"):
                v_domain = (
                    ["&"]
                    + v_domain
                    + [
                        "|",
                        ("default_code", "=", v["default_code"]),
                        ("barcode", "=", v.get("barcode") or False),
                    ]
                )
            elif v.get("barcode"):
                v_domain.append(("barcode", "=", v["barcode"]))

            dest_variant = ProductProduct.sudo().search(v_domain)
            if len(dest_variant) > 1:
                _logger.error(
                    f"Find multiple product for combination '{str_associate_ids_ptvv}'"
                )
            v_vals = {
                "product_tmpl_id": dest_tmpl.id,
                "name": v.get("name") or dest_tmpl.name,
                "default_code": v.get("default_code") or False,
                "barcode": v.get("barcode") or False,
                # "list_price": v.get("list_price") or dest_tmpl.list_price,
                # "standard_price": v.get("standard_price")
                # or dest_tmpl.standard_price,
                "image_1920": v.get("image_1920") or False,
                # "attribute_line_ids": (
                #     [(6, 0, comb_vals)] if comb_vals else [(5, 0, 0)]
                # ),
                "active": v.get("active", True),
            }
            if dest_variant:
                if self.update_existing:
                    dest_variant.write(v_vals)
            else:
                # ProductProduct.sudo().create(v_vals)
                _logger.error(
                    f"Missing product.product associate with '{str_associate_ids_ptvv}'"
                )
