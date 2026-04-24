from datetime import date
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ApprovalRequest(models.Model):
    """
    One approval request = one document going through the workflow.
    Tracks current level, all decisions, deadlines.
    """
    _name = 'approval.request'
    _description = 'Approval Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        required=True,
        copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('approval.request'),
    )
    template_id = fields.Many2one(
        'approval.template', required=True, ondelete='restrict'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True, copy=False)

    requester_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
    )
    current_level = fields.Integer(
        string='Current Approval Level',
        default=0,
        copy=False,
    )
    current_approver_id = fields.Many2one(
        'res.users',
        string='Current Approver',
        compute='_compute_current_approver',
        store=True,
    )
    deadline = fields.Date(
        string='Response Deadline',
        compute='_compute_deadline',
        store=True,
    )

    # Reference to the originating document (generic)
    res_model = fields.Char(string='Document Model')
    res_id = fields.Integer(string='Document ID')
    res_name = fields.Char(string='Document Reference')

    line_ids = fields.One2many(
        'approval.request.line', 'request_id', string='Decisions'
    )
    total_levels = fields.Integer(
        compute='_compute_total_levels', store=True
    )
    progress = fields.Integer(
        string='Progress (%)',
        compute='_compute_progress',
        store=True,
    )

    @api.depends('template_id', 'line_ids')
    def _compute_total_levels(self):
        for req in self:
            req.total_levels = len(req.template_id.level_ids)

    @api.depends('current_level', 'total_levels')
    def _compute_progress(self):
        for req in self:
            if req.total_levels:
                req.progress = int((req.current_level / req.total_levels) * 100)
            else:
                req.progress = 0

    @api.depends('current_level', 'template_id.level_ids')
    def _compute_current_approver(self):
        for req in self:
            level = req._get_current_level_record()
            if level:
                record = req._get_source_record()
                req.current_approver_id = level.get_approver_for_record(record) if record else level.approver_user_id
            else:
                req.current_approver_id = False

    @api.depends('create_date', 'template_id.escalation_days')
    def _compute_deadline(self):
        for req in self:
            if req.create_date and req.template_id.escalation_days:
                from datetime import timedelta
                req.deadline = (req.create_date + timedelta(days=req.template_id.escalation_days)).date()
            else:
                req.deadline = False

    def _get_current_level_record(self):
        self.ensure_one()
        levels = self.template_id.level_ids.sorted('sequence')
        idx = self.current_level
        if 0 <= idx < len(levels):
            return levels[idx]
        return None

    def _get_source_record(self):
        self.ensure_one()
        if self.res_model and self.res_id:
            return self.env[self.res_model].browse(self.res_id)
        return None

    def action_submit(self):
        for req in self:
            if req.state != 'draft':
                raise UserError(_('Only draft requests can be submitted.'))
            req.write({'state': 'pending', 'current_level': 0})
            req._notify_current_approver()

    def action_approve(self, comment=''):
        for req in self:
            if req.state != 'pending':
                raise UserError(_('This request is not pending approval.'))
            if req.current_approver_id and req.current_approver_id != self.env.user:
                raise UserError(_('You are not the designated approver for this level.'))
            req._record_decision('approved', comment)
            req._advance_or_complete()

    def action_refuse(self, comment=''):
        for req in self:
            req._record_decision('refused', comment)
            req.write({'state': 'refused'})
            req._on_refused()

    def _record_decision(self, decision, comment):
        self.ensure_one()
        level = self._get_current_level_record()
        self.env['approval.request.line'].create({
            'request_id': self.id,
            'level_id': level.id if level else False,
            'level_sequence': self.current_level,
            'approver_id': self.env.user.id,
            'decision': decision,
            'comment': comment,
            'decision_date': fields.Datetime.now(),
        })

    def _advance_or_complete(self):
        self.ensure_one()
        next_level = self.current_level + 1
        if next_level >= len(self.template_id.level_ids):
            self.write({'state': 'approved', 'current_level': next_level})
            self._on_approved()
        else:
            self.write({'current_level': next_level})
            self._notify_current_approver()

    def _notify_current_approver(self):
        self.ensure_one()
        approver = self.current_approver_id
        if not approver:
            return
        template = self.env.ref(
            'odoo_approval_workflow.mail_template_approval_request',
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=approver.id,
            note=_('Please review and approve/refuse this request: %s') % self.name,
        )

    def _on_approved(self):
        self.ensure_one()
        source = self._get_source_record()
        if source and hasattr(source, '_on_approval_granted'):
            source._on_approval_granted()
        self.message_post(
            body=_('Request fully approved. All %d levels completed.') % self.total_levels,
            message_type='notification',
        )

    def _on_refused(self):
        self.ensure_one()
        source = self._get_source_record()
        if source and hasattr(source, '_on_approval_refused'):
            source._on_approval_refused()

    @api.model
    def _cron_escalate_pending(self):
        """Escalate requests that exceeded their deadline without response."""
        today = date.today()
        pending = self.search([
            ('state', '=', 'pending'),
            ('deadline', '<', today),
        ])
        for req in pending:
            req.message_post(
                body=_('Approval deadline passed. Escalating to manager.'),
                message_type='notification',
            )
