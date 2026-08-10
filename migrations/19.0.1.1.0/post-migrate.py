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

OLD_PREFIX = "Comisiones — "
NEW_PREFIX = "Commissions — "
OLD_CRON = "Comisiones: recálculo mensual"
NEW_CRON = "Commissions: monthly recompute"


def migrate(cr, version):
    if not version:
        return  # fresh install: the XML data already carries the English text

    # `tracking_disable`: renaming a tracked field posts a chatter entry reading
    # "Comisiones — Darakjian -> Commissions — Darakjian". That entry documents nothing
    # about the client's business — it documents OUR maintenance run — and it puts the
    # very Spanish we are removing back on the screen the client opens every day.
    env = api.Environment(cr, SUPERUSER_ID, {"tracking_disable": True})

    # 1. Settings record. Matched by PREFIX and not by the whole string, because the
    #    default (`_('Comisiones — %s', company.name)`) produces one name per company
    #    while the seed file produces another. A name the client typed does not match
    #    either and is left alone.
    configs = env["yaguven.commission.config"].with_context(active_test=False).search([])
    renamed = 0
    for cfg in configs:
        if cfg.name and cfg.name.startswith(OLD_PREFIX):
            cfg.name = NEW_PREFIX + cfg.name[len(OLD_PREFIX):]
            renamed += 1

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
    cron_renamed = False
    if cron and cron.name == OLD_CRON:
        cron.name = NEW_CRON
        cron_renamed = True

    _logger.info(
        "yaguven_darakjian_comisiones -> EN: %d settings renamed, %d target names "
        "recomputed, cron renamed: %s", renamed, len(targets), cron_renamed)
