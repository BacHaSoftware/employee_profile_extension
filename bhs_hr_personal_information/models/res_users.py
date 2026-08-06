from odoo import models, api, fields
import logging
import time

_logger = logging.getLogger(__name__)


class BHSResUsers(models.Model):
    _inherit = 'res.users'

    birthday = fields.Date(related='employee_id.birthday', readonly=False, related_sudo=False)
    ssnid = fields.Char(related='employee_id.ssnid', readonly=False, related_sudo=False)
    identification_id = fields.Char(related='employee_id.identification_id', readonly=False, related_sudo=False)
    private_permanent_street = fields.Char(related='employee_id.private_permanent_street', readonly=False, related_sudo=False)
    private_permanent_street2 = fields.Char(related='employee_id.private_permanent_street2', readonly=False, related_sudo=False)
    private_permanent_city = fields.Char(related='employee_id.private_permanent_city', readonly=False, related_sudo=False)
    private_permanent_state_id = fields.Many2one(
        related='employee_id.private_permanent_state_id', readonly=False, related_sudo=False)
    private_permanent_country_id = fields.Many2one(related='employee_id.private_permanent_country_id', readonly=False, related_sudo=False)
    cccd_issue_date = fields.Date(related='employee_id.cccd_issue_date', readonly=False, related_sudo=False)
    cccd_issue_place = fields.Char(related='employee_id.cccd_issue_place', readonly=False, related_sudo=False)

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + [
            'birthday',
            'ssnid',
            'identification_id',
            'private_permanent_street',
            'private_permanent_street2',
            'private_permanent_city',
            'private_permanent_state_id',
            'private_permanent_country_id',
            'cccd_issue_date',
            'cccd_issue_place',
        ]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + [
            'birthday',
            'ssnid',
            'identification_id',
            'private_permanent_street',
            'private_permanent_street2',
            'private_permanent_city',
            'private_permanent_state_id',
            'private_permanent_country_id',
            'cccd_issue_date',
            'cccd_issue_place',
        ]