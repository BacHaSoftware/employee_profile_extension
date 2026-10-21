from odoo import fields, models


class BHSHrVersion(models.Model):
    _inherit = 'hr.version'

    # Label set on the field, not in a view: other modules may replace the identification_id node of the
    # employee form (e.g. Open HRMS hr_employee_updation), which drops a view-level string.
    identification_id = fields.Char(string="Citizen ID Number")


class BHSHrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Odoo 20: the Citizen ID number is the core field hr.version.identification_id, filled by migrations/20.0.1.0.0
    private_permanent_street = fields.Char(string="Private Permanent Street", groups="hr.group_hr_user", tracking=True)
    private_permanent_street2 = fields.Char(string="Private Permanent Street2", groups="hr.group_hr_user", tracking=True)
    private_permanent_city = fields.Char(string="Private Permanent City", groups="hr.group_hr_user", tracking=True)
    private_permanent_state_id = fields.Many2one(
        "res.country.state", string="Private Permanent State",
        domain="[('id', 'in', allowed_country_state_ids)]",
        groups="hr.group_hr_user", tracking=True)
    private_permanent_country_id = fields.Many2one("res.country", string="Permanent Country",
                                         groups="hr.group_hr_user", tracking=True)
    cccd_issue_date = fields.Date(string="Issue Date", groups="hr.group_hr_user")
    cccd_issue_place = fields.Char(string="Place of Issue", groups="hr.group_hr_user")
