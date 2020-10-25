# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import base64
from odoo import _, api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

try:
    import MySQLdb

    assert MySQLdb
except (ImportError, AssertionError):
    _logger.info('MySQLdb not available. Please install "mysqlclient" python package.')


def post_init_hook(cr, e):
    migration = MigrationAccorderie(cr)
    migration.migrate_tbl_accorderie()


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

    def migrate_tbl_accorderie(self):
        cur = self.conn.cursor()
        # Get all Accorderie
        str_query = f"""SELECT * FROM tbl_accorderie;"""
        cur.nextset()
        cur.execute(str_query)
        tpl_result = cur.fetchall()

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

            for result in tpl_result:
                name = f"Accorderie {result[6]}"
                value = {
                    'name': name,
                    'street': result[7],
                    'zip': result[8],
                    'phone': result[9],
                    'email': result[11],
                    'website': result[14],
                }
                if result[16]:
                    data = open(f"{self.logo_path}/{result[16]}", "rb").read()
                    value["logo"] = base64.b64encode(data)

                obj = env['res.company'].create(value)
                obj.tz = "America/Montreal"
                obj.partner_id.active = result[19] == 0
                print(f"RES.PARTNER - {name} added.")
