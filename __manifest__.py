{
    'name': 'Approval Workflow Engine',
    'version': '17.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Multi-level approval matrix for purchase orders, expenses and custom documents',
    'description': """
Approval Workflow Engine
========================
A configurable multi-level approval engine for Odoo 17.
Define approval matrices based on amount thresholds, departments, or product categories.

Key Features:
- Approval templates: define N levels with approver rules (user, group, manager)
- Amount-based routing: auto-select approval level based on order total
- Works with purchase.order, hr.expense.sheet, and custom models
- Email notifications at each approval step
- Full audit trail with timestamps and comments
- Delegation: approver can delegate to another user
- Escalation: auto-escalate after configurable timeout
- Mobile-friendly approval interface
    """,
    'author': 'Bayane Miguel Singcol',
    'website': 'https://github.com/Bayane-max219/odoo-approval-workflow',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'purchase',
        'hr_expense',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'data/approval_cron.xml',
        'views/approval_template_views.xml',
        'views/approval_request_views.xml',
        'views/purchase_order_views.xml',
        'views/menu.xml',
        'wizards/approval_action_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
}
