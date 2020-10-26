# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import base64
from odoo import _, api, SUPERUSER_ID
import collections

_logger = logging.getLogger(__name__)

try:
    import MySQLdb

    assert MySQLdb
except (ImportError, AssertionError):
    _logger.info('MySQLdb not available. Please install "mysqlclient" python package.')


def post_init_hook(cr, e):
    migration = MigrationAccorderie(cr)
    migration.migrate_tbl_accorderie()
    migration.migrate_tbl_fournisseur()


class MigrationAccorderie:
    def __init__(self, cr):
        print("Start migration of Accorderie of Quebec.")
        assert MySQLdb
        self.host = "localhost"
        self.user = "accorderie"
        self.passwd = "accorderie"
        self.db_name = "accorderie_log_2019_2"
        self.conn = MySQLdb.connect(host=self.host, user=self.user, passwd=self.passwd, db=self.db_name)
        self.source_code_path = "/home/mathben/Documents/technolibre/accorderie/accorderie20200826/Intranet"
        self.logo_path = f"{self.source_code_path}/images/logo"
        self.cr = cr

        self.dct_tbl = {}

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
            i = 0
            for result in tpl_result:
                i += 1
                pos_id = f"{i}/{len(tpl_result)}"

                # Exception for warehouse
                if result[5].strip() == "Réseau Accorderie (du Qc)":
                    name = result[5].strip()
                    obj = env['res.company'].browse(1)
                    obj.name = name
                    obj.street = result[7].strip()
                    obj.zip = result[8].strip()
                    obj.phone = result[9].strip()
                    obj.partner_id.fax = result[10].strip()
                    obj.email = result[11].strip()
                    obj.website = "www.accorderie.ca"
                    obj.tz = "America/Montreal"
                    if result[16]:
                        data = open(f"{self.logo_path}/{result[16]}", "rb").read()
                        obj.logo = base64.b64encode(data)
                    print(f"{pos_id} - RES.PARTNER - tbl_accorderie - UPDATED {name}")
                else:
                    name = f"Accorderie {result[6].strip()}"
                    value = {
                        'name': name,
                        'street': result[7].strip(),
                        'zip': result[8].strip(),
                        'phone': result[9].strip(),
                        'email': result[11].strip(),
                        # 'website': result[14].strip(),
                    }
                    if result[16]:
                        data = open(f"{self.logo_path}/{result[16]}", "rb").read()
                        value["logo"] = base64.b64encode(data)

                    obj = env['res.company'].create(value)
                    obj.tz = "America/Montreal"
                    obj.partner_id.active = result[19] == 0
                    obj.partner_id.fax = result[10].strip()

                    print(f"{pos_id} - RES.PARTNER - tbl_accorderie - ADDED {name}")
                lst_result.append((obj, result))

    def migrate_tbl_fournisseur(self):
        print("Begin migrate tbl_fournisseur")
        cur = self.conn.cursor()
        # Get all fournisseur
        str_query = f"""SELECT * FROM tbl_fournisseur;"""
        cur.nextset()
        cur.execute(str_query)
        tpl_result = cur.fetchall()

        self.dct_tbl["tbl_fournisseur"] = tpl_result

        # Debug duplicate data, need unique name
        dct_debug = collections.defaultdict(list)
        for result in tpl_result:
            dct_debug[result[4]].append(result)
        lst_to_remove = []
        for key, value in dct_debug.items():
            if len(value) > 1:
                print(f"Duplicate name ({len(value)}) {key}: {value}\n")
            else:
                lst_to_remove.append(key)
        for key in lst_to_remove:
            del dct_debug[key]

        self.dct_tbl["tbl_fournisseur|conflict"] = dct_debug

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
                    accorderie_id = self._get_accorderie(result[1])
                    if not accorderie_id:
                        raise Exception(f"Cannot find associated accorderie {result}")
                    accorderie_id.partner_id.supplier = True
                    new_comment = ""
                    if accorderie_id.partner_id.comment:
                        new_comment = f"{accorderie_id.partner_id.comment}\n"
                    accorderie_id.partner_id.comment = f"{new_comment}Fournisseur : {result[13].strip()}"
                    print(f"{pos_id} - RES.PARTNER - tbl_fournisseur - UPDATED {name}/{accorderie_id.partner_id.name}")
                    continue
                elif name in dct_debug.keys():
                    lst_duplicated = dct_debug.get(name)
                    print(f"{pos_id} - RES.PARTNER - tbl_fournisseur - SKIPPED {name}")
                    continue

                value = {
                    'name': name,
                    'street': result[5].strip(),
                    'zip': result[6].strip(),
                    'phone': result[7].strip(),
                    'fax': result[8].strip(),
                    'email': result[9].strip(),
                    'supplier': True,
                    'customer': False,
                    'company_type': 'company',
                    'comment': result[13].strip(),
                    'tz': "America/Montreal",
                    'active': result[14] == 1,
                }

                obj = env['res.partner'].create(value)

                value_contact = {
                    'name': result[10].strip(),
                    'function': result[11].strip(),
                    'email': result[12].strip(),
                    'parent_id': obj.id,
                }
                obj_contact = env['res.partner'].create(value_contact)

                print(f"{pos_id} - RES.PARTNER - tbl_fournisseur - ADDED {name}")

    def _get_accorderie(self, id_accorderie: int = None):
        if id_accorderie:
            for obj_id_accorderie, tpl_obj in self.dct_tbl.get("tbl_accorderie"):
                if tpl_obj[0] == id_accorderie:
                    return obj_id_accorderie
