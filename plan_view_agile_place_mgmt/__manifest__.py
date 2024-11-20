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
        "views/hr_views.xml",
        "views/plan_view_agile_place_customfield.xml",
        "views/plan_view_agile_place_board.xml",
        "views/plan_view_agile_place_board_type.xml",
        "views/plan_view_agile_place_card.xml",
        "views/plan_view_agile_place_card_type.xml",
        "views/plan_view_agile_place_lane.xml",
        "views/plan_view_agile_place_processus.xml",
        "views/plan_view_agile_place_request_history.xml",
        "views/plan_view_agile_place_session.xml",
        "views/plan_view_agile_place_sms_history.xml",
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
