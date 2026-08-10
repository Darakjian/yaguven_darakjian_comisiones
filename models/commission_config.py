from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class YaguvenCommissionConfig(models.Model):
    """Configuración de tramos de comisión (company-level).

    Guarda los porcentajes fijos y el corte del tramo superior. Gabriel definió
    3/6/9 y el corte en 125%; viven como configuración (editable) para no cablear
    los números en código, pero Janel no los toca: solo carga el objetivo mensual
    en ``yaguven.commission.target``.
    """

    _name = 'yaguven.commission.config'
    _description = 'Darakjian — Commission Settings'
    _inherit = ['mail.thread']
    _order = 'company_id, id'

    name = fields.Char(
        required=True,
        default=lambda self: _('Commissions — %s', self.env.company.name),
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        required=True,
        index=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)

    pct_below = fields.Float(
        string='% Below Target',
        digits=(5, 2),
        default=3.0,
        required=True,
        help='Rate applied when the month volume falls short of the target.',
        tracking=True,
    )
    pct_target = fields.Float(
        string='% At Target',
        digits=(5, 2),
        default=6.0,
        required=True,
        help='Rate applied when the volume reaches the target but stays below '
             'llega al corte superior.',
        tracking=True,
    )
    pct_super = fields.Float(
        string='% Above Target',
        digits=(5, 2),
        default=9.0,
        required=True,
        help='Rate applied when the volume reaches or passes the upper '
             'cut-off (target x threshold).',
        tracking=True,
    )
    super_threshold_pct = fields.Float(
        string='Upper Tier Threshold (%)',
        digits=(5, 2),
        default=125.0,
        required=True,
        help='Percentage of the target at which the upper rate starts to apply. '
             'E.g. 125 => the upper tier starts at 1.25 x target.',
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains('pct_below', 'pct_target', 'pct_super')
    def _check_percentages(self):
        for rec in self:
            for value in (rec.pct_below, rec.pct_target, rec.pct_super):
                if value < 0 or value > 100:
                    raise ValidationError(_('Rates must be between 0 and 100.'))

    @api.constrains('super_threshold_pct')
    def _check_threshold(self):
        for rec in self:
            if rec.super_threshold_pct < 100:
                raise ValidationError(_(
                    'The upper tier threshold cannot be lower than 100%% '
                    '(the upper tier starts at the target or above).'
                ))

    @api.constrains('company_id', 'active')
    def _check_single_active_per_company(self):
        for rec in self:
            if not rec.active:
                continue
            others = self.search_count([
                ('company_id', '=', rec.company_id.id),
                ('active', '=', True),
                ('id', '!=', rec.id),
            ])
            if others:
                raise ValidationError(_(
                    'Active commission settings already exist for company '
                    '"%s". Archive the existing one before creating another.'
                ) % rec.company_id.name)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @api.model
    def _get_for_company(self, company):
        """Devuelve la config activa de la compañía; la crea con defaults si no hay."""
        company = company or self.env.company
        config = self.search([
            ('company_id', '=', company.id),
            ('active', '=', True),
        ], limit=1)
        if not config:
            config = self.sudo().create({
                'name': _('Commissions — %s', company.name),
                'company_id': company.id,
            })
        return config

    def _resolve_tier(self, volume, objective):
        """Resuelve el tramo y el % según el volumen del mes contra el objetivo.

        Efecto "cliff": el % aplica sobre el total, no por tramos marginales.
        Devuelve (tier, pct) con tier in ('below', 'target', 'super').
        Si el objetivo no es positivo (aún no cargado), se asume 'below'.
        """
        self.ensure_one()
        if not objective or objective <= 0:
            return 'below', self.pct_below
        super_amount = objective * self.super_threshold_pct / 100.0
        if volume >= super_amount:
            return 'super', self.pct_super
        if volume >= objective:
            return 'target', self.pct_target
        return 'below', self.pct_below
