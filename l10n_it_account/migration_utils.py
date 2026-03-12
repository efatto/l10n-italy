# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


def uninstall_modules(env, modules):
    """Fully uninstall modules that no longer exist in this version.

    Unlike :func:`remove_modules_views`, which is meant for modules whose
    features have been merged into a surviving module (so only their orphan
    views need to be dropped), this is for modules whose features are simply
    gone: a proper uninstall removes their data, fields, columns and views
    through Odoo's own machinery, leaving nothing dangling.

    ``modules`` can be a single module name or a list of module names.

    ``module_uninstall`` is used on purpose instead of
    ``button_immediate_uninstall``: the latter commits and reloads the registry,
    which must not happen in the middle of a migration.
    """
    if isinstance(modules, str):
        modules = [modules]
    if not modules:
        return
    module_records = env["ir.module.module"].search(
        [
            ("name", "in", modules),
            ("state", "not in", ("uninstalled", "uninstallable")),
        ]
    )
    if module_records:
        _logger.info(
            "Uninstalling modules no longer existing in this version: %s",
            module_records.mapped("name"),
        )
        module_records.module_uninstall()


def remove_modules_views(cr, modules):
    """Remove the views registered by the given modules and any view inheriting
    them.

    ``modules`` can be a single module name or a list of module names.

    Uses a recursive CTE so that:
     - inherited views are deleted before their parents (no FK violation)
     - all ir_model_data rows for deleted views are removed (no orphans)
    """
    if isinstance(modules, str):
        modules = [modules]
    if not modules:
        return
    openupgrade.logged_query(
        cr,
        """
        WITH RECURSIVE views_to_delete AS (
            SELECT v.id
            FROM ir_ui_view v
            JOIN ir_model_data imd
                ON imd.model = 'ir.ui.view'
               AND imd.res_id = v.id
               AND imd.module = ANY(%s)
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
        (list(modules),),
    )
