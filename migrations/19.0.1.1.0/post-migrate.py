# -*- coding: utf-8 -*-
"""Carry the records created before the module was translated over to English.

WHY A MIGRATION AND NOT A ONE-OFF SCRIPT
Three things do not follow from translating the source, and each fails silently:

  1. `yaguven.commission.target.name` is a STORED computed field. It is built from the
     `MONTHS` selection labels, but it only depends on `salesperson_id`, `year` and
     `month` - none of which change here. Translating the labels leaves the stored value
     untouched, so the list keeps showing `Administrator - Julio 2026` under an otherwise
     English UI. Nothing errors; it just looks like a bug.
  2. The settings record was seeded from `data/commission_config_data.xml`, which now
     carries `noupdate="1"` so that an upgrade stops overwriting the rates Janel may have
     edited. That flag also means the upgrade no longer renames it.
  3. `data/commission_cron.xml` has always had `noupdate="1"`, which protects the
     `nextcall` and `active` the client may have adjusted - and equally blocks the rename.

Living inside the module rather than in a loose script means it runs on the `-u` by
itself, and runs on any future database (a staging rebuild, a second company) without
anyone having to remember it.

Every step is idempotent and guarded by the value it expects to find, so running it twice
changes nothing, and a name the client has already customized is never overwritten.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

VIEJO_PREFIJO = "Comisiones — "
NUEVO_PREFIJO = "Commissions — "
CRON_VIEJO = "Comisiones: recálculo mensual"
CRON_NUEVO = "Commissions: monthly recompute"


def migrate(cr, version):
    if not version:
        return  # fresh install: the XML data already carries the English text

    env = api.Environment(cr, SUPERUSER_ID, {})

    # 1. Settings record. Matched by PREFIX and not by the whole string, because the
    #    default (`_('Comisiones — %s', company.name)`) produces one name per company
    #    while the seed file produces another. A name the client typed does not match
    #    either and is left alone.
    configs = env["yaguven.commission.config"].with_context(active_test=False).search([])
    renombradas = 0
    for cfg in configs:
        if cfg.name and cfg.name.startswith(VIEJO_PREFIJO):
            cfg.name = NUEVO_PREFIJO + cfg.name[len(VIEJO_PREFIJO):]
            renombradas += 1

    # 2. The stored name of every target. `_compute_name` is called outright: `modified()`
    #    would not fire, since no field it depends on has changed - the SELECTION LABELS
    #    changed, and those are not a dependency.
    targets = env["yaguven.commission.target"].with_context(active_test=False).search([])
    if targets:
        targets._compute_name()
        env.flush_all()

    # 3. The cron, which its own `noupdate="1"` keeps the upgrade from touching.
    cron = env.ref("yaguven_darakjian_comisiones.ir_cron_commission_recompute",
                   raise_if_not_found=False)
    cron_ok = False
    if cron and cron.name == CRON_VIEJO:
        cron.name = CRON_NUEVO
        cron_ok = True

    _logger.info(
        "yaguven_darakjian_comisiones -> EN: %d settings renamed, %d target names "
        "recomputed, cron renamed: %s", renombradas, len(targets), cron_ok)
