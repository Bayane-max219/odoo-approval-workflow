from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ApprovalActionWizard(models.TransientModel):
    _name = 'approval.action.wizard'
    _description = 'Approve or Refuse Request'

    request_id = fields.Many2one('approval.request', required=True, readonly=True)
    action = fields.Selection([
        ('approve', 'Approve'),
        ('refuse', 'Refuse'),
        ('delegate', 'Delegate'),
    ], required=True, default='approve')
    comment = fields.Text(string='Comment / Reason')
    delegate_to_id = fields.Many2one(
        'res.users',
        string='Delegate To',
        domain=[('share', '=', False)],
    )

    def action_confirm(self):
        self.ensure_one()
        if self.action == 'approve':
            self.request_id.action_approve(comment=self.comment or '')
        elif self.action == 'refuse':
            if not self.comment:
                raise UserError(_('A reason is required when refusing an approval request.'))
            self.request_id.action_refuse(comment=self.comment)
        elif self.action == 'delegate':
            if not self.delegate_to_id:
                raise UserError(_('Please select a user to delegate to.'))
            if not self.request_id.current_level_can_delegate():
                raise UserError(_('Delegation is not allowed at this approval level.'))
            self.request_id._record_decision('delegated', self.comment or '')
            self.request_id.write({
                'current_approver_id': self.delegate_to_id.id,
            })
            self.request_id._notify_current_approver()
        return {'type': 'ir.actions.act_window_close'}
