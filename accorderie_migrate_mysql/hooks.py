# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import base64
from odoo import _, api, SUPERUSER_ID
import collections
# from odoo.exceptions import ValidationError
import pickle
import os

_logger = logging.getLogger(__name__)

try:
    import MySQLdb

    assert MySQLdb
except (ImportError, AssertionError):
    _logger.info('MySQLdb not available. Please install "mysqlclient" python package.')

# TODO update me with your backup version
BACKUP_PATH = "/home/mathben/Documents/technolibre/accorderie/accorderie20200826/Intranet"
FILE_PATH = f"{BACKUP_PATH}/document/doc"
SECRET_PASSWORD = ""
DEBUG_LIMIT = False
LIMIT = 200
GENERIC_EMAIL = f"%s_membre@accorderie.ca"
CACHE_FILE = os.path.join(os.path.dirname(__file__), '.cache')


def post_init_hook(cr, e):
    print("Start migration of Accorderie of Quebec.")
    migration = MigrationAccorderie(cr)

    # General configuration
    migration.setup_configuration()

    # Create company
    migration.migrate_company()

    # Create file
    migration.migrate_muk_dms()

    # Create product
    migration.migrate_product()

    # Create user
    migration.migrate_member()

    # migration.migrate_tbl_categorie(dry_run=False)
    # migration.migrate_tbl_sous_categorie(dry_run=False)
    # migration.migrate_tbl_categorie_sous_categorie(dry_run=False)
    #
    # Update user configuration
    migration.update_user(dry_run=False)


class Struct(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)


class MigrationAccorderie:
    def __init__(self, cr):
        assert MySQLdb
        self.host = "localhost"
        self.user = "accorderie"
        self.passwd = "accorderie"
        self.db_name = "accorderie_log_2019_2"
        self.conn = MySQLdb.connect(host=self.host, user=self.user, passwd=self.passwd, db=self.db_name)
        # Path of the backup
        self.source_code_path = BACKUP_PATH
        self.logo_path = f"{self.source_code_path}/images/logo"
        self.cr = cr

        self.dct_accorderie = {}
        # self.dct_accorderie_by_email = {}
        self.dct_pointservice = {}
        self.dct_fichier = {}
        self.dct_produit = {}
        self.dct_membre = {}

        self._fill_cache_obj()

        self.dct_tbl = self._fill_tbl()

    def _fill_cache_obj(self):
        """Read cache"""

        def get_obj(name, model, field_search=None):
            if name not in db:
                return {}
            # Get all obj with browse id
            with api.Environment.manage():
                env = api.Environment(self.cr, SUPERUSER_ID, {})
            if not field_search:
                return {a: env[model].browse(b) for a, b in db.get(name).items()}
            return {a: env[model].search([(field_search, '=', a)]) for a, b in db.get(name).items()}

        if not os.path.isfile(CACHE_FILE):
            return
        db_file = open(CACHE_FILE, 'rb')
        db = pickle.load(db_file)
        if db:
            self.dct_accorderie = get_obj("dct_accorderie", "res.company")
            # self.dct_accorderie_by_email = get_obj("dct_accorderie_by_email", "res.company", field_search="email")
            # self.dct_accorderie_by_email = get_obj("dct_accorderie_by_email", "res.company")
            self.dct_pointservice = get_obj("dct_pointservice", "res.company")
            self.dct_fichier = get_obj("dct_fichier", "muk_dms.file")
            self.dct_produit = get_obj("dct_produit", "product.template")
            self.dct_membre = get_obj("dct_membre", "res.users")
        db_file.close()

    def _update_cache_obj(self):
        """Write cache"""
        # database
        db = {}
        db['dct_accorderie'] = {a: b.id for a, b in self.dct_accorderie.items()}
        # db['dct_accorderie_by_email'] = {a: b.id for a, b in self.dct_accorderie_by_email.items()}
        db['dct_pointservice'] = {a: b.id for a, b in self.dct_pointservice.items()}
        db['dct_fichier'] = {a: b.id for a, b in self.dct_fichier.items()}
        db['dct_produit'] = {a: b.id for a, b in self.dct_produit.items()}
        db['dct_membre'] = {a: b.id for a, b in self.dct_membre.items()}

        # Its important to use binary mode
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        db_file = open(CACHE_FILE, 'ab')

        # source, destination
        pickle.dump(db, db_file)
        db_file.close()

    def _fill_tbl(self):
        """
        Fill all database in self.dct_tbl
        :return:
        """
        cur = self.conn.cursor()
        # Get all tables
        str_query = f"""SHOW tables;"""
        cur.nextset()
        cur.execute(str_query)
        tpl_result = cur.fetchall()

        lst_ignore_table = ["tbl_log_acces",
                            "tbl_commande_membre_produit",
                            "tbl_echange_service",
                            "tbl_fournisseur_produit_commande"]

        dct_tbl = {a[0]: [] for a in tpl_result if "tbl" in a[0]}

        for table, lst_column in dct_tbl.items():
            if table in lst_ignore_table:
                print(f"Skip table '{table}'")
                continue

            print(f"Import in cache table '{table}'")
            str_query = f"""SHOW COLUMNS FROM {table};"""
            cur.nextset()
            cur.execute(str_query)
            tpl_result = cur.fetchall()
            lst_column_name = [a[0] for a in tpl_result]

            if table == "tbl_membre":
                str_query = f"""SELECT *,DECODE(MotDePasse,'{SECRET_PASSWORD}') AS MotDePasseRaw FROM tbl_membre;"""
                lst_column_name.append("MotDePasseRaw")
            else:
                str_query = f"""SELECT * FROM {table};"""
            cur.nextset()
            cur.execute(str_query)
            tpl_result = cur.fetchall()

            for lst_result in tpl_result:
                i = -1
                dct_value = {}
                for result in lst_result:
                    i += 1
                    # Exception fix database
                    if table == "tbl_membre" and lst_column_name[i] == "Courriel" and lst_result[0] == 927:
                        result = "mercier-hochelaga-maisonneuve@accorderie.ca"
                    dct_value[lst_column_name[i]] = result
                lst_column.append(Struct(**dct_value))

        return Struct(**dct_tbl)

    def _get_ville(self, no_ville: int):
        for ville in self.dct_tbl.tbl_ville:
            if ville.NoVille == no_ville:
                return ville

    def _get_membre(self, no_membre: int):
        for membre in self.dct_tbl.tbl_membre:
            if membre.NoMembre == no_membre:
                return membre

    def _set_phone(self, membre, value):
        # Manage phone
        # result 22, 25, 28 is type
        # Type: 1 choose (empty)
        # Type: 2 domicile Phone
        # Type: 3 Travail À SUPPORTÉ
        # Type: 4 Cellulaire MOBILE
        # Type: 5 Téléavertisseur (pagette) NON SUPPORTÉ

        # Pagette
        if membre.NoTypeTel1 == 5 or membre.NoTypeTel2 == 5 or membre.NoTypeTel3 == 5:
            print("WARNING, le pagette n'est pas supporté.")

        # Travail
        if membre.NoTypeTel1 == 3 or membre.NoTypeTel2 == 3 or membre.NoTypeTel3 == 3:
            print("WARNING, le téléphone travail n'est pas supporté.")

        # MOBILE
        has_mobile = False
        if membre.NoTypeTel1 == 4 and membre.Telephone1 and membre.Telephone1.strip():
            has_mobile = True
            value['mobile'] = membre.Telephone1.strip()
            if membre.PosteTel1 and membre.PosteTel1.strip():
                print("WARNING, le numéro de poste du mobile n'est pas supporté.")
        if membre.NoTypeTel2 == 4 and membre.Telephone2 and membre.Telephone2.strip():
            if has_mobile:
                print("WARNING, duplicat du cellulaire.")
            else:
                has_mobile = True
                value['mobile'] = membre.Telephone2.strip()
                if membre.PosteTel2 and membre.PosteTel2.strip():
                    print("WARNING, le numéro de poste du mobile n'est pas supporté.")
        if membre.NoTypeTel3 == 4 and membre.Telephone3 and membre.Telephone3.strip():
            if has_mobile:
                print("WARNING, duplicat du cellulaire.")
            else:
                has_mobile = True
                value['mobile'] = membre.Telephone3.strip()
                if membre.PosteTel3 and membre.PosteTel3.strip():
                    print("WARNING, le numéro de poste du mobile n'est pas supporté.")

        has_domicile = False
        if membre.NoTypeTel1 == 2 and membre.Telephone1 and membre.Telephone1.strip():
            has_domicile = True
            value['phone'] = membre.Telephone1.strip()
            if membre.PosteTel1 and membre.PosteTel1 and membre.PosteTel1.strip():
                print("WARNING, le numéro de poste du domicile n'est pas supporté.")
        if membre.NoTypeTel2 == 2 and membre.Telephone2 and membre.Telephone2.strip():
            if has_domicile:
                print("WARNING, duplicat du cellulaire.")
            else:
                has_domicile = True
                value['phone'] = membre.Telephone2.strip()
                if membre.PosteTel2 and membre.PosteTel2.strip():
                    print("WARNING, le numéro de poste du domicile n'est pas supporté.")
        if membre.NoTypeTel3 == 2 and membre.Telephone3 and membre.Telephone3.strip():
            if has_domicile:
                print("WARNING, duplicat du cellulaire.")
            else:
                has_domicile = True
                value['phone'] = membre.Telephone3.strip()
                if membre.PosteTel3 and membre.PosteTel3.strip():
                    print("WARNING, le numéro de poste du domicile n'est pas supporté.")

    def _check_duplicate(self, tbl_membre, key, verbose=True):
        # Ignore duplicate since enable multi-company with different contact, not sharing
        # Debug duplicate data, need unique name
        dct_debug = collections.defaultdict(list)
        for result in tbl_membre:
            dct_debug[result.__dict__.get(key)].append(result)
        lst_to_remove = []
        for key, value in dct_debug.items():
            if len(value) > 1:
                if verbose:
                    print(f"Duplicate name ({len(value)}) {key}: {value}\n")
            else:
                lst_to_remove.append(key)
        for key in lst_to_remove:
            del dct_debug[key]
        return dct_debug

    def setup_configuration(self, dry_run=False):
        print("Setup configuration")

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})
            # CRM
            # team = env['crm.team'].browse(1)
            # Team name Europe need to be change in i18n french canadian
            # team.name = "Québec"

            # General configuration
            values = {
                # 'use_quotation_validity_days': True,
                # 'quotation_validity_days': 30,
                # 'portal_confirmation_sign': True,
                # 'portal_invoice_confirmation_sign': True,
                # 'group_sale_delivery_address': True,
                # 'group_sale_order_template': True,
                # 'default_sale_order_template_id': True,
                # 'use_sale_note': True,
                # 'sale_note': "N° TPS : \n"
                #              "N° TVQ : \n"
                #              "N° RBQ : 5775-6991-01\n"
                #              "N° BSP : SC 20047464\n"
                #              "Des frais de 2% par mois sont exigés sur tout solde impayé"
                #              " après la date d'échéance.",
                # 'refund_total_tip_amount_included_to_employee': True,
                # 'group_discount_per_so_line': True,
                # 'group_use_lead': True,
                # 'generate_lead_from_alias': True,
                # 'crm_alias_prefix': "service",
                'theme_color_brand': "#004a98",
                # 'theme_color_primary': "#2CD5C4",
                'theme_background_image': env.ref("accorderie_migrate_mysql.theme_background_image").datas,
                # 'branding_color_text': "#4c4c4c",

                # Enable multi company for each accorderie
                'group_multi_company': True,
                'company_share_partner': False,
                'company_share_product': False,

                # Ignore KPI digest
                'digest_emails': False,

                # Authentication
                'auth_signup_reset_password': True,

                # Commercial
                # TODO Cause bug when uninstall, need to do it manually
                # 'module_web_unsplash': False,
                # 'module_partner_autocomplete': False,

            }
            if not dry_run:
                event_config = env['res.config.settings'].sudo().create(values)
                event_config.execute()

    def update_user(self, dry_run=False):
        print("Update user preference")
        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})

            administrator = env['res.users'].browse(2)
            # administrator.email = "admin@nuagelibre.ca"
            # Add all society to administrator
            administrator.company_ids = env['res.company'].search([]).ids

    def migrate_company(self, dry_run=False):
        print("Migrate company")
        # tbl_accorderie + tbl_pointservice

        head_quarter = None
        lst_child_company = []
        is_updated = False

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})

            if not self.dct_accorderie:
                is_updated = True
                # Accorderie
                i = 0
                for accorderie in self.dct_tbl.tbl_accorderie:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_accorderie)}"

                    if accorderie.Nom == "Réseau Accorderie (du Qc)":
                        # Update main company
                        name = accorderie.Nom.strip()
                        head_quarter = env['res.company'].browse(1)
                        head_quarter.name = name
                        head_quarter.street = accorderie.AdresseAccorderie.strip()
                        head_quarter.zip = accorderie.CodePostalAccorderie.strip()
                        head_quarter.phone = accorderie.TelAccorderie.strip()
                        head_quarter.partner_id.fax = accorderie.TelecopieurAccorderie.strip()
                        head_quarter.email = accorderie.CourrielAccorderie.strip()
                        head_quarter.website = "www.accorderie.ca"
                        head_quarter.state_id = 543  # Quebec
                        head_quarter.country_id = 38  # Canada
                        head_quarter.tz = "America/Montreal"
                        head_quarter.create_date = accorderie.DateMAJ_Accorderie

                        # City
                        ville = self._get_ville(accorderie.NoVille)
                        head_quarter.city = ville.Ville

                        if accorderie.URL_LogoAccorderie:
                            data = open(f"{self.logo_path}/{accorderie.URL_LogoAccorderie}", "rb").read()
                            head_quarter.logo = base64.b64encode(data)
                        else:
                            # obj.logo = base64.b64encode(env.ref("accorderie_migrate_mysql.logo_blanc_accorderie").datas),
                            _path = os.path.dirname(__file__)
                            data = open(f"{_path}/static/img/logonoiblancaccorderie.jpg", "rb").read()
                            head_quarter.logo = base64.b64encode(data)
                        obj = head_quarter
                    else:
                        name = f"Accorderie {accorderie.Nom.strip()}"
                        ville = self._get_ville(accorderie.NoVille)
                        value = {
                            'name': name,
                            'city': ville.Ville,
                            'street': accorderie.AdresseAccorderie.strip(),
                            'zip': accorderie.CodePostalAccorderie.strip(),
                            'phone': accorderie.TelAccorderie.strip(),
                            'email': accorderie.CourrielAccorderie.strip(),
                            'state_id': 543,  # Quebec
                            'country_id': 38,  # Canada
                            'create_date': accorderie.DateMAJ_Accorderie,
                            'background_image': env.ref("accorderie_migrate_mysql.theme_background_image").datas,
                            # 'website': result[14].strip(),
                        }

                        if accorderie.URL_LogoAccorderie:
                            data = open(f"{self.logo_path}/{accorderie.URL_LogoAccorderie}", "rb").read()
                            value["logo"] = base64.b64encode(data)

                        obj = env['res.company'].create(value)
                        lst_child_company.append(obj)
                        obj.tz = "America/Montreal"
                        obj.partner_id.active = accorderie.NonVisible == 0
                        obj.partner_id.fax = accorderie.TelecopieurAccorderie.strip()
                        obj.partner_id.customer = False
                        obj.partner_id.supplier = False

                    self.dct_accorderie[accorderie.NoAccorderie] = obj
                    # self.dct_accorderie_by_email[obj.email] = obj
                    print(f"{pos_id} - res.company - tbl_accorderie - ADDED '{name}' id {accorderie.NoAccorderie}")

                if head_quarter:
                    for child in lst_child_company:
                        child.parent_id = head_quarter.id

            # Point Service
            if not self.dct_pointservice:
                is_updated = True
                i = 0
                for pointservice in self.dct_tbl.tbl_pointservice:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_pointservice)}"

                    tbl_membre = self._get_membre(pointservice.NoMembre)
                    name = f"Point de service {pointservice.NomPointService.strip()}"
                    accorderie_obj = self.dct_accorderie.get(pointservice.NoAccorderie)

                    # TODO missing Telephone2 if exist, tpl_result[23]
                    value = {
                        'name': name,
                        'email': tbl_membre.Courriel.strip(),
                        'street': tbl_membre.Adresse.strip(),
                        'zip': tbl_membre.CodePostal.strip(),
                        'phone': tbl_membre.Telephone1,
                        'state_id': 543,  # Quebec
                        'country_id': 38,  # Canada
                        'create_date': pointservice.DateMAJ_PointService,
                        'parent_id': accorderie_obj.id,
                        'background_image': env.ref("accorderie_migrate_mysql.theme_background_image").datas,
                        # 'website': result[14].strip(),
                    }

                    obj = env['res.company'].create(value)
                    obj.tz = "America/Montreal"
                    obj.partner_id.active = tbl_membre.MembreActif == -1
                    obj.partner_id.customer = False
                    obj.partner_id.supplier = False
                    # obj.partner_id.fax = accorderie.TelecopieurAccorderie.strip()
                    print(f"{pos_id} - res.company - tbl_pointservice - "
                          f"ADDED '{name}' id {pointservice.NoPointService}")
                    # accorderie_email_obj = self.dct_accorderie_by_email.get(tbl_membre.Courriel.strip())
                    # name = f"Point de service {pointservice.NomPointService.strip()}"
                    # if not accorderie_email_obj:
                    #     accorderie_obj = self.dct_accorderie.get(pointservice.NoAccorderie)
                    #
                    #     # TODO missing Telephone2 if exist, tpl_result[23]
                    #     value = {
                    #         'name': name,
                    #         'email': tbl_membre.Courriel.strip(),
                    #         'street': tbl_membre.Adresse.strip(),
                    #         'zip': tbl_membre.CodePostal.strip(),
                    #         'phone': tbl_membre.Telephone1,
                    #         'state_id': 543,  # Quebec
                    #         'country_id': 38,  # Canada
                    #         'create_date': pointservice.DateMAJ_PointService,
                    #         'parent_id': accorderie_obj.id,
                    #         # 'website': result[14].strip(),
                    #     }
                    #
                    #     obj = env['res.company'].create(value)
                    #     obj.tz = "America/Montreal"
                    #     obj.partner_id.active = tbl_membre.MembreActif == -1
                    #     obj.partner_id.customer = False
                    #     obj.partner_id.supplier = False
                    #     # obj.partner_id.fax = accorderie.TelecopieurAccorderie.strip()
                    #     print(f"{pos_id} - res.company - tbl_pointservice - "
                    #           f"ADDED '{name}' id {pointservice.NoPointService}")
                    # else:
                    #     obj = accorderie_email_obj
                    #     print(f"{pos_id} - res.company - tbl_pointservice - "
                    #           f"DUPLICATED '{name}' id {pointservice.NoPointService} "
                    #           f"obj_id {obj.id}")
                    self.dct_pointservice[pointservice.NoPointService] = obj

        if is_updated:
            self._update_cache_obj()

    def migrate_muk_dms(self):
        """
        Depend on company.
        :return:
        """
        print("Migrate files")
        # tbl_type_fichier and tbl_fichier

        if not self.dct_fichier:
            # Setup type fichier
            dct_type_fichier = {}
            with api.Environment.manage():
                env = api.Environment(self.cr, SUPERUSER_ID, {})

                i = 0
                for fichier in self.dct_tbl.tbl_type_fichier:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_type_fichier)}"
                    name = fichier.TypeFichier
                    value = {
                        'name': name,
                        'create_date': fichier.DateMAJ_TypeFichier,
                    }

                    category_id = env['muk_dms.category'].create(value)
                    dct_type_fichier[fichier.Id_TypeFichier] = category_id
                    print(f"{pos_id} - muk_dms.category - tbl_type_fichier - ADDED '{name}' "
                          f"id {fichier.Id_TypeFichier}")

                # Setup directory
                dct_storage = {}
                i = 0

                # for accorderie in list(self.dct_pointservice.values()) + list(self.dct_accorderie.values()):
                for accorderie in list(self.dct_accorderie.values()):
                    i += 1
                    pos_id = f"{i}/{len(self.dct_accorderie.values())}"
                    name = accorderie.name

                    value = {
                        'name': name,
                        'company': accorderie.id,
                    }

                    storage_id = env["muk_dms.storage"].create(value)

                    if "/" in name:
                        name = name.replace("/", "_")
                    value = {
                        'name': name,
                        'root_storage': storage_id.id,
                        'is_root_directory': True,
                    }

                    directory_id = env["muk_dms.directory"].create(value)
                    if accorderie.id in dct_storage:
                        raise Exception(f"Duplicate {accorderie} : {dct_storage}")

                    dct_storage[accorderie.id] = directory_id
                    print(f"{pos_id} - muk_dms.storage - tbl_accorderie - "
                          f"ADDED '{name}' id {storage_id.id if storage_id else ''}")

                i = 0
                for fichier in self.dct_tbl.tbl_fichier:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_fichier)}"

                    name = fichier.NomFichierOriginal

                    data = open(f"{FILE_PATH}/{fichier.NomFichierStokage}", "rb").read()
                    content = base64.b64encode(data)

                    # _, directory_id = self._get_storage(id_accorderie=result[2])

                    # type_fichier_id, _ = self._get_type_fichier(id_type_fichier=result[1])

                    category = dct_type_fichier.get(fichier.Id_TypeFichier).id

                    value = {
                        'name': name,
                        'category': category,
                        'active': fichier.Si_Disponible == 1,
                        'directory': dct_storage[self.dct_accorderie.get(fichier.NoAccorderie).id].id,
                        'content': content,
                        'create_date': fichier.DateMAJ_Fichier,
                    }

                    try:
                        file_id = env['muk_dms.file'].create(value)
                    except Exception as e:
                        continue
                    # Validate not duplicate
                    # files_id = env['muk_dms.file'].search([('name', '=', name), ('directory', '=', directory_id.id)])
                    # if not files_id:
                    #     file_id = env['muk_dms.file'].create(value)
                    # else:
                    #     if len(files_id) > 1:
                    #         raise Exception(f"ERROR, duplicate file id {i}")
                    #     if files_id[0].content == content:
                    #         print(f"{pos_id} - muk_dms.file - tbl_fichier - SKIPPED DUPLICATED SAME CONTENT '{name}' "
                    #               f"on storage '{directory_id.name}' id {fichier.Id_Fichier}")
                    #     else:
                    #         raise Exception(
                    #             f"ERROR, duplicate file id {i}, content is different, but same name '{name}'")

                    self.dct_fichier[fichier.Id_Fichier] = file_id
                    print(f"{pos_id} - muk_dms.file - tbl_fichier - ADDED '{name}' "
                          f"on storage '{directory_id.name if directory_id else ''}' id {fichier.Id_Fichier}")
            self._update_cache_obj()

    def migrate_product(self):
        """
        :return:
        """
        print("Migrate products")
        # tbl_titre, tbl_produit

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})
            if not self.dct_produit:
                dct_titre = {}

                product_cat_root_id = env['product.category'].create({'name': 'Aliment'})

                i = 0
                for titre in self.dct_tbl.tbl_titre:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_titre)}"
                    name = titre.Titre
                    value = {
                        'name': name,
                        'parent_id': product_cat_root_id.id,
                        'create_date': titre.DateMAJ_Titre,
                    }

                    product_cat_id = env['product.category'].create(value)
                    dct_titre[titre.NoTitre] = product_cat_id
                    print(f"{pos_id} - product.category - tbl_titre - ADDED '{name}' id {titre.NoTitre}")

                dct_produit = {}
                i = 0
                for produit in self.dct_tbl.tbl_produit:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_produit)}"
                    titre_id = dct_titre.get(produit.NoTitre)
                    accorderie_obj = self.dct_accorderie.get(produit.NoAccorderie)
                    name = produit.NomProduit
                    value = {
                        'name': name,
                        'categ_id': titre_id.id,
                        'active': produit.Visible_Produit == 1,
                        'company_id': accorderie_obj.id,
                        'create_date': produit.DateMAJ_Produit,
                    }

                    product_id = env['product.template'].create(value)
                    dct_produit[produit.NoProduit] = product_id
                    print(f"{pos_id} - product.category - tbl_produit - ADDED '{name}' id {produit.NoProduit}")

                self.dct_produit = dct_produit
                self._update_cache_obj()

    def migrate_member(self):
        """
        :return:
        """
        print("Migrate member")
        # tbl_membre

        dct_debug_login = self._check_duplicate(self.dct_tbl.tbl_membre, "NomUtilisateur", verbose=False)
        dct_debug_email = self._check_duplicate(self.dct_tbl.tbl_membre, "Courriel", verbose=False)
        # self.dct_tbl["tbl_membre|conflict"] = dct_debug
        # print("profile")
        # print(dct_debug_login)
        # print("email")
        # print(dct_debug_email)

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})
            if not self.dct_membre:
                dct_membre = {}

                i = 0
                for membre in self.dct_tbl.tbl_membre:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_membre)}"

                    login = membre.NomUtilisateur
                    # Get the name in 1 field
                    if membre.Prenom and membre.Nom:
                        name = f"{membre.Prenom.strip()} {membre.Nom.strip()}"
                    elif membre.Prenom:
                        name = f"{membre.Prenom.strip()}"
                    elif membre.Nom:
                        name = f"{membre.Nom.strip()}"
                    else:
                        name = ""

                    if not login or not name:
                        print(f"{pos_id} - res.partner - tbl_membre - SKIPPED EMPTY LOGIN '{name}' "
                              f"id {membre.NoMembre}")
                        # lst_result .append((None, result))
                        continue

                    # Ignore test user
                    if ("test" in name or "test" in login) and login not in ["claudettestlaur"]:
                        print(f"{pos_id} - res.partner - tbl_membre - SKIPPED TEST LOGIN "
                              f"name '{name}' login '{login}' id {membre.NoMembre}")
                        continue

                    email = membre.Courriel.strip()
                    if not email:
                        if login in dct_debug_login.keys():
                            # TODO Need to merge it
                            print(f"{pos_id} - res.partner - tbl_membre - SKIPPED DUPLICATED LOGIN "
                                  f"name '{name}' login '{login}' email '{email}' id {membre.NoMembre}")
                            continue
                        # Need an email for login, force create it
                        # TODO coder un séquenceur dans Odoo pour la création de courriel générique
                        # email = GENERIC_EMAIL % i
                        email = GENERIC_EMAIL % login
                    elif email in dct_debug_email.keys():
                        # TODO merge user
                        print(f"{pos_id} - res.partner - tbl_membre - SKIPPED DUPLICATED EMAIL "
                              f"name '{name}' login '{login}' email '{email}' id {membre.NoMembre}")
                        continue

                    # Show duplicate profile
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_login.items())[:15] for a in va[1] if a[37] == -1])
                    # Show duplicate email
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1]])
                    # Show duplicate not empty email
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[29].strip() != ""])
                    # Show duplicate not empty email actif
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[29].strip() != "" and a[37] == -1])
                    # Show duplicate email active user
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[37] == -1])
                    # duplicate email and duplicate user and active
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[37] == -1 and a[44] in dct_debug_login])

                    # Technique remplacé par l'utilisation du courriel
                    # if login in dct_debug_login.keys():
                    #     # Validate unique email
                    #     print(f"{pos_id} - res.partner - tbl_membre - SKIPPED DUPLICATED "
                    #           f"name '{name}' login '{login}' id {result[0]}")
                    #
                    #     if email in dct_debug_email:
                    #         print(dct_debug_email[email])
                    #     continue

                    company_id = self.dct_accorderie.get(membre.NoAccorderie)
                    city_name = self._get_ville(membre.NoVille)

                    value = {
                        'name': name,
                        'street': membre.Adresse.strip(),
                        'zip': membre.CodePostal.strip(),
                        'email': email,
                        'supplier': False,
                        'customer': True,
                        'state_id': 543,  # Quebec
                        'country_id': 38,  # Canada
                        'tz': "America/Montreal",
                        'active': membre.MembreActif == 0,
                        'company_id': company_id.id,
                        'create_date': membre.Date_MAJ_Membre,
                        'free_member': True,
                    }

                    if membre.Memo:
                        value['comment'] = membre.Memo.strip()

                    if city_name:
                        value['city'] = city_name

                    self._set_phone(membre, value)

                    obj_partner = env['res.partner'].create(value)

                    value = {
                        'name': name,
                        'active': membre.MembreActif == 0,
                        'login': email,
                        'password': membre.MotDePasseRaw,
                        'email': email,
                        'groups_id': [(4, env.ref('base.group_user').id)],
                        'company_id': company_id.id,
                        'company_ids': [(4, company_id.id)],
                        'partner_id': obj_partner.id,
                    }

                    obj_user = env['res.users'].with_context({'no_reset_password': True}).create(value)

                    dct_membre[membre.NoMembre] = obj_user
                    print(f"{pos_id} - res.users - tbl_membre - ADDED '{name}' login '{login}' email '{email}' "
                          f"id {membre.NoMembre}")

                self.dct_membre = dct_membre
                self._update_cache_obj()


class MigrationAccorderieCopy:
    def __init__(self, cr):
        print("Start migration of Accorderie of Quebec.")
        assert MySQLdb
        self.host = "localhost"
        self.user = "accorderie"
        self.passwd = "accorderie"
        self.db_name = "accorderie_log_2019_2"
        self.conn = MySQLdb.connect(host=self.host, user=self.user, passwd=self.passwd, db=self.db_name)
        # Path of the backup
        self.source_code_path = BACKUP_PATH
        self.logo_path = f"{self.source_code_path}/images/logo"
        self.cr = cr

        self.dct_tbl = {}

    def migrate_tbl_fournisseur(self, dry_run=False):
        print("Begin migrate tbl_fournisseur")
        cur = self.conn.cursor()
        # Get all fournisseur
        str_query = f"""SELECT * FROM tbl_fournisseur;"""
        cur.nextset()
        cur.execute(str_query)
        tpl_result = cur.fetchall()

        self.dct_tbl["tbl_fournisseur"] = tpl_result

        # Ignore duplicate since enable multi-company with different contact, not sharing
        # Debug duplicate data, need unique name
        # dct_debug = collections.defaultdict(list)
        # for result in tpl_result:
        #     dct_debug[result[4]].append(result)
        # lst_to_remove = []
        # for key, value in dct_debug.items():
        #     if len(value) > 1:
        #         print(f"Duplicate name ({len(value)}) {key}: {value}\n")
        #     else:
        #         lst_to_remove.append(key)
        # for key in lst_to_remove:
        #     del dct_debug[key]
        #
        # self.dct_tbl["tbl_fournisseur|conflict"] = dct_debug

        # 0 `NoFournisseur` int(10) UNSIGNED NOT NULL,
        # 1 `NoAccorderie` int(10) UNSIGNED NOT NULL,
        # 2 `NoRegion` int(10) UNSIGNED NOT NULL,
        # 3 `NoVille` int(10) UNSIGNED NOT NULL,
        # 4 `NomFournisseur` varchar(80) CHARACTER SET latin1 DEFAULT NULL,
        # 5 `Adresse` varchar(80) CHARACTER SET latin1 DEFAULT NULL,
        # 6 `CodePostalFournisseur` varchar(7) CHARACTER SET latin1 DEFAULT NULL,
        # 7 `TelFournisseur` varchar(14) CHARACTER SET latin1 DEFAULT NULL,
        # 8 `FaxFounisseur` varchar(40) CHARACTER SET latin1 DEFAULT NULL,
        # 9 `CourrielFournisseur` varchar(255) CHARACTER SET latin1 DEFAULT NULL,
        # 10 `NomContact` varchar(100) CHARACTER SET latin1 DEFAULT NULL,
        # 11 `PosteContact` varchar(8) CHARACTER SET latin1 DEFAULT NULL,
        # 12 `CourrielContact` varchar(255) CHARACTER SET latin1 DEFAULT NULL,
        # 13 `NoteFournisseur` text CHARACTER SET latin1,
        # 14 `Visible_Fournisseur` tinyint(1) UNSIGNED DEFAULT '1',
        # 15 `DateMAJ_Fournisseur` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})

            i = 0
            for result in tpl_result:
                i += 1
                pos_id = f"{i}/{len(tpl_result)}"

                if DEBUG_LIMIT and i >= LIMIT:
                    print(f"REACH LIMIT {LIMIT}")
                    break

                name = result[4].strip()
                if not dry_run:
                    if "Accorderie" in name:
                        accorderie_id, _ = self._get_accorderie(result[1])
                        if not accorderie_id:
                            raise Exception(f"Cannot find associated accorderie {result}")
                        accorderie_id.partner_id.supplier = True
                        new_comment = ""
                        if accorderie_id.partner_id.comment:
                            new_comment = f"{accorderie_id.partner_id.comment}\n"
                        accorderie_id.partner_id.comment = f"{new_comment}Fournisseur : {result[13].strip()}"
                        accorderie_id.create_date = result[15]

                        print(f"{pos_id} - res.partner - tbl_fournisseur - "
                              f"UPDATED '{name}/{accorderie_id.partner_id.name}' id {result[0]}")
                        continue
                    # elif name in dct_debug.keys():
                    #     lst_duplicated = dct_debug.get(name)
                    #     print(f"{pos_id} - res.partner - tbl_fournisseur - SKIPPED '{name}' id {result[0]}")
                    #     continue

                    company_id, _ = self._get_accorderie(id_accorderie=result[1])
                    if not company_id:
                        raise Exception(f"Cannot find associated accorderie {result}")

                    city_name = self._get_ville(result[3])

                    value = {
                        'name': name,
                        'street': result[5].strip(),
                        'zip': result[6].strip(),
                        'phone': result[7].strip(),
                        'fax': result[8].strip(),
                        'email': result[9].strip(),
                        'supplier': True,
                        'customer': False,
                        'state_id': 543,  # Quebec
                        'country_id': 38,  # Canada
                        'company_type': 'company',
                        'comment': result[13].strip(),
                        'tz': "America/Montreal",
                        'active': result[14] == 1,
                        'company_id': company_id.id,
                        'create_date': result[15],
                    }

                    if city_name:
                        value['city'] = city_name

                    obj = env['res.partner'].create(value)

                    value_contact = {
                        'name': result[10].strip(),
                        'function': result[11].strip(),
                        'email': result[12].strip(),
                        'parent_id': obj.id,
                        'company_id': company_id.id,
                        'create_date': result[15],
                    }

                    obj_contact = env['res.partner'].create(value_contact)

                print(f"{pos_id} - res.partner - tbl_fournisseur - ADDED '{name}' id {result[0]}")

    def migrate_tbl_membre(self, dry_run=False):
        print("Begin migrate tbl_membre")
        cur = self.conn.cursor()
        str_query = f"""SELECT *,DECODE(MotDePasse,'{SECRET_PASSWORD}') AS MotDePasse FROM tbl_membre;"""
        cur.nextset()
        cur.execute(str_query)
        tpl_result = cur.fetchall()

        lst_result = []
        self.dct_tbl["tbl_membre"] = lst_result

        dct_debug_login = self._check_duplicate(tpl_result, 44, verbose=False)
        dct_debug_email = self._check_duplicate(tpl_result, 29, verbose=False)
        # self.dct_tbl["tbl_membre|conflict"] = dct_debug
        # print("profile")
        # print(dct_debug_login)
        # print("email")
        # print(dct_debug_email)

        # 0 `NoMembre` int(10) UNSIGNED NOT NULL,
        # 1 `NoCartier` int(10) UNSIGNED DEFAULT '0',
        # 2 `NoAccorderie` int(10) UNSIGNED NOT NULL,
        # 3 `NoPointService` int(10) UNSIGNED DEFAULT NULL,
        # 4 `NoTypeCommunication` int(10) UNSIGNED NOT NULL,
        # 5 `NoOccupation` int(10) UNSIGNED NOT NULL,
        # 6 `NoOrigine` int(10) UNSIGNED NOT NULL,
        # 7 `NoSituationMaison` int(10) UNSIGNED NOT NULL,
        # 8 `NoProvenance` int(10) UNSIGNED NOT NULL,
        # 9 `NoRevenuFamilial` int(10) UNSIGNED NOT NULL,
        # 10 `NoArrondissement` int(10) UNSIGNED DEFAULT NULL,
        # 11 `NoVille` int(10) UNSIGNED NOT NULL,
        # 12 `NoRegion` int(10) UNSIGNED NOT NULL,
        # 13 `MembreCA` tinyint(4) DEFAULT '0',
        # 14 `PartSocialPaye` tinyint(4) DEFAULT '0',
        # 15 `CodePostal` varchar(7) DEFAULT NULL,
        # 16 `DateAdhesion` date DEFAULT NULL,
        # 17 `Nom` varchar(45) DEFAULT NULL,
        # 18 `Prenom` varchar(45) DEFAULT NULL,
        # 19 `Adresse` varchar(255) DEFAULT NULL,
        # 20 `Telephone1` varchar(10) DEFAULT NULL,
        # 21 `PosteTel1` varchar(10) DEFAULT NULL,
        # 22 `NoTypeTel1` int(10) UNSIGNED DEFAULT NULL,
        # 23 `Telephone2` varchar(10) DEFAULT NULL,
        # 24 `PosteTel2` varchar(10) DEFAULT NULL,
        # 25 `NoTypeTel2` int(10) UNSIGNED DEFAULT NULL,
        # 26 `Telephone3` varchar(10) DEFAULT NULL,
        # 27 `PosteTel3` varchar(10) DEFAULT NULL,
        # 28 `NoTypeTel3` int(10) UNSIGNED DEFAULT NULL,
        # 29 `Courriel` varchar(255) DEFAULT NULL,
        # 30 `AchatRegrouper` tinyint(1) DEFAULT NULL,
        # 31 `PretActif` tinyint(1) DEFAULT NULL,
        # 32 `PretRadier` tinyint(1) DEFAULT NULL,
        # 33 `PretPayer` tinyint(1) DEFAULT NULL,
        # 34 `EtatCompteCourriel` tinyint(1) DEFAULT NULL,
        # 35 `BottinTel` tinyint(1) DEFAULT NULL,
        # 36 `BottinCourriel` tinyint(1) DEFAULT NULL,
        # 37 `MembreActif` tinyint(1) DEFAULT '-1',
        # 38 `MembreConjoint` tinyint(1) DEFAULT NULL,
        # 39 `NoMembreConjoint` int(10) UNSIGNED DEFAULT NULL,
        # 40 `Memo` text,
        # 41 `Sexe` tinyint(1) DEFAULT NULL,
        # 42 `AnneeNaissance` int(4) DEFAULT NULL,
        # 43 `PrecisezOrigine` varchar(45) DEFAULT NULL,
        # 44 `NomUtilisateur` varchar(15) DEFAULT NULL,
        # 45 `MotDePasse` varchar(15) DEFAULT NULL,
        # 46 `ProfilApprouver` tinyint(1) DEFAULT '-1',
        # 47 `MembrePrinc` tinyint(1) DEFAULT NULL,
        # 48 `NomAccorderie` varchar(90) DEFAULT NULL,
        # 49 `RecevoirCourrielGRP` tinyint(1) DEFAULT NULL,
        # 50 `PasCommunication` tinyint(1) DEFAULT NULL,
        # 51 `DescriptionAccordeur` varchar(255) DEFAULT NULL,
        # 52 `Date_MAJ_Membre` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        # 53 `TransfereDe` int(10) DEFAULT NULL
        # 54 PASSWORD

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})

            i = 0
            for result in tpl_result:
                i += 1
                pos_id = f"{i}/{len(tpl_result)}"

                if DEBUG_LIMIT and i >= LIMIT:
                    print(f"REACH LIMIT {LIMIT}")
                    break
                obj_user = None
                if not dry_run:
                    login = result[44]

                    # Get the name in 1 field
                    if result[18] and result[17]:
                        name = f"{result[18].strip()} {result[17].strip()}"
                    elif result[18]:
                        name = f"{result[18].strip()}"
                    elif result[17]:
                        name = f"{result[17].strip()}"
                    else:
                        name = ""

                    if not login or not name:
                        print(f"{pos_id} - res.partner - tbl_membre - SKIPPED EMPTY LOGIN '{name}' id {result[0]}")
                        lst_result.append((None, result))
                        continue

                    # Ignore test user
                    if "test" in name or "test" in login:
                        print(f"{pos_id} - res.partner - tbl_membre - SKIPPED TEST LOGIN "
                              f"name '{name}' login '{login}' id {result[0]}")
                        continue

                    email = result[29].strip()
                    if not email:
                        if login in dct_debug_login.keys():
                            # TODO Need to merge it
                            print(f"{pos_id} - res.partner - tbl_membre - SKIPPED DUPPLICATED LOGIN "
                                  f"name '{name}' login '{login}' email '{email}' id {result[0]}")
                            continue
                        # Need an email for login, force create it
                        # TODO coder un séquenceur dans Odoo pour la création de courriel générique
                        # email = GENERIC_EMAIL % i
                        email = GENERIC_EMAIL % login
                    elif email in dct_debug_email.keys():
                        # TODO merge user
                        print(f"{pos_id} - res.partner - tbl_membre - SKIPPED DUPLICATED EMAIL "
                              f"name '{name}' login '{login}' email '{email}' id {result[0]}")
                        continue

                    # Show duplicate profile
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_login.items())[:15] for a in va[1] if a[37] == -1])
                    # Show duplicate email
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1]])
                    # Show duplicate not empty email
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[29].strip() != ""])
                    # Show duplicate not empty email actif
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[29].strip() != "" and a[37] == -1])
                    # Show duplicate email active user
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[37] == -1])
                    # duplicate email and duplicate user and active
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[37] == -1 and a[44] in dct_debug_login])

                    # Technique remplacé par l'utilisation du courriel
                    # if login in dct_debug_login.keys():
                    #     # Validate unique email
                    #     print(f"{pos_id} - res.partner - tbl_membre - SKIPPED DUPLICATED "
                    #           f"name '{name}' login '{login}' id {result[0]}")
                    #
                    #     if email in dct_debug_email:
                    #         print(dct_debug_email[email])
                    #     continue

                    company_id, _ = self._get_accorderie(id_accorderie=result[2])
                    if not company_id:
                        raise Exception(f"Cannot find associated accorderie {result}")

                    city_name = self._get_ville(result[11])

                    # TODO ajouter l'ancien login en description
                    value = {
                        'name': name,
                        'street': result[19].strip(),
                        'zip': result[15].strip(),
                        'email': email,
                        'supplier': False,
                        'customer': True,
                        'state_id': 543,  # Quebec
                        'country_id': 38,  # Canada
                        'tz': "America/Montreal",
                        'active': result[37] == 0,
                        'company_id': company_id.id,
                        'create_date': result[52],
                    }

                    if result[40]:
                        value['comment'] = result[40].strip()

                    if city_name:
                        value['city'] = city_name

                    self._set_phone(result, value)

                    obj_partner = env['res.partner'].create(value)

                    value = {
                        'name': name,
                        'active': result[37] == 0,
                        'login': email,
                        'password': result[54],
                        'email': email,
                        'groups_id': [(4, env.ref('base.group_user').id)],
                        'company_id': company_id.id,
                        'company_ids': [(4, company_id.id)],
                        'partner_id': obj_partner.id,
                        'free_member': True,
                    }

                    obj_user = env['res.users'].with_context({'no_reset_password': True}).create(value)
                else:
                    name = ""
                lst_result.append((obj_user, result))
                print(f"{pos_id} - res.partner - tbl_membre - ADDED '{name}' id {result[0]}")

    def migrate_tbl_pointservice(self, dry_run=False):
        print("Begin migrate tbl_pointservice")
        cur = self.conn.cursor()
        str_query = f"""SELECT * FROM tbl_pointservice;"""
        cur.nextset()
        cur.execute(str_query)
        tpl_result = cur.fetchall()

        lst_result = []
        self.dct_tbl["tbl_pointservice"] = lst_result

        # 0 `NoPointService` int(10) UNSIGNED NOT NULL,
        # 1 `NoAccorderie` int(10) UNSIGNED NOT NULL,
        # 2 `NoMembre` int(10) UNSIGNED DEFAULT NULL,
        # 3 `NomPointService` varchar(255) CHARACTER SET latin1 DEFAULT NULL,
        # 4 `OrdrePointService` tinyint(3) UNSIGNED DEFAULT '0',
        # 5 `NoteGrpAchatPageClient` text COLLATE latin1_general_ci,
        # 6 `DateMAJ_PointService` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})
            i = 0
            for result in tpl_result:
                i += 1
                pos_id = f"{i}/{len(tpl_result)}"

                if DEBUG_LIMIT and i >= LIMIT:
                    print(f"REACH LIMIT {LIMIT}")
                    break

                if not dry_run:
                    company_id, _ = self._get_accorderie(id_accorderie=result[1])
                    member_id, tpl_member = self._get_member(id_member=result[2])
                    if not (not member_id and tpl_member):
                        print("Error, member not suppose to be create.")
                        continue

                    email = tpl_member[29].strip()

                    # TODO missing Telephone2 if exist, tpl_result[23]
                    name = f"Point de service {result[3].strip()}"
                    value = {
                        'name': name,
                        'email': email,
                        'street': tpl_member[19].strip(),
                        'zip': tpl_member[15].strip(),
                        'customer': False,
                        'supplier': False,
                        'phone': tpl_member[20],
                        'state_id': 543,  # Quebec
                        'country_id': 38,  # Canada
                        'create_date': result[6],
                        'parent_id': company_id.id,
                        # 'website': result[14].strip(),
                    }

                    # City
                    city_name = self._get_ville(tpl_member[11])
                    if city_name:
                        value["city"] = city_name

                    obj = env['res.company'].create(value)
                    obj.tz = "America/Montreal"

                    # TODO set res.partner update member with self._set_member(id_member=result[2], member)

                    # if member_id:
                    #     member_id.parent_id = obj.partner_id.id
                    # else:
                    #     print(f"ERROR, missing member id {result[2]}.")
                else:
                    obj = None

                print(f"{pos_id} - res.company - tbl_pointservice - ADDED '{name}' id {result[0]}")
                lst_result.append((obj, result))

    def migrate_tbl_categorie(self, dry_run=False):
        print("Begin migrate tbl_categorie")
        cur = self.conn.cursor()
        str_query = f"""SELECT * FROM tbl_categorie;"""
        cur.nextset()
        cur.execute(str_query)
        tpl_result = cur.fetchall()

        lst_result = []
        self.dct_tbl["tbl_categorie"] = lst_result

        # 0 `NoCategorie` int(10) UNSIGNED NOT NULL,
        # 1 `TitreCategorie` varchar(255) CHARACTER SET latin1 DEFAULT NULL,
        # 2 `Supprimer` int(1) DEFAULT NULL,
        # 3 `Approuver` int(1) DEFAULT NULL

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})

            i = 0
            for result in tpl_result:
                i += 1
                pos_id = f"{i}/{len(tpl_result)}"

                if DEBUG_LIMIT and i >= LIMIT:
                    print(f"REACH LIMIT {LIMIT}")
                    break

                if not dry_run:
                    # TODO create new field instead put that information in name
                    name = f"{result[0]} - {result[1]}"

                    value = {
                        'name': name,
                        'active': result[2] == 0,
                    }

                    skill_id = env['hr.skill'].create(value)
                else:
                    skill_id = None
                    name = ""

                lst_result.append((skill_id, result))

                print(f"{pos_id} - hr.skill - tbl_categorie - ADDED '{name}' id {result[0]}")

    def migrate_tbl_sous_categorie(self, dry_run=False):
        print("Begin migrate tbl_sous_categorie")
        cur = self.conn.cursor()
        str_query = f"""SELECT * FROM tbl_sous_categorie;"""
        cur.nextset()
        cur.execute(str_query)
        tpl_result = cur.fetchall()

        lst_result = []
        self.dct_tbl["tbl_sous_categorie"] = lst_result

        # 0 `NoSousCategorie` char(2) NOT NULL DEFAULT '',
        # 1 `NoCategorie` int(10) UNSIGNED NOT NULL DEFAULT '0',
        # 2 `TitreSousCategorie` varchar(255) DEFAULT NULL,
        # 3 `Supprimer` int(1) DEFAULT NULL,
        # 4 `Approuver` int(1) DEFAULT NULL

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})

            i = 0
            for result in tpl_result:
                i += 1
                pos_id = f"{i}/{len(tpl_result)}"

                if DEBUG_LIMIT and i >= LIMIT:
                    print(f"REACH LIMIT {LIMIT}")
                    break

                if not dry_run:
                    # TODO create new field instead put that information in name
                    name = f"{result[0]}-{result[1]} - {result[2]}"

                    parent_id, _ = self._get_categorie(id_categorie=result[1])

                    value = {
                        'name': name,
                        'parent_id': parent_id.id,
                        'active': result[3] == 0,
                    }

                    skill_id = env['hr.skill'].create(value)
                else:
                    skill_id = None
                    name = ""

                lst_result.append((skill_id, result))

                print(f"{pos_id} - hr.skill - tbl_sous_categorie - ADDED '{name}' id {result[0]}")

    def migrate_tbl_categorie_sous_categorie(self, dry_run=False):
        print("Begin migrate tbl_categorie_sous_categorie")
        cur = self.conn.cursor()
        str_query = f"""SELECT * FROM tbl_categorie_sous_categorie;"""
        cur.nextset()
        cur.execute(str_query)
        tpl_result = cur.fetchall()

        lst_result = []
        self.dct_tbl["tbl_categorie_sous_categorie"] = lst_result
        # dct_parent_key = collections.defaultdict(list)

        # 0 `NoCategorieSousCategorie` int(10) UNSIGNED NOT NULL,
        # 1 `NoSousCategorie` char(2) CHARACTER SET latin1 DEFAULT NULL,
        # 2 `NoCategorie` int(10) UNSIGNED DEFAULT NULL,
        # 3 `TitreOffre` varchar(255) CHARACTER SET latin1 DEFAULT NULL,
        # 4 `Supprimer` int(1) DEFAULT NULL,
        # 5 `Approuver` int(1) DEFAULT NULL,
        # 6 `Description` varchar(255) CHARACTER SET latin1 DEFAULT NULL,
        # 7 `NoOffre` int(10) UNSIGNED DEFAULT NULL

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})

            i = 0
            for result in tpl_result:
                i += 1
                pos_id = f"{i}/{len(tpl_result)}"

                if DEBUG_LIMIT and i >= LIMIT:
                    print(f"REACH LIMIT {LIMIT}")
                    break

                if result[7] > 900:
                    print(f"{pos_id} - hr.skill - tbl_categorie_sous_categorie - SKIPPED "
                          f"result '{result[7]}' because > 900 and id {result[0]}")
                    continue

                if not dry_run:
                    # parent_key = f"{result[2]}-{result[1]}"
                    # dct_parent_key[parent_key].append(True)

                    # TODO create new field instead put that information in name
                    # name = f"{parent_key}-{len(dct_parent_key[parent_key])} - {result[3]}"
                    name = f"{result[2]}-{result[1]}-{result[7]} - {result[3]}"

                    parent_id, _ = self._get_sous_categorie(id_categorie=result[2], id_sous_categorie=result[1])

                    value = {
                        'name': name,
                        'parent_id': parent_id.id,
                        'active': result[4] == 0,
                        'description': result[6].strip(),
                    }

                    product_id = env['hr.skill'].create(value)
                else:
                    product_id = None
                    name = ""

                lst_result.append((product_id, result))

                print(f"{pos_id} - hr.skill - tbl_categorie_sous_categorie - ADDED '{name}' id {result[0]}")

    def _get_categorie(self, id_categorie: int = None):
        if id_categorie:
            for obj_id_titre, tpl_obj in self.dct_tbl.get("tbl_categorie"):
                if tpl_obj[0] == id_categorie:
                    return obj_id_titre, tpl_obj
            print(f"Error, cannot find categorie {id_categorie}")
        return None, None

    def _get_sous_categorie(self, id_categorie: int = None, id_sous_categorie: int = None):
        if id_categorie and id_sous_categorie:
            for obj_id_titre, tpl_obj in self.dct_tbl.get("tbl_sous_categorie"):
                if tpl_obj[1] == id_categorie and tpl_obj[0] == id_sous_categorie:
                    return obj_id_titre, tpl_obj
            print(f"Error, cannot find categorie {id_categorie} and sous_categorie {id_sous_categorie}")
        return None, None
