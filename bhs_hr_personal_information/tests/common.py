# -*- coding: utf-8 -*-
"""Shared fixtures for the personal information tests.

Roles: admin, HR manager, HR officer, employee (self-service), another employee, portal user and an internal
user without employee.

Module fields:
- hr.employee: identification_id (core hr.version field since 20, versioned), cccd_issue_date, cccd_issue_place,
  private_permanent_* (HR only);
- res.users: the same fields, simulated related to the employee of the user (core ``related_employee_field``),
  writable by the user himself (``user_writeable``); birthday is a core field of res.users since 20.
"""
from datetime import date

from odoo.tests import TransactionCase, new_test_user

MODULE = 'bhs_hr_personal_information'
TZ = 'Asia/Ho_Chi_Minh'

CHAR_FIELDS = (
    'identification_id', 'cccd_issue_place',
    'private_permanent_street', 'private_permanent_street2', 'private_permanent_city',
)
EMPLOYEE_FIELDS = CHAR_FIELDS + (
    'cccd_issue_date', 'private_permanent_state_id', 'private_permanent_country_id',
)
USER_FIELDS = EMPLOYEE_FIELDS + ('birthday',)
PERMANENT_FIELDS = (
    'private_permanent_street', 'private_permanent_street2', 'private_permanent_city',
    'private_permanent_state_id', 'private_permanent_country_id',
)


class PersonalInfoCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = cls.env.ref('base.vn')
        cls.state = cls.env['res.country.state'].create({
            'name': 'HPI Test Province', 'code': 'HPI', 'country_id': cls.country.id,
        })

        cls.admin = cls.env.ref('base.user_admin')
        cls.hr_manager = cls._user('hpi_hr_manager', 'base.group_user,hr.group_hr_manager')
        cls.hr_officer = cls._user('hpi_hr_officer', 'base.group_user,hr.group_hr_user')
        cls.emp_user = cls._user('hpi_employee', 'base.group_user')
        cls.other_user = cls._user('hpi_other', 'base.group_user')
        cls.portal_user = cls._user('hpi_portal', 'base.group_portal')
        cls.no_emp_user = cls._user('hpi_no_employee', 'base.group_user')

        cls.emp = cls.env['hr.employee'].create({'name': 'HPI Employee', 'user_id': cls.emp_user.id})
        cls.other_emp = cls.env['hr.employee'].create({
            'name': 'HPI Other', 'user_id': cls.other_user.id, **cls._values('OTHER'),
        })

    @classmethod
    def _user(cls, login, groups):
        # tz: required on the Preferences form
        return new_test_user(cls.env, login=login, groups=groups, email=f'{login}@example.com',
                             name=login.replace('_', ' ').title(), tz=TZ)

    @classmethod
    def _values(cls, tag, with_birthday=False):
        """Values for every module field (``tag`` makes them distinct per test)."""
        vals = {
            'identification_id': f'0010{tag}',
            'cccd_issue_date': date(2021, 3, 15),
            'cccd_issue_place': f'Police {tag}',
            'private_permanent_street': f'1 Street {tag}',
            'private_permanent_street2': f'Ward {tag}',
            'private_permanent_city': f'City {tag}',
            'private_permanent_state_id': cls.state.id,
            'private_permanent_country_id': cls.country.id,
        }
        if with_birthday:
            vals['birthday'] = date(1990, 5, 20)
        return vals

    def assertStored(self, employee, vals):
        """Values as stored on the employee (read as superuser)."""
        employee = employee.sudo()
        for name, expected in vals.items():
            value = employee[name]
            if hasattr(value, '_name'):
                value = value.id
            self.assertEqual(value, expected, f"{employee.name}.{name}")
