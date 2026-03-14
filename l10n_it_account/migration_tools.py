# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Common methods for migrations
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


def _remove_module(env, module_name):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_module_module
        SET
            state = 'to remove'
        WHERE
            name = %(module_name)s
            AND state NOT IN ('to remove', 'uninstalled')
        """,
        dict(
            module_name=module_name,
        ),
    )


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
    cr.execute(
        """
        SELECT module, name, id from ir_model_data
        WHERE model = 'ir.ui.menu'
        AND module = ANY(%s)
        """,
        (list(modules),),
    )
    menus = cr.fetchall()
    if menus:
        deleted_menus = "\n".join(
            f"module: {menu[0]}: name: {menu[1]}, id (ir.model.data): {menu[2]}"
            for menu in menus
        )
        _logger.info(f"Deleted menus: {deleted_menus}")
        openupgrade.logged_query(
            cr,
            """
            DELETE from ir_model_data
            WHERE model = 'ir.ui.menu'
            AND module = ANY(%s)
            """,
            (list(modules),),
        )
