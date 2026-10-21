{
    "name": "Employee Profile Extension",
    "version": "20.0.1.0.2",
    "author": "Bac Ha Software",
    "depends": ["hr"],
    'summary': 'Centralize employee personal information management and enable employees to self-service profile updates through the My Profile portal.',
    "data": [
        "views/bhs_inherit_preferences.xml",
        "views/bhs_inherit_employee_views.xml"
    ],
    'assets': {
        'web.assets_tests': [
            'bhs_hr_personal_information/static/tests/tours/**/*',
        ],
    },
    'images': ['static/description/banner.png'],
    "installable": True,
    "application": False,
    'license': 'LGPL-3',
}