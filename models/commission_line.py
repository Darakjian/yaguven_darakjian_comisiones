from odoo import api, fields, models


class YaguvenCommissionLine(models.Model):
    """One commission line per invoice, for the salesperson, within the month.

    One line per document (invoice or credit note) issued by the salesperson inside the
    ``target`` period. The ``volume`` and ``cost_total`` snapshots are frozen when the
    line is created by the recompute engine in ``yaguven.commission.target``, while
    ``pct_applied`` and the collection state are refreshed on every recompute — and the
    commission amounts follow from those.
    """

    _name = 'yaguven.commission.line'
    _description = 'Darakjian — Commission Line'
    _order = 'target_id, invoice_date, move_id'

    target_id = fields.Many2one(
        'yaguven.commission.target',
        required=True,
        index=True,
        ondelete='cascade',
    )
    salesperson_id = fields.Many2one(
        related='target_id.salesperson_id',
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        related='target_id.company_id',
        store=True,
        index=True,
    )
    currency_id = fields.Many2one(
        related='company_id.currency_id',
        store=True,
    )

    # --- Source invoice (native datasource, read only) ---
    move_id = fields.Many2one(
        'account.move',
        string='Invoice',
        required=True,
        index=True,
        ondelete='cascade',
    )
    move_name = fields.Char(related='move_id.name', string='Number')
    invoice_date = fields.Date(related='move_id.invoice_date', store=True)
    move_type = fields.Selection(related='move_id.move_type')

    # --- Snapshots frozen as of the invoice date ---
    volume = fields.Monetary(
        currency_field='currency_id',
        help='Attributed net billed, signed: credit notes subtract.',
    )
    cost_total = fields.Monetary(
        currency_field='currency_id',
        help='Total cost of the product lines, frozen as of the invoice date.',
    )
    margin = fields.Monetary(
        currency_field='currency_id',
        compute='_compute_margin',
        store=True,
        help='Margin = net billed − cost. The commission base.',
    )

    # --- Tier and commission ---
    pct_applied = fields.Float(
        string='Rate Applied',
        digits=(5, 2),
        help='Rate of the tier the month volume reached (cliff, not marginal).',
    )
    commission_amount = fields.Monetary(
        string='Commission Earned',
        currency_field='currency_id',
        compute='_compute_commission_amount',
        store=True,
    )

    # --- Cobro (criterio percibido) ---
    is_collected = fields.Boolean(
        string='Collected',
        help='The source invoice has been collected (payment_state paid/in_payment).',
    )
    commission_payable = fields.Monetary(
        string='Commission Payable',
        currency_field='currency_id',
        compute='_compute_commission_payable',
        store=True,
        help='Commission that can already be paid out: earned, but only once the invoice is collected.',
    )

    _sql_constraints = [
        (
            'target_move_uniq',
            'unique(target_id, move_id)',
            'A commission line already exists for this invoice in this period.',
        ),
    ]

    @api.depends('volume', 'cost_total')
    def _compute_margin(self):
        for rec in self:
            rec.margin = rec.volume - rec.cost_total

    @api.depends('margin', 'pct_applied')
    def _compute_commission_amount(self):
        for rec in self:
            rec.commission_amount = rec.margin * rec.pct_applied / 100.0

    @api.depends('commission_amount', 'is_collected')
    def _compute_commission_payable(self):
        for rec in self:
            rec.commission_payable = rec.commission_amount if rec.is_collected else 0.0
