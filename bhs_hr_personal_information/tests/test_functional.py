# -*- coding: utf-8 -*-
"""Business flows through the real forms: HR edits the employee form, employees fill their own Preferences."""
from datetime import date

from lxml import etree

from odoo.tests import Form, tagged

from .common import MODULE, PERMANENT_FIELDS, PersonalInfoCommon

EMPLOYEE_FORM = 'hr.view_employee_form'
PREFERENCES_FORM = 'hr.res_users_view_form_preferences'


@tagged('post_install', '-at_install')
class TestForms(PersonalInfoCommon):

    def _arch(self, model, view_xmlid, user):
        view = self.env.ref(view_xmlid)
        return etree.fromstring(self.env[model].with_user(user).get_views([(view.id, 'form')])['views']['form']['arch'])

    def test_hr_roles_edit_employee_form(self):
        for user in (self.admin, self.hr_manager, self.hr_officer):
            with self.subTest(role=user.login):
                tag = user.login.upper()
                with Form(self.other_emp.with_user(user), view=EMPLOYEE_FORM) as form:
                    form.identification_id = f'0010{tag}'
                    form.cccd_issue_date = date(2022, 1, 2)
                    form.cccd_issue_place = f'Police {tag}'
                self.assertStored(self.other_emp, {
                    'identification_id': f'0010{tag}',
                    'cccd_issue_date': date(2022, 1, 2),
                    'cccd_issue_place': f'Police {tag}',
                })
                # the version of the employee holds the identification number (core 20 field)
                self.assertEqual(self.other_emp.sudo().version_id.identification_id, f'0010{tag}')

    def test_citizen_id_label(self):
        """The module label "Citizen ID Number" (also in vi_VN) replaces the core "Identification No"."""
        expected = {'en_US': 'Citizen ID Number'}
        try:
            self.env['res.lang']._activate_lang('vi_VN')
            self.env['ir.module.module']._load_module_terms([MODULE], ['vi_VN'], overwrite=True)
            expected['vi_VN'] = 'Số CCCD'
        except Exception:  # noqa: BLE001 - language not loadable here: check en_US only
            pass
        view = self.env.ref(EMPLOYEE_FORM)
        for lang, label in expected.items():
            with self.subTest(lang=lang):
                env = self.env(context=dict(self.env.context, lang=lang))
                views = env['hr.employee'].with_user(self.hr_officer).get_views([(view.id, 'form')])
                node = etree.fromstring(views['views']['form']['arch']).xpath("//field[@name='identification_id']")
                # label of the field itself (hr.version), the node only overrides it with a string attribute
                field_label = views['models']['hr.employee']['fields']['identification_id']['string']
                self.assertEqual(node[0].get('string') or field_label, label)
                description = env['res.users'].with_user(self.emp_user).fields_get(['identification_id'])
                self.assertEqual(description['identification_id']['string'], label)

    def test_employee_form_layout(self):
        arch = self._arch('hr.employee', EMPLOYEE_FORM, self.hr_officer)
        names = [node.get('name') for node in arch.xpath("//field[@name='identification_id']/following::field")]
        self.assertEqual(names[:2], ['cccd_issue_date', 'cccd_issue_place'])
        for name in PERMANENT_FIELDS:
            nodes = arch.xpath(f"//field[@name='{name}']")
            self.assertEqual(len(nodes), 1, name)
            self.assertEqual(nodes[0].get('invisible'), '1', f"{name} stays hidden on the employee form")

    def test_employee_fills_own_preferences(self):
        me = self.emp_user.with_user(self.emp_user)
        with Form(me, view=PREFERENCES_FORM) as form:
            form.identification_id = '0010PREF'
            form.cccd_issue_date = date(2023, 4, 5)
            form.cccd_issue_place = 'Police PREF'
            form.birthday = date(1991, 7, 8)
        self.assertStored(self.emp, {
            'identification_id': '0010PREF',
            'cccd_issue_date': date(2023, 4, 5),
            'cccd_issue_place': 'Police PREF',
            'birthday': date(1991, 7, 8),
        })
        # permanent address: hidden on the form, still writable by the user himself
        me.write({name: value for name, value in self._values('PREF').items() if name in PERMANENT_FIELDS})
        self.assertStored(self.emp, {'private_permanent_city': 'City PREF', 'private_permanent_state_id': self.state.id})
        form = Form(me, view=PREFERENCES_FORM)
        self.assertEqual(form.identification_id, '0010PREF')
        self.assertEqual(form.cccd_issue_place, 'Police PREF')

    def test_preferences_layout(self):
        arch = self._arch('res.users', PREFERENCES_FORM, self.emp_user)
        self.assertFalse(arch.xpath("//field[@name='ssnid']"))
        self.assertEqual(len(arch.xpath("//field[@name='birthday']")), 1, "birthday is shown once, by the core view")
        for name in ('identification_id', 'cccd_issue_date', 'cccd_issue_place'):
            node = arch.xpath(f"//field[@name='{name}']")
            self.assertEqual(len(node), 1, name)
            self.assertNotEqual(node[0].get('invisible'), '1', name)
            self.assertNotEqual(node[0].get('readonly'), '1', name)
        for name in PERMANENT_FIELDS:
            nodes = arch.xpath(f"//field[@name='{name}']")
            self.assertEqual(len(nodes), 1, name)
            self.assertEqual(nodes[0].get('invisible'), '1', f"{name} stays hidden on the Preferences form")

    def test_user_without_employee_opens_preferences(self):
        me = self.no_emp_user.with_user(self.no_emp_user)
        action = me.action_get()
        self.assertEqual(action['res_model'], 'res.users')
        form = Form(me, view=PREFERENCES_FORM)
        for name in ('identification_id', 'cccd_issue_date', 'cccd_issue_place', 'birthday'):
            self.assertFalse(getattr(form, name), name)

    def test_employee_preferences_action(self):
        action = self.emp_user.with_user(self.emp_user).action_get()
        self.assertEqual(action['views'][0][0], self.env.ref('hr.res_users_view_form_preferences').id)

    def test_views_load_for_each_role(self):
        for user in (self.admin, self.hr_manager, self.hr_officer):
            with self.subTest(role=user.login):
                self.env['hr.employee'].with_user(user).get_views([(False, 'form'), (False, 'list')])
        for user in (self.admin, self.hr_officer, self.emp_user, self.no_emp_user):
            with self.subTest(role=user.login):
                self.env['res.users'].with_user(user).get_views([(self.env.ref(PREFERENCES_FORM).id, 'form')])
