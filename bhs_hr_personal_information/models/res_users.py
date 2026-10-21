from odoo import fields, models

from odoo.addons.hr.models.res_users import related_employee_field


class BHSResUsers(models.Model):
    _inherit = 'res.users'

    # Simulated related fields "employee_id.<name>" (core hr): the current user reads and writes his own employee
    # (user_writeable), other users go through the normal access rights. birthday is a core field since Odoo 20.
    identification_id = fields.Char(
        **related_employee_field('identification_id', string="Citizen ID Number"), user_writeable=True)
    private_permanent_street = fields.Char(**related_employee_field('private_permanent_street'), user_writeable=True)
    private_permanent_street2 = fields.Char(**related_employee_field('private_permanent_street2'), user_writeable=True)
    private_permanent_city = fields.Char(**related_employee_field('private_permanent_city'), user_writeable=True)
    private_permanent_state_id = fields.Many2one(
        'res.country.state',
        domain="[('country_id', '=?', private_permanent_country_id)]",
        **related_employee_field('private_permanent_state_id'),
        user_writeable=True,
    )
    private_permanent_country_id = fields.Many2one(
        'res.country', **related_employee_field('private_permanent_country_id'), user_writeable=True)
    cccd_issue_date = fields.Date(**related_employee_field('cccd_issue_date'), user_writeable=True)
    cccd_issue_place = fields.Char(**related_employee_field('cccd_issue_place'), user_writeable=True)
