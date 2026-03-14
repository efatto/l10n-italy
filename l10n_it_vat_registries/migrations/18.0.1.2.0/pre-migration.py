# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

_OLD_MODULES = [
    "l10n_it_vat_registries_rc",
    "l10n_it_vat_registries_split_payment",
]


def _remove_module_views(cr, module_name):
    """Remove views registered by the old module and any views inheriting them.

    Uses a recursive CTE so that:
     - inherited views are deleted before their parents (no FK violation)
     - all ir_model_data rows for deleted views are removed (no orphans)
    """
    openupgrade.logged_query(
        cr,
        """
        WITH RECURSIVE views_to_delete AS (
            SELECT v.id
            FROM ir_ui_view v
            JOIN ir_model_data imd
                ON imd.model = 'ir.ui.view'
               AND imd.res_id = v.id
               AND imd.module = %s
            UNION ALL
            SELECT v.id
            FROM ir_ui_view v
            JOIN views_to_delete vtd ON v.inherit_id = vtd.id
        ),
        deleted_imd AS (
            DELETE FROM ir_model_data
            WHERE model = 'ir.ui.view'
              AND res_id IN (SELECT id FROM views_to_delete)
        )
        DELETE FROM ir_ui_view
        WHERE id IN (SELECT id FROM views_to_delete)
        """,
        (module_name,),
    )


@openupgrade.migrate()
def migrate(env, version):
    for module in _OLD_MODULES:
        if openupgrade.is_module_installed(env.cr, module):
            _logger.info(
                "Module %s was installed in previous version, removing its views",
                module,
            )
            _remove_module_views(env.cr, module)
            openupgrade.update_module_names(
                env.cr,
                [(module, "l10n_it_vat_registries")],
                merge_modules=True,
            )
