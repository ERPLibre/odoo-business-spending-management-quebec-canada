# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Res partner fix group by company",
    "version": "12.0.0.0.1",
    "author": "MathBenTech",
    "website": "https://mathben.tech",
    "license": "AGPL-3",
    "category": "Contact",
    "summary": "CRM filter all",
    "description": """
Res partner fix group by company
================================
Group by company using commercial_partner_id instead of parent_id. Add group by parent_id. This support multi-level of company.

""",
    "depends": ["base"],
    "data": [
        "views/res_partner_views.xml",
    ],
    "installable": True,
}
