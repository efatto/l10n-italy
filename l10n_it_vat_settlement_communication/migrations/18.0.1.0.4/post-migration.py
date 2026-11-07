#  Copyright 2026 Sergio Corato <https://github.com/sergiocorato>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

from odoo.addons.l10n_it_vat_settlement_communication import hooks


@openupgrade.migrate()
def migrate(env, version):
    # The module is renamed from "l10n_it_vat_statement_communication" (see
    # OpenUpgrade apriori), so it is upgraded, not installed: its post_init_hook
    # does not run and the hook must be called explicitly. The hook only touches
    # the taxes that had vsc_exclude_operation = True, a leftover column that is
    # NULL on the taxes created by 18.0, so it is idempotent and safe here.
    hooks.post_absorb_old_module(env)
