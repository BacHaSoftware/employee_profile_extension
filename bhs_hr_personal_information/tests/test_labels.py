# -*- coding: utf-8 -*-
"""Labels and contexts of the module fields."""
import re

from lxml import etree

from odoo.tests import tagged

from .common import MODULE, PERMANENT_FIELDS, PersonalInfoCommon

EMPLOYEE_FORM = 'hr.view_employee_form'
PREFERENCES_FORM = 'hr.res_users_view_form_preferences'
MODULE_FIELDS = PERMANENT_FIELDS + ('identification_id', 'cccd_issue_date', 'cccd_issue_place')
LABELS = {
    'en_US': {'identification_id': 'Citizen ID Number', 'private_permanent_country_id': 'Permanent Country'},
    'vi_VN': {'identification_id': 'Số CCCD', 'private_permanent_country_id': 'Quốc gia thường trú'},
}


@tagged('post_install', '-at_install')
class TestLabels(PersonalInfoCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.langs = ['en_US']
        try:
            cls.env['res.lang']._activate_lang('vi_VN')
            cls.env['ir.module.module']._load_module_terms([MODULE], ['vi_VN'], overwrite=True)
            cls.langs.append('vi_VN')
        except Exception:  # noqa: BLE001 - language not loadable here: check en_US only
            pass

    def _env(self, lang):
        return self.env(context=dict(self.env.context, lang=lang))

    def test_citizen_id_label_survives_a_view_that_rewrites_the_field(self):
        """A third-party view (e.g. Open HRMS hr_employee_updation) replaces the core identification_id node:
        the employee form still labels it "Citizen ID Number"."""
        self.env['ir.ui.view'].create({
            'name': 'hpi.test.rewrite.identification_id',
            'model': 'hr.employee',
            'inherit_id': self.env.ref(EMPLOYEE_FORM).id,
            'arch': """<data>
                <field name="identification_id" position="replace"/>
                <xpath expr="//page[@name='personal_information']" position="inside">
                    <group name="hpi_test_identification"><field name="identification_id"/></group>
                </xpath>
            </data>""",
        })
        for lang in self.langs:
            with self.subTest(lang=lang):
                Employee = self._env(lang)['hr.employee'].with_user(self.hr_officer)
                views = Employee.get_views([(self.env.ref(EMPLOYEE_FORM).id, 'form')])
                arch = etree.fromstring(views['views']['form']['arch'])
                field_label = views['models']['hr.employee']['fields']['identification_id']['string']
                nodes = arch.xpath("//field[@name='identification_id']")
                self.assertTrue(nodes)
                for node in nodes:
                    self.assertEqual(node.get('string') or field_label, LABELS[lang]['identification_id'])

    def test_field_labels(self):
        for lang in self.langs:
            for model in ('hr.employee', 'res.users'):
                with self.subTest(lang=lang, model=model):
                    fields = self._env(lang)[model].with_user(self.admin).fields_get(attributes=['string'])
                    for name, label in LABELS[lang].items():
                        self.assertEqual(fields[name]['string'], label, name)

    def test_module_field_labels_are_unique(self):
        """No duplicate-label warning: no other field shares the label of a module field."""
        for model in ('hr.employee', 'res.users'):
            fields = self.env[model]._fields
            for name in MODULE_FIELDS:
                with self.subTest(model=model, field=name):
                    same = [other for other, field in fields.items()
                            if other != name and field.string == fields[name].string]
                    self.assertFalse(same, f"{model}.{name} shares the label {fields[name].string!r} with {same}")

    def test_permanent_state_defaults_to_the_permanent_country(self):
        for model, view in (('hr.employee', EMPLOYEE_FORM), ('res.users', PREFERENCES_FORM)):
            with self.subTest(model=model):
                views = self.env[model].with_user(self.admin).get_views([(self.env.ref(view).id, 'form')])
                arch = etree.fromstring(views['views']['form']['arch'])
                nodes = arch.xpath("//field[@name='private_permanent_state_id']")
                self.assertEqual(len(nodes), 1)
                context = nodes[0].get('context') or ''
                self.assertRegex(context, r"'default_country_id':\s*private_permanent_country_id\b")
                self.assertNotRegex(context, re.escape('private_country_id'))
