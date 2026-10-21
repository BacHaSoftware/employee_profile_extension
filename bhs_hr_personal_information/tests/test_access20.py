# -*- coding: utf-8 -*-
"""Access to the personal information fields per role (Odoo 20), in pairs:
"cannot do X" + "can still do his own part"."""
from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import EMPLOYEE_FIELDS, MODULE, USER_FIELDS, PersonalInfoCommon


def employee_field_leaks(env, module):
    """Stored hr.employee fields of ``module`` readable by non-HR users although missing on hr.employee.public."""
    public = env['hr.employee.public']._fields
    return sorted(name for name, field in env['hr.employee']._fields.items()
                  if module in (getattr(field, '_modules', None) or ()) and field.store and field.column_type
                  and not field.groups and name not in public)


@tagged('post_install', '-at_install')
class TestFieldDefinitions(PersonalInfoCommon):

    def test_module_employee_fields_not_leaking(self):
        self.assertFalse(employee_field_leaks(self.env, MODULE))

    def test_module_employee_fields_hr_only(self):
        for name in EMPLOYEE_FIELDS:
            with self.subTest(field=name):
                self.assertEqual(self.env['hr.employee']._fields[name].groups, 'hr.group_hr_user')

    def test_identification_id_is_the_core_versioned_field(self):
        field = self.env['hr.employee']._fields['identification_id']
        self.assertTrue(field.inherited, "identification_id must be the hr.version field (no hr_employee column)")
        self.assertEqual(field.inherited_field.model_name, 'hr.version')
        self.emp.identification_id = '0019001'
        self.assertEqual(self.emp.version_id.identification_id, '0019001')

    def test_user_fields_simulate_employee_fields(self):
        Users = self.env['res.users']
        self.assertNotIn('ssnid', Users._fields)
        for name in USER_FIELDS:
            with self.subTest(field=name):
                field = Users._fields[name]
                self.assertTrue(getattr(field, 'user_writeable', False), f"res.users.{name} must be user_writeable")
                self.assertEqual(getattr(field.compute, 'employee_field_name', None), name)
        self.assertNotIn(MODULE, Users._fields['birthday']._modules, "birthday is the core field of res.users")

    def test_internal_user_reads_employee_directory(self):
        # core flows read every accessible stored hr.employee field with the user's rights (redirected to
        # hr.employee.public): no module field may be among them
        Employee = self.env['hr.employee'].with_user(self.emp_user)
        fetched = {field.name for field in Employee._determine_fields_to_fetch()}
        self.assertFalse(fetched & set(EMPLOYEE_FIELDS))
        public = [name for name in fetched if name in self.env['hr.employee.public']._fields]
        Employee.search([('id', 'in', (self.emp | self.other_emp).ids)]).read(public)

    def test_cccd_fields_hidden_from_non_hr(self):
        for user in (self.emp_user, self.portal_user):
            fields = self.env['hr.employee'].with_user(user).fields_get()
            for name in EMPLOYEE_FIELDS:
                with self.subTest(user=user.login, field=name):
                    self.assertNotIn(name, fields)
        fields = self.env['hr.employee'].with_user(self.hr_officer).fields_get()
        for name in EMPLOYEE_FIELDS:
            self.assertIn(name, fields)


@tagged('post_install', '-at_install')
class TestHrRoles(PersonalInfoCommon):

    def test_hr_roles_write_and_read_employee_fields(self):
        for user in (self.admin, self.hr_manager, self.hr_officer):
            with self.subTest(role=user.login):
                vals = self._values(user.login.upper())
                self.other_emp.with_user(user).write(vals)
                self.assertStored(self.other_emp, vals)
                read = self.other_emp.with_user(user).read(list(EMPLOYEE_FIELDS))[0]
                self.assertEqual(read['identification_id'], vals['identification_id'])
                self.assertEqual(read['private_permanent_state_id'][0], self.state.id)

    def test_hr_officer_cannot_write_other_user_record(self):
        with self.assertRaises(AccessError):
            self.other_user.with_user(self.hr_officer).write({'identification_id': 'HACK'})
        self.assertStored(self.other_emp, {'identification_id': '0010OTHER'})

    def test_admin_writes_user_record(self):
        self.other_user.with_user(self.admin).write({'identification_id': '0010ADMIN', 'cccd_issue_place': 'Admin'})
        self.assertStored(self.other_emp, {'identification_id': '0010ADMIN', 'cccd_issue_place': 'Admin'})


