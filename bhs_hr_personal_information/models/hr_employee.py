from odoo import models, fields, api, _
from datetime import timedelta, datetime
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class BHSHrEmployee(models.Model):
    _inherit = 'hr.employee'

    identification_id = fields.Char(string ='Citizen ID Number')
    private_permanent_street = fields.Char(string="Private Permanent Street", groups="hr.group_hr_user", tracking=True)
    private_permanent_street2 = fields.Char(string="Private Permanent Street2", groups="hr.group_hr_user", tracking=True)
    private_permanent_city = fields.Char(string="Private Permanent City", groups="hr.group_hr_user", tracking=True)
    private_permanent_state_id = fields.Many2one(
        "res.country.state", string="Private Permanent State",
        domain="[('id', 'in', allowed_country_state_ids)]",
        groups="hr.group_hr_user", tracking=True)
    private_permanent_country_id = fields.Many2one("res.country", string="Private Country",
                                         groups="hr.group_hr_user", tracking=True)
    cccd_issue_date = fields.Date(string="Issue Date")
    cccd_issue_place = fields.Char(string="Place of Issue")