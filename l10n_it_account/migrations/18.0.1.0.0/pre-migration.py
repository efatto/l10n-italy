# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_it_account.migration_utils import uninstall_modules

# Modules that no longer exist in v18 and whose features are not merged into any
# surviving module. They are fully uninstalled (data, fields, columns and views)
# instead of just dropping their views, so that nothing is left dangling.
OLD_MODULES_TO_UNINSTALL = [
    "l10n_it_vat_statement_split_payment",
]


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    uninstall_modules(env, OLD_MODULES_TO_UNINSTALL)