@tagged('post_install', '-at_install')
class TestEmployeeSelfService(PersonalInfoCommon):

    def test_employee_writes_and_reads_own_user_fields(self):
        vals = self._values('SELF', with_birthday=True)
        me = self.emp_user.with_user(self.emp_user)
        me.write(vals)
        self.assertStored(self.emp, vals)
        self.env.invalidate_all()
        read = me.read(list(USER_FIELDS))[0]
        self.assertEqual(read['identification_id'], '0010SELF')
        self.assertEqual(read['cccd_issue_place'], 'Police SELF')
        self.assertEqual(read['private_permanent_country_id'][0], self.country.id)
        self.assertEqual(str(read['birthday']), '1990-05-20')

    def test_employee_cannot_write_own_employee_record(self):
        # self-service goes through res.users only, hr.employee stays HR only
        with self.assertRaises(AccessError):
            self.emp.with_user(self.emp_user).write({'identification_id': 'DIRECT'})

    def test_employee_cannot_write_other_user_fields(self):
        for name, value in self._values('HACK').items():
            with self.subTest(field=name), self.assertRaises(AccessError):
                self.other_user.with_user(self.emp_user).write({name: value})
        self.assertStored(self.other_emp, self._values('OTHER'))

    def test_employee_cannot_read_other_user_fields(self):
        other = self.other_user.with_user(self.emp_user)
        for name in USER_FIELDS:
            with self.subTest(field=name), self.assertRaises(AccessError):
                other.read([name])
            self.env.invalidate_all()

    def test_hr_officer_reads_other_user_fields(self):
        read = self.other_user.with_user(self.hr_officer).read(list(EMPLOYEE_FIELDS))[0]
        self.assertEqual(read['identification_id'], '0010OTHER')
        self.assertEqual(read['cccd_issue_place'], 'Police OTHER')

    def test_employee_cannot_read_or_write_other_employee_fields(self):
        other = self.other_emp.with_user(self.emp_user)
        for name in EMPLOYEE_FIELDS:
            with self.subTest(field=name), self.assertRaises(AccessError):
                other.read([name])
        with self.assertRaises(AccessError):
            other.write({'cccd_issue_place': 'HACK'})
        self.assertStored(self.other_emp, self._values('OTHER'))

    def test_user_without_employee_reads_empty_values(self):
        me = self.no_emp_user.with_user(self.no_emp_user)
        read = me.read(list(USER_FIELDS))[0]
        for name in USER_FIELDS:
            self.assertFalse(read[name], name)


@tagged('post_install', '-at_install')
class TestPortal(PersonalInfoCommon):

    def test_portal_cannot_read_employees(self):
        for model in ('hr.employee', 'hr.employee.public'):
            with self.subTest(model=model), self.assertRaises(AccessError):
                self.env[model].with_user(self.portal_user).search_read([('id', '=', self.other_emp.id)], ['name'])
        with self.assertRaises(AccessError):
            self.other_emp.with_user(self.portal_user).read(['cccd_issue_place'])

    def test_portal_cannot_read_or_write_internal_user_fields(self):
        with self.assertRaises(AccessError):
            self.other_user.with_user(self.portal_user).read(list(EMPLOYEE_FIELDS))
        with self.assertRaises(AccessError):
            self.other_user.with_user(self.portal_user).write({'identification_id': 'HACK'})
        self.assertStored(self.other_emp, {'identification_id': '0010OTHER'})

    def test_portal_own_user_has_no_values(self):
        read = self.portal_user.with_user(self.portal_user).read(list(USER_FIELDS))[0]
        for name in USER_FIELDS:
            self.assertFalse(read[name], name)
