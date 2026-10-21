"""Database update 19.0.1.0 -> 20.0.1.0.0 (idempotent).

Odoo 19: the module re-declared hr.employee.identification_id (Citizen ID Number) as its own column
hr_employee.identification_id, next to the core field hr.version.identification_id. Odoo 20: the module uses the
core versioned field. Every non-blank module value is copied into all versions of the employee; when a version holds
a different non-empty core value, the module value wins and the replacement is logged (record ids only, never the
numbers). A blank module value (NULL, '' or whitespace) is treated as empty: the core value is kept, and when the
core value is non-empty (hidden by the module in 19, shown in 20) it is logged (record ids only). The old column is
left in place (the ORM no longer reads it).
"""
import logging

from odoo.tools.sql import column_exists

_logger = logging.getLogger('odoo.addons.bhs_hr_personal_information.migrations')

_HAS_MODULE_VALUE = "btrim(e.identification_id) <> ''"
_HAS_CORE_VALUE = "btrim(v.identification_id) <> ''"


def _log_conflicts(cr):
    cr.execute(f"""
        SELECT v.employee_id, array_agg(v.id ORDER BY v.id)
          FROM hr_version v
          JOIN hr_employee e ON e.id = v.employee_id
         WHERE {_HAS_MODULE_VALUE}
           AND {_HAS_CORE_VALUE}
           AND v.identification_id <> e.identification_id
         GROUP BY v.employee_id
         ORDER BY v.employee_id
    """)
    for employee_id, version_ids in cr.fetchall():
        _logger.warning("bhs_hr_personal_information: employee %s, version(s) %s: different core identification "
                        "number replaced by the module value", employee_id, version_ids)


def _log_hidden_core_values(cr):
    cr.execute(f"""
        SELECT v.employee_id, array_agg(v.id ORDER BY v.id)
          FROM hr_version v
          JOIN hr_employee e ON e.id = v.employee_id
         WHERE NOT coalesce({_HAS_MODULE_VALUE}, false)
           AND {_HAS_CORE_VALUE}
         GROUP BY v.employee_id
         ORDER BY v.employee_id
    """)
    for employee_id, version_ids in cr.fetchall():
        _logger.warning("bhs_hr_personal_information: employee %s, version(s) %s: no module identification number, "
                        "the core value (hidden in 19) is now shown", employee_id, version_ids)


def migrate(cr, version):
    if not column_exists(cr, 'hr_employee', 'identification_id'):
        _logger.info("bhs_hr_personal_information: no hr_employee.identification_id column, nothing to copy")
        return
    _log_conflicts(cr)
    _log_hidden_core_values(cr)
    cr.execute(f"""
        UPDATE hr_version v
           SET identification_id = e.identification_id
          FROM hr_employee e
         WHERE e.id = v.employee_id
           AND {_HAS_MODULE_VALUE}
           AND v.identification_id IS DISTINCT FROM e.identification_id
    """)
    _logger.info("bhs_hr_personal_information: identification number copied into %s version(s)", cr.rowcount)
