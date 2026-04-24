from odoo import api, fields, models


class ApprovalTemplateLevel(models.Model):
    _name = 'approval.template.level'
    _description = 'Approval Level'
    _order = 'template_id, sequence'

    template_id = fields.Many2one(
        'approval.template', required=True, ondelete='cascade'
    )
    sequence = fields.Integer(default=10, required=True)
    name = fields.Char(required=True, translate=True)
    approver_type = fields.Selection([
        ('user', 'Specific User'),
        ('group', 'User Group'),
        ('manager', 'Direct Manager'),
        ('purchase_manager', 'Purchase Manager'),
    ], required=True, default='user')
    approver_user_id = fields.Many2one(
        'res.users',
        string='Approver',
        domain=[('share', '=', False)],
    )
    approver_group_id = fields.Many2one(
        'res.groups',
        string='Approver Group',
    )
    min_amount = fields.Monetary(
        currency_field='currency_id',
        string='Min Amount',
        help='This level applies when the document amount >= this value.',
    )
    max_amount = fields.Monetary(
        currency_field='currency_id',
        string='Max Amount (excl.)',
        help='This level applies when the document amount < this value. Leave empty for no upper bound.',
    )
    currency_id = fields.Many2one(related='template_id.currency_id', store=True)
    can_delegate = fields.Boolean(
        string='Allow Delegation',
        default=True,
    )
    required = fields.Boolean(
        string='Mandatory',
        default=True,
        help='If unchecked, this level can be skipped.',
    )

    def get_approver_for_record(self, record):
        """Resolve the actual approver user for a given document record."""
        self.ensure_one()
        if self.approver_type == 'user':
            return self.approver_user_id
        elif self.approver_type == 'manager':
            if hasattr(record, 'user_id') and record.user_id.employee_id:
                parent = record.user_id.employee_id.parent_id
                return parent.user_id if parent else self.env['res.users']
            return self.env['res.users']
        elif self.approver_type == 'purchase_manager':
            group = self.env.ref('purchase.group_purchase_manager', raise_if_not_found=False)
            if group:
                return group.users[:1]
            return self.env['res.users']
        elif self.approver_type == 'group':
            return self.approver_group_id.users[:1]
        return self.env['res.users']
