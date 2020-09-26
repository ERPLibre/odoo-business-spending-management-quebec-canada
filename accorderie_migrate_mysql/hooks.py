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
    assert MySQLdb
    host = "localhost"
    user = "accorderie"
    passwd = "accorderie"
    db_name = "accorderie_log_2019_2"
    conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=db_name)

    source_code_path = "/home/mathben/Documents/technolibre/accorderie/accorderie20200826/Intranet"
    logo_path = f"{source_code_path}/images/logo"

    cur = conn.cursor()
    # Get all Accorderie
    str_query = f"""SELECT * FROM tbl_accorderie;"""
    cur.nextset()
    cur.execute(str_query)
    tpl_result = cur.fetchall()

    # `NoAccorderie` int(10) UNSIGNED NOT NULL,
    # `NoRegion` int(10) UNSIGNED NOT NULL,
    # `NoVille` int(10) UNSIGNED NOT NULL,
    # `NoArrondissement` int(10) UNSIGNED DEFAULT NULL,
    # `NoCartier` int(10) UNSIGNED DEFAULT NULL,
    # `Nom` varchar(45) CHARACTER SET latin1 DEFAULT NULL,
    # `NomComplet` varchar(255) COLLATE latin1_general_ci NOT NULL,
    # `AdresseAccorderie` varchar(255) CHARACTER SET latin1 DEFAULT NULL,
    # `CodePostalAccorderie` varchar(7) CHARACTER SET latin1 DEFAULT NULL,
    # `TelAccorderie` varchar(10) CHARACTER SET latin1 DEFAULT NULL,
    # `TelecopieurAccorderie` varchar(10) CHARACTER SET latin1 DEFAULT NULL,
    # `CourrielAccorderie` varchar(255) CHARACTER SET latin1 DEFAULT NULL,
    # `MessageGrpAchat` text COLLATE latin1_general_ci,
    # `MessageAccueil` text COLLATE latin1_general_ci,
    # `URL_Public_Accorderie` varchar(255) COLLATE latin1_general_ci DEFAULT NULL,
    # `URL_Transac_Accorderie` varchar(255) COLLATE latin1_general_ci DEFAULT NULL,
    # `URL_LogoAccorderie` varchar(255) COLLATE latin1_general_ci DEFAULT NULL,
    # `GrpAchat_Admin` tinyint(4) DEFAULT '0',
    # `GrpAchat_Accordeur` tinyint(4) DEFAULT '0',
    # `NonVisible` int(11) NOT NULL DEFAULT '0',
    # `DateMAJ_Accorderie` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

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
                data = open(f"{logo_path}/{result[16]}", "rb").read()
                value["logo"] = base64.b64encode(data)

            obj = env['res.company'].create(value)
            obj.tz = "America/Montreal"
            obj.active = result[19] == 0
            print(f"RES.PARTNER - {name} added.")
