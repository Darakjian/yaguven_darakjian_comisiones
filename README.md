# yaguven_darakjian_comisiones

Odoo 19 module — **salesperson commissions** for Darakjian Jewelers.

Business rules (set by Ara, clarified by Gabriel on 2026-07-08):

- A **monthly sales volume goal** in USD, set by Janel month by month for each salesperson.
- **One rate per tier, applied to the whole total** (a *cliff*, not marginal):
  - sales `< goal` → **3%**
  - `goal ≤ sales < 125% of goal` → **6%**
  - `sales ≥ 125% of goal` → **9%**
- The rate applies to the **margin** (price − cost), not to the billed amount.
- **Paid when collected:** a commission becomes payable once the invoice has been paid.
- Computed **monthly**, per **individual salesperson**.

Non-invasive by design: it reads the native models (`account.move`, `account.move.line`,
`account.payment`) as a read-only *datasource* and writes only to its own models
(`yaguven.commission.*`). It neither depends on nor inherits from Odoo's own commission
module (`sale_commission`).

## A note on language

The source of this module is English, including its comments — Darakjian is a Michigan
deployment. There are deliberately **no `.po` catalogs**: since Odoo 16 the `en_US` value
IS the translation key, so a catalog can never translate *into* the source language.
Writing the strings in English is what makes the module translatable at all; adding a
Spanish-keyed catalog would undo that. See `../GLOSSARY.md`.

Yagüven C.G.
