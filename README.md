# odoo-approval-workflow

> Odoo 17 module — Multi-level approval engine for purchase orders, expenses and custom documents.

[![Odoo 17](https://img.shields.io/badge/Odoo-17.0-875A7B?style=flat-square&logo=odoo)](https://www.odoo.com)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)](https://python.org)
[![License: LGPL-3](https://img.shields.io/badge/License-LGPL--3-blue?style=flat-square)](https://www.gnu.org/licenses/lgpl-3.0)

## Features

- **Configurable templates**: define N approval levels per document type (Purchase Order, Expense Sheet)
- **Smart amount routing**: levels automatically selected based on `amount_total` thresholds
- **Flexible approver resolution**: Specific User, User Group, Direct Manager, Purchase Manager
- **Purchase order interception**: overrides `button_confirm()` — orders above threshold block until approved
- **Full audit trail**: `approval.request.line` records every decision with timestamp + comment
- **Delegation**: approver can delegate to another user (configurable per level)
- **Escalation cron**: auto-escalates requests past their deadline
- **Email notifications**: mail template sent to approver at each level
- **Odoo Activities**: creates `mail.mail_activity_data_todo` for each pending approver

## How it works

```
PurchaseOrder.button_confirm()
       │
       ├─→ amount_total < threshold? ──→ confirm immediately
       │
       └─→ amount_total >= threshold?
               │
               ▼
       ApprovalRequest.create() + submit()
               │
               ▼
       Level 0 → email approver → activity created
               │
               ▼ (approver clicks Approve)
       Level 1 → email next approver...
               │
               ▼ (all levels done)
       PurchaseOrder._on_approval_granted()
       → super().button_confirm() → PO confirmed
```

## Technical highlights

| Area | Implementation |
|---|---|
| Model override | `purchase.order.button_confirm()` intercepted with approval gate |
| Dynamic routing | `get_required_levels(amount)` — filters levels by min/max amount |
| Approver resolution | `get_approver_for_record()` — handles user/group/manager/purchase_manager |
| Callback pattern | `_on_approval_granted()` / `_on_approval_refused()` hooks on source model |
| State machine | 5 states: draft → pending → approved/refused/cancelled |
| Wizard | `approval.action.wizard` TransientModel for approve/refuse/delegate |
| Cron | Daily escalation of overdue requests |
| Security | `ir.model.access.csv` — users read-only on templates, write on own requests |

## Author

**Bayane Miguel Singcol** — Odoo Developer  
[GitHub](https://github.com/Bayane-max219) · baymi312@gmail.com
