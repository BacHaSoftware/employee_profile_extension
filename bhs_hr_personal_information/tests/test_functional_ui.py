# -*- coding: utf-8 -*-
"""UI-level tests.

- Clickbot (run explicitly, slow: $T test --db <db> --clickbot bhs_hr_personal_information): Odoo's clickbot clicks
  every menu of the Employees app for each role. Any JS/RPC/access error -> FAIL.
- Browser tour (standard run): an employee fills his personal information in My Preferences.
"""
from datetime import date

from odoo.tests import HttpCase, tagged

from .common import TZ

APPS: list[str] = ['hr.menu_hr_root']
# No base.default_user_group: a DB may make it imply HR manager, the low roles must stay low.
ROLES = {
    'click_hpi_admin': ['base.group_user', 'base.group_system', 'hr.group_hr_manager'],
    'click_hpi_hr_officer': ['base.group_user', 'hr.group_hr_user'],
    'click_hpi_employee': ['base.group_user'],
}


class UiMixin:

    def _make_user(self, login, groups):
        group_ids = [self.env.ref(g).id for g in groups]
        existing = self.env['res.users'].search([('login', '=', login)])
        if existing:
            # the tour enters dates in the en_US format: reset lang and tz as well
            existing.write({'group_ids': [(6, 0, group_ids)], 'password': login, 'tz': TZ, 'lang': 'en_US'})
            return existing
        return self.env['res.users'].with_context(no_reset_password=True).create({
            'name': login, 'login': login, 'password': login, 'email': f'{login}@click.example.com', 'tz': TZ,
            'lang': 'en_US', 'group_ids': [(6, 0, group_ids)],
        })

    def _seed_data(self, users):
        """One employee per user, with personal information, plus an employee without user."""
        for user in users:
            self.env['hr.employee'].create({
                'name': f'HPI {user.login}', 'user_id': user.id, 'identification_id': f'0010{user.id}',
                'cccd_issue_date': date(2021, 3, 15), 'cccd_issue_place': 'Police HN',
            })
        self.env['hr.employee'].create({'name': 'HPI No User', 'identification_id': '0010NOUSER'})


@tagged('click_all', 'post_install', '-at_install', '-standard')
class TestFunctionalUI(UiMixin, HttpCase):

    def test_clickbot_module_apps(self):
        users = [self._make_user(login, groups) for login, groups in ROLES.items()]
        self._seed_data(users)
        for user in users:
            visible = self.env['ir.ui.menu'].with_user(user)._visible_menu_ids()
            for xmlid in APPS:
                self.assertIn(self.env.ref(xmlid).id, visible, f"Role {user.login} must see app {xmlid}")
                with self.subTest(role=user.login, app=xmlid):
                    self.browser_js(
                        '/odoo',
                        "odoo.loader.modules.get('@web/webclient/clickbot/clickbot_loader')"
                        f".startClickEverywhere({{ xmlId: '{xmlid}', logger: true }});",
                        login=user.login, timeout=1200, success_signal='clickbot test succeeded')


@tagged('post_install', '-at_install')
class TestPreferencesTour(UiMixin, HttpCase):

    def test_employee_fills_preferences(self):
        user = self._make_user('tour_hpi_employee', ['base.group_user'])
        employee = self.env['hr.employee'].create({'name': 'HPI Tour Employee', 'user_id': user.id})
        self.start_tour('/odoo', 'bhs_hpi_preferences_tour', login=user.login)
        self.assertEqual(employee.identification_id, '079090001234')
        self.assertEqual(employee.cccd_issue_place, 'Police Ha Noi')
        self.assertEqual(employee.cccd_issue_date, date(2021, 3, 15))
        self.assertEqual(employee.birthday, date(1990, 5, 20))
