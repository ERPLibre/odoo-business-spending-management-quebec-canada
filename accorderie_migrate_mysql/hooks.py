# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import base64
from odoo import _, api, SUPERUSER_ID
import collections
import os

_logger = logging.getLogger(__name__)

try:
    import MySQLdb

    assert MySQLdb
except (ImportError, AssertionError):
    _logger.info('MySQLdb not available. Please install "mysqlclient" python package.')

# TODO update me with your backup version
BACKUP_PATH = "/home/mathben/Documents/technolibre/accorderie/accorderie20200826/Intranet"


def post_init_hook(cr, e):
    migration = MigrationAccorderie(cr)
    migration.setup_configuration()
    migration.migrate_tbl_ville()
    migration.migrate_tbl_accorderie()
    migration.migrate_tbl_fournisseur()
    migration.migrate_tbl_membre()
    migration.update_user()


class MigrationAccorderie:
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

    def setup_configuration(self):
        print("Update configuration")

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
                # TODO Cause bug when uninstall
                # 'module_web_unsplash': False,
                # 'module_partner_autocomplete': False,

            }
            event_config = env['res.config.settings'].sudo().create(values)
            event_config.execute()

    def migrate_tbl_ville(self):
        print("Begin migrate tbl_ville")
        cur = self.conn.cursor()
        # Get all ville
        str_query = f"""SELECT * FROM tbl_ville;"""
        cur.nextset()
        cur.execute(str_query)
        tpl_result = cur.fetchall()

        # 0 `NoVille` int(10) UNSIGNED NOT NULL,
        # 1 `Ville` varchar(60) DEFAULT NULL,
        # 2 `NoRegion` int(10) UNSIGNED DEFAULT NULL

        lst_result = list(tpl_result)
        self.dct_tbl["tbl_ville"] = lst_result

    def migrate_tbl_accorderie(self):
        print("Begin migrate tbl_accorderie")
        cur = self.conn.cursor()
        # Get all Accorderie
        str_query = f"""SELECT * FROM tbl_accorderie;"""
        cur.nextset()
        cur.execute(str_query)
        tpl_result = cur.fetchall()

        lst_result = []
        self.dct_tbl["tbl_accorderie"] = lst_result

        # 0 `NoAccorderie` int(10) UNSIGNED NOT NULL,
        # 1 `NoRegion` int(10) UNSIGNED NOT NULL,
        # 2 `NoVille` int(10) UNSIGNED NOT NULL,
        # 3 `NoArrondissement` int(10) UNSIGNED DEFAULT NULL,
        # 4 `NoCartier` int(10) UNSIGNED DEFAULT NULL,
        # 5 `Nom` varchar(45) CHARACTER SET latin1 DEFAULT NULL,
        # 6 `NomComplet` varchar(255) COLLATE latin1_general_ci NOT NULL,
        # 7 `AdresseAccorderie` varchar(255) CHARACTER SET latin1 DEFAULT NULL,
        # 8 `CodePostalAccorderie` varchar(7) CHARACTER SET latin1 DEFAULT NULL,
        # 9 `TelAccorderie` varchar(10) CHARACTER SET latin1 DEFAULT NULL,
        # 10 `TelecopieurAccorderie` varchar(10) CHARACTER SET latin1 DEFAULT NULL,
        # 11 `CourrielAccorderie` varchar(255) CHARACTER SET latin1 DEFAULT NULL,
        # 12 `MessageGrpAchat` text COLLATE latin1_general_ci,
        # 13 `MessageAccueil` text COLLATE latin1_general_ci,
        # 14 `URL_Public_Accorderie` varchar(255) COLLATE latin1_general_ci DEFAULT NULL,
        # 15 `URL_Transac_Accorderie` varchar(255) COLLATE latin1_general_ci DEFAULT NULL,
        # 16 `URL_LogoAccorderie` varchar(255) COLLATE latin1_general_ci DEFAULT NULL,
        # 17 `GrpAchat_Admin` tinyint(4) DEFAULT '0',
        # 18 `GrpAchat_Accordeur` tinyint(4) DEFAULT '0',
        # 19 `NonVisible` int(11) NOT NULL DEFAULT '0',
        # 20 `DateMAJ_Accorderie` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})
            head_quarter = None
            lst_child_company = []
            i = 0
            for result in tpl_result:
                i += 1
                pos_id = f"{i}/{len(tpl_result)}"

                if result[5].strip() == "Réseau Accorderie (du Qc)":
                    # Update main company
                    name = result[5].strip()
                    obj = env['res.company'].browse(1)
                    head_quarter = obj
                    obj.name = name
                    obj.street = result[7].strip()
                    obj.zip = result[8].strip()
                    obj.phone = result[9].strip()
                    obj.partner_id.fax = result[10].strip()
                    obj.email = result[11].strip()
                    obj.website = "www.accorderie.ca"
                    obj.state_id = 543  # Quebec
                    obj.country_id = 38  # Canada
                    obj.tz = "America/Montreal"
                    # City
                    city_name = self._get_ville(result[2])
                    if city_name:
                        obj.city = city_name

                    if result[16]:
                        data = open(f"{self.logo_path}/{result[16]}", "rb").read()
                        obj.logo = base64.b64encode(data)
                    else:
                        # obj.logo = base64.b64encode(env.ref("accorderie_migrate_mysql.logo_blanc_accorderie").datas),
                        _path = os.path.dirname(__file__)
                        data = open(f"{_path}/static/img/logonoiblancaccorderie.jpg", "rb").read()
                        obj.logo = base64.b64encode(data)
                    print(f"{pos_id} - RES.PARTNER - tbl_accorderie - UPDATED '{name}' id {result[0]}")
                else:
                    # Create new accorderie
                    name = f"Accorderie {result[6].strip()}"
                    value = {
                        'name': name,
                        'street': result[7].strip(),
                        'zip': result[8].strip(),
                        'phone': result[9].strip(),
                        'email': result[11].strip(),
                        'state_id': 543,  # Quebec
                        'country_id': 38,  # Canada
                        # 'website': result[14].strip(),
                    }
                    if result[16]:
                        data = open(f"{self.logo_path}/{result[16]}", "rb").read()
                        value["logo"] = base64.b64encode(data)

                    # City
                    city_name = self._get_ville(result[2])
                    if city_name:
                        value["city"] = city_name

                    obj = env['res.company'].create(value)
                    lst_child_company.append(obj)
                    obj.tz = "America/Montreal"
                    obj.partner_id.active = result[19] == 0
                    obj.partner_id.fax = result[10].strip()

                    print(f"{pos_id} - RES.PARTNER - tbl_accorderie - ADDED '{name}' id {result[0]}")
                lst_result.append((obj, result))

                if head_quarter:
                    for child in lst_child_company:
                        child.parent_id = head_quarter.id

    def migrate_tbl_fournisseur(self):
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
                name = result[4].strip()

                if "Accorderie" in name:
                    accorderie_id, _ = self._get_accorderie(result[1])
                    if not accorderie_id:
                        raise Exception(f"Cannot find associated accorderie {result}")
                    accorderie_id.partner_id.supplier = True
                    new_comment = ""
                    if accorderie_id.partner_id.comment:
                        new_comment = f"{accorderie_id.partner_id.comment}\n"
                    accorderie_id.partner_id.comment = f"{new_comment}Fournisseur : {result[13].strip()}"
                    print(f"{pos_id} - RES.PARTNER - tbl_fournisseur - "
                          f"UPDATED '{name}/{accorderie_id.partner_id.name}' id {result[0]}")
                    continue
                # elif name in dct_debug.keys():
                #     lst_duplicated = dct_debug.get(name)
                #     print(f"{pos_id} - RES.PARTNER - tbl_fournisseur - SKIPPED '{name}' id {result[0]}")
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
                }
                obj_contact = env['res.partner'].create(value_contact)

                print(f"{pos_id} - RES.PARTNER - tbl_fournisseur - ADDED '{name}' id {result[0]}")

    def migrate_tbl_membre(self):
        print("Begin migrate tbl_membre")
        cur = self.conn.cursor()
        # Get all fournisseur
        str_query = f"""SELECT * FROM tbl_membre;"""
        cur.nextset()
        cur.execute(str_query)
        tpl_result = cur.fetchall()

        self.dct_tbl["tbl_membre"] = tpl_result
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

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})

            i = 0
            for result in tpl_result:
                i += 1
                pos_id = f"{i}/{len(tpl_result)}"
                if result[18] and result[17]:
                    name = f"{result[18].strip()} {result[17].strip()}"
                elif result[18]:
                    name = f"{result[18].strip()}"
                elif result[17]:
                    name = f"{result[17].strip()}"

                company_id, _ = self._get_accorderie(id_accorderie=result[2])
                if not company_id:
                    raise Exception(f"Cannot find associated accorderie {result}")

                city_name = self._get_ville(result[11])

                value = {
                    'name': name,
                    'street': result[19].strip(),
                    'zip': result[15].strip(),
                    'email': result[29].strip(),
                    'supplier': False,
                    'customer': True,
                    'state_id': 543,  # Quebec
                    'country_id': 38,  # Canada
                    'tz': "America/Montreal",
                    'active': result[37] == 0,
                    'company_id': company_id.id,
                }

                if result[40]:
                    value['comment'] = result[40].strip()

                if city_name:
                    value['city'] = city_name

                self._set_phone(result, value)

                obj = env['res.partner'].create(value)

                print(f"{pos_id} - RES.PARTNER - tbl_membre - ADDED '{name}' id {result[0]}")

    def update_user(self):
        print("Update user preference")
        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})

            administrator = env['res.users'].browse(2)
            # administrator.email = "admin@nuagelibre.ca"
            # Add all society to administrator
            administrator.company_ids = env['res.company'].search([]).ids

    def _set_phone(self, result, value):
        # Manage phone
        # result 22, 25, 28 is type
        # Type: 1 choose (empty)
        # Type: 2 domicile Phone
        # Type: 3 Travail À SUPPORTÉ
        # Type: 4 Cellulaire MOBILE
        # Type: 5 Téléavertisseur (pagette) NON SUPPORTÉ

        # Pagette
        if result[22] == 5 or result[25] == 5 or result[28] == 5:
            print("WARNING, le pagette n'est pas supporté.")

        # Travail
        if result[22] == 3 or result[25] == 3 or result[28] == 3:
            print("WARNING, le téléphone travail n'est pas supporté.")

        # MOBILE
        has_mobile = False
        if result[22] == 4 and result[20] and result[20].strip():
            has_mobile = True
            value['mobile'] = result[20].strip()
            if result[21] and result[21].strip():
                print("WARNING, le numéro de poste du mobile n'est pas supporté.")
        if result[25] == 4 and result[23] and result[23].strip():
            if has_mobile:
                print("WARNING, duplicat du cellulaire.")
            else:
                has_mobile = True
                value['mobile'] = result[23].strip()
                if result[24] and result[24].strip():
                    print("WARNING, le numéro de poste du mobile n'est pas supporté.")
        if result[28] == 4 and result[26] and result[26].strip():
            if has_mobile:
                print("WARNING, duplicat du cellulaire.")
            else:
                has_mobile = True
                value['mobile'] = result[26].strip()
                if result[27] and result[27].strip():
                    print("WARNING, le numéro de poste du mobile n'est pas supporté.")

        has_domicile = False
        if result[22] == 2 and result[20] and result[20].strip():
            has_domicile = True
            value['phone'] = result[20].strip()
            if result[21] and result[21] and result[21].strip():
                print("WARNING, le numéro de poste du domicile n'est pas supporté.")
        if result[25] == 2 and result[23] and result[23].strip():
            if has_domicile:
                print("WARNING, duplicat du cellulaire.")
            else:
                has_domicile = True
                value['phone'] = result[23].strip()
                if result[24] and result[24].strip():
                    print("WARNING, le numéro de poste du domicile n'est pas supporté.")
        if result[28] == 2 and result[26] and result[26].strip():
            if has_domicile:
                print("WARNING, duplicat du cellulaire.")
            else:
                has_domicile = True
                value['phone'] = result[26].strip()
                if result[27] and result[27].strip():
                    print("WARNING, le numéro de poste du domicile n'est pas supporté.")

    def _get_accorderie(self, id_accorderie: int = None):
        if id_accorderie:
            for obj_id_accorderie, tpl_obj in self.dct_tbl.get("tbl_accorderie"):
                if tpl_obj[0] == id_accorderie:
                    return obj_id_accorderie, tpl_obj

    def _get_ville(self, id_ville: int = None):
        if id_ville:
            for tpl_obj in self.dct_tbl.get("tbl_ville"):
                if tpl_obj[0] == id_ville:
                    return tpl_obj[1]
            print(f"Error, cannot find city {id_ville}")
