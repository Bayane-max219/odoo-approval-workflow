from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class ApprovalTemplate(models.Model):
    """
    Defines an approval workflow: which model, how many levels,
    amount thresholds and approver rules per level.
    """
    _name = 'approval.template'
    _description = 'Approval Template'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(required=True, translate=True, tracking=True)
    active = fields.Boolean(default=True)
    model_id = fields.Many2one(
        'ir.model',
        string='Target Model',
        required=True,
        domain=[('model', 'in', ['purchase.order', 'hr.expense.sheet'])],
        ondelete='cascade',
        tracking=True,
    )
    model_name = fields.Char(related='model_id.model', store=True)
    amount_field = fields.Char(
        string='Amount Field',
        default='amount_total',
        help='Technical name of the monetary field used for threshold routing.',
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )
    level_ids = fields.One2many(
        'approval.template.level',
        'template_id',
        string='Approval Levels',
        copy=True,
    )
    escalation_days = fields.Integer(
        default=3,
        string='Escalation After (Days)',
        help='Automatically escalate pending approvals after N days of inactivity.',
    )
    description = fields.Html(translate=True)

    request_count = fields.Integer(compute='_compute_request_count')

    def _compute_request_count(self):
        for tmpl in self:
            tmpl.request_count = self.env['approval.request'].search_count([
                ('template_id', '=', tmpl.id)
            ])

    @api.constrains('level_ids')
    def _check_levels(self):
        for tmpl in self:
            if tmpl.level_ids:
                sequences = tmpl.level_ids.mapped('sequence')
                if len(sequences) != len(set(sequences)):
                    raise ValidationError(_('Approval levels must have unique sequence numbers.'))

    def get_required_levels(self, amount):
        """
        Return the approval levels applicable for a given amount.
        Levels with min_amount <= amount < max_amount (or no max) are included.
        """
        self.ensure_one()
        applicable = self.level_ids.filtered(
            lambda l: (not l.min_amount or l.min_amount <= amount)
            and (not l.max_amount or l.max_amount > amount)
        ).sorted('sequence')
        return applicable

    def action_view_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Approval Requests'),
            'res_model': 'approval.request',
            'view_mode': 'list,form',
            'domain': [('template_id', '=', self.id)],
        }
