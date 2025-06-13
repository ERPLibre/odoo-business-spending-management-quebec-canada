{
    "name": "Asana",
    "version": "12.0.1.0",
    "author": "TechnoLibre",
    "license": "AGPL-3",
    "website": "https://technolibre.ca",
    "application": True,
    "data": [
        "security/ir.model.access.csv",
        "views/asana_agendrix.xml",
        "views/asana_task_agendrix_resource.xml",
        "views/menu.xml",
    ],
    "depends": ["asana", "agendrix"],
    "external_dependencies": {"python": ["asana"]},
    "installable": True,
}
