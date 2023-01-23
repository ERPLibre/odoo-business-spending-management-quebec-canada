{
    "name": "Canada - Quebec - Accounting",
    "author": "MathBenTech",
    "website": "https://mathben.tech",
    "category": "Localization",
    "description": """
This is the module to manage the Canadian Quebec accounting chart
=================================================================

Canadian Quebec accounting charts and localizations.
    """,
    "depends": [
        "account",
        "l10n_ca",
        "account_coa_menu",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/fiscal_templates_data.xml",
        "views/account_fiscal_position_template.xml",
        "views/account_view.xml",
    ],
}
