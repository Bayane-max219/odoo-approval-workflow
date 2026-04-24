from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    approval_request_id = fields.Many2one(
        'approval.request',
        string='Approval Request',
        readonly=True,
        copy=False,
    )
    approval_state = fields.Selection([
        ('not_required', 'Not Required'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
    ], default='not_required', readonly=True, copy=False, tracking=True)
    requires_approval = fields.Boolean(
        compute='_compute_requires_approval',
        store=True,
    )

    @api.depends('amount_total', 'company_id')
    def _compute_requires_approval(self):
        for order in self:
            template = order._find_approval_template()
            order.requires_approval = bool(
                template and template.get_required_levels(order.amount_total)
            )

    def _find_approval_template(self):
        """Find the most specific approval template for purchase.order."""
        return self.env['approval.template'].search([
            ('model_name', '=', 'purchase.order'),
            ('active', '=', True),
        ], limit=1, order='id desc')

    def button_confirm(self):
        """Override to intercept and require approval when needed."""
        for order in self:
            template = order._find_approval_template()
            if template and template.get_required_levels(order.amount_total):
                if order.approval_state not in ('approved',):
                    order._create_approval_request(template)
                    order.write({'approval_state': 'pending'})
                    continue
            super(PurchaseOrder, order).button_confirm()

    def _create_approval_request(self, template):
        self.ensure_one()
        request = self.env['approval.request'].create({
            'template_id': template.id,
            'res_model': self._name,
            'res_id': self.id,
            'res_name': self.name,
        })
        request.action_submit()
        self.approval_request_id = request
        self.message_post(
            body=_('Approval request %s created. Waiting for approval before confirmation.') % request.name,
            message_type='notification',
        )

    def _on_approval_granted(self):
        """Called by ApprovalRequest when fully approved."""
        self.write({'approval_state': 'approved'})
        super(PurchaseOrder, self).button_confirm()

    def _on_approval_refused(self):
        """Called by ApprovalRequest when refused."""
        self.write({'approval_state': 'refused'})
        self.message_post(
            body=_('Purchase order refused by approver.'),
            message_type='notification',
        )
