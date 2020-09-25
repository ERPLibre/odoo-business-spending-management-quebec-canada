# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'accorderie migrate mysql',
    'version': '12.0.0.1',
    'author': "TechnoLibre",
    'website': 'https://technolibre.ca',
    'license': 'AGPL-3',
    'category': 'Extra tools',
    'summary': 'Migrate database of project Accorderie',
    'description': """
accorderie migrate mysql
========================

""",
    'depends': [
        'l10n_ca'
    ],
    'external_dependencies': {
        'python': [
            'MySQLdb',
        ],
    },
    'data': [
    ],
    "post_init_hook": "post_init_hook",
    'installable': True,
}
