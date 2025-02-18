#!/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

{
    "name": "Plan View Agile Place Mgmt",
    "version": "16.0.1.0",
    "author": "TechnoLibre",
    "license": "GPL-3",
    "website": "https://technolibre.ca",
    "application": True,
    "data": [
        "security/ir.model.access.csv",
        "security/groups.xml",
        "views/hr_views.xml",
        "views/planviewap_automated_action_log.xml",
        "views/planviewap_customfield.xml",
        "views/planviewap_board.xml",
        "views/planviewap_board_type.xml",
        "views/planviewap_card.xml",
        "views/planviewap_card_type.xml",
        "views/planviewap_lane.xml",
        "views/planviewap_processus.xml",
        "views/planviewap_request_history.xml",
        "views/planviewap_session.xml",
        "views/planviewap_sms_history.xml",
        "views/menu.xml",
    ],
    "depends": [
        "hr",
        "contacts",
        "purchase",
        "fieldservice",
        "fieldservice_calendar",
        "fieldservice_geoengine",
        "fieldservice_skill",
        "fieldservice_timeline",
        "fieldservice_vehicle",
        "partner_manual_rank",
    ],
    "installable": True,
}
