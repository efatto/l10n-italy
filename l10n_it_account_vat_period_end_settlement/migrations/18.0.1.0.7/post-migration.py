#  Copyright 2026 Sergio Corato <https://github.com/sergiocorato>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

from odoo.addons.l10n_it_account_vat_period_end_settlement import hooks


@openupgrade.migrate()
def migrate(env, version):
    # The module is renamed from "account_vat_period_end_statement" (see
    # OpenUpgrade apriori), so on the upgrade path it is upgraded, not
    # installed: its post_init_hook does not run and the hook must be called
    # explicitly. The hook is idempotent and also consumes the marker written by
    # l10n_it_account, so the taxes added by the 18.0 chart are not excluded
    # from the VAT settlements.
    hooks.post_absorb_old_module(env)
