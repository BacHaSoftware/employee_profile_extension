# -*- coding: utf-8 -*-
"""Database update 19 -> 20: migrations/20.0.1.0.0/post-migrate.py copies the 19 module column
hr_employee.identification_id into hr_version.identification_id (core field, every version of the employee)."""
import importlib.util
from datetime import date

from odoo.tests import tagged
from odoo.tools.misc import file_path
from odoo.tools.sql import column_exists

from .common import MODULE, PersonalInfoCommon

SCRIPT = f'{MODULE}/migrations/20.0.1.0.0/post-migrate.py'


def _load_script():
    spec = importlib.util.spec_from_file_location('bhs_hpi_post_migrate', file_path(SCRIPT))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@tagged('post_install', '-at_install')
class TestMigration(PersonalInfoCommon):

    def setUp(self):
        super().setUp()
        self.script = _load_script()
        self.legacy = self.env['hr.employee'].create({'name': 'HPI Legacy', 'date_version': date(2020, 1, 1)})
        self.first_version = self.legacy.version_id
        self.second_version = self.env['hr.version'].create({
            'employee_id': self.legacy.id, 'date_version': date(2024, 1, 1),
        })
        self.conflict = self.env['hr.employee'].create({'name': 'HPI Conflict', 'identification_id': 'CORE-VALUE'})
        self.empty = self.env['hr.employee'].create({'name': 'HPI Empty', 'identification_id': 'KEEP-ME'})
        self.env.flush_all()

    def _seed_legacy_column(self, values):
        # DDL is transactional in PostgreSQL: rolled back with the test
        if not column_exists(self.env.cr, 'hr_employee', 'identification_id'):
            self.env.cr.execute("ALTER TABLE hr_employee ADD COLUMN identification_id varchar")
        for employee, value in values.items():
            self.env.cr.execute("UPDATE hr_employee SET identification_id = %s WHERE id = %s", [value, employee.id])

    def _version_values(self, employee):
        self.env.cr.execute("SELECT id, identification_id FROM hr_version WHERE employee_id = %s ORDER BY id",
                            [employee.id])
        return dict(self.env.cr.fetchall())

    def test_copy_into_every_version(self):
        self._seed_legacy_column({self.legacy: '0019LEGACY', self.empty: ''})
        with self.assertLogs('odoo.addons.' + MODULE, level='INFO') as logs:
            self.script.migrate(self.env.cr, '19.0.1.0')
        values = self._version_values(self.legacy)
        self.assertEqual(set(values), {self.first_version.id, self.second_version.id})
        self.assertEqual(set(values.values()), {'0019LEGACY'})
        # empty module value: the core value is left alone
        self.assertEqual(set(self._version_values(self.empty).values()), {'KEEP-ME'})
        self.assertTrue(any('copied' in line for line in logs.output))
        self.env.invalidate_all()
        self.assertEqual(self.legacy.identification_id, '0019LEGACY')

    def test_module_value_wins_over_different_core_value(self):
        self._seed_legacy_column({self.conflict: '0019MODULE'})
        with self.assertLogs('odoo.addons.' + MODULE, level='WARNING') as logs:
            self.script.migrate(self.env.cr, '19.0.1.0')
        self.assertEqual(set(self._version_values(self.conflict).values()), {'0019MODULE'})
        self.assertTrue(any(str(self.conflict.id) in line for line in logs.output))
        self.assertFalse(any('CORE-VALUE' in line or '0019MODULE' in line for line in logs.output),
                         "identification numbers must not be written to the log")

    def test_blank_module_value_keeps_core_value(self):
        self._seed_legacy_column({self.conflict: '  '})
        self.script.migrate(self.env.cr, '19.0.1.0')
        self.assertEqual(set(self._version_values(self.conflict).values()), {'CORE-VALUE'})

    def test_missing_module_value_with_core_value_is_logged(self):
        for module_value in (None, '', ' '):
            with self.subTest(module_value=module_value):
                self._seed_legacy_column({self.conflict: module_value})
                with self.assertLogs('odoo.addons.' + MODULE, level='WARNING') as logs:
                    self.script.migrate(self.env.cr, '19.0.1.0')
                versions = self._version_values(self.conflict)
                self.assertEqual(set(versions.values()), {'CORE-VALUE'})
                lines = [line for line in logs.output if 'hidden in 19' in line]
                expected = f"employee {self.conflict.id}, version(s) {sorted(versions)}"
                self.assertTrue(any(expected in line for line in lines), logs.output)
                self.assertFalse(any('CORE-VALUE' in line for line in logs.output),
                                 "identification numbers must not be written to the log")

    def test_idempotent(self):
        self._seed_legacy_column({self.legacy: '0019LEGACY', self.conflict: '0019MODULE'})
        self.script.migrate(self.env.cr, '19.0.1.0')
        before = {**self._version_values(self.legacy), **self._version_values(self.conflict)}
        with self.assertLogs('odoo.addons.' + MODULE, level='INFO') as logs:
            self.script.migrate(self.env.cr, '19.0.1.0')
        after = {**self._version_values(self.legacy), **self._version_values(self.conflict)}
        self.assertEqual(before, after)
        self.assertTrue(any('0 version(s)' in line for line in logs.output))
        # no replacement left on the second run (core-only values of other employees are still reported)
        self.assertFalse(any('replaced' in line for line in logs.output))

    def test_without_legacy_column_nothing_changes(self):
        if column_exists(self.env.cr, 'hr_employee', 'identification_id'):
            self.env.cr.execute("ALTER TABLE hr_employee DROP COLUMN identification_id")
        before = self._version_values(self.conflict)
        with self.assertLogs('odoo.addons.' + MODULE, level='INFO') as logs:
            self.script.migrate(self.env.cr, '19.0.1.0')
        self.assertTrue(any('nothing to copy' in line for line in logs.output))
        self.assertEqual(self._version_values(self.conflict), before)
