{
    'name': 'Darakjian — Commissions',
    'summary': 'Salesperson commissions: one cliff rate per tier on the margin, paid when collected.',
    'description': """
Commissions for Darakjian Jewelers.

Business rules (set by Ara, clarified by Gabriel on 2026-07-08):

- A monthly sales volume target in USD, set by Janel for each salesperson.
- One rate per tier applied to the TOTAL — a "cliff", NOT marginal:
    * sales < target                      -> 3%
    * target <= sales < 125% of target    -> 6%
    * sales >= 125% of target             -> 9%
- The rate applies to the MARGIN (price - cost), not to the billed amount.
- Paid when COLLECTED: a commission becomes payable once the invoice is paid.
- Computed MONTHLY, per INDIVIDUAL salesperson.

Non-invasive by design: it reads the native models (account.move, account.move.line,
account.payment) as a read-only datasource and writes only to its own models
(yaguven.commission.*). It neither depends on nor inherits from Odoo's own commission
module (sale_commission).
""",
    'author': 'Yagüven C.G.',
    'maintainer': 'Yagüven C.G.',
    'category': 'Sales/Commissions',
    'version': '19.0.1.1.0',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'account',
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/commission_config_data.xml',
        'data/commission_cron.xml',
        'views/commission_config_views.xml',
        'views/commission_target_views.xml',
        'views/commission_line_views.xml',
        'views/menu.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
