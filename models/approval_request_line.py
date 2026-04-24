from odoo import fields, models


class ApprovalRequestLine(models.Model):
    _name = 'approval.request.line'
    _description = 'Approval Decision'
    _order = 'decision_date'

    request_id = fields.Many2one(
        'approval.request', required=True, ondelete='cascade', index=True
    )
    level_id = fields.Many2one('approval.template.level', ondelete='set null')
    level_sequence = fields.Integer(string='Level')
    approver_id = fields.Many2one('res.users', required=True, readonly=True)
    decision = fields.Selection([
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('delegated', 'Delegated'),
    ], required=True)
    comment = fields.Text()
    decision_date = fields.Datetime(readonly=True)
    delegated_to_id = fields.Many2one('res.users', string='Delegated To')
