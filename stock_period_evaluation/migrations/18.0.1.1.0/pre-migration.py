# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

from odoo.tools.sql import column_exists

# The module is renamed from stock_close_period in apriori.py, so the old XML-IDs
# are already stored under the new module name when this script is executed.
MODULE = "stock_period_evaluation"

FIELD_RENAMES = [
    (
        "stock.close.period",
        "stock_close_period",
        "work_start",
        "work_start_date",
    ),
    (
        "stock.close.period",
        "stock_close_period",
        "work_end",
        "work_end_date",
    ),
]

XMLID_RENAMES = [
    (
        "module_category_stock_close_period",
        "module_category_stock_period_evaluation",
    ),
    (
        "group_stock_close_period_user_readonly",
        "group_stock_period_evaluation_user_readonly",
    ),
    (
        "group_stock_close_period_manager",
        "group_stock_period_evaluation_manager",
    ),
    ("stock_close_period_comp_rule", "stock_period_evaluation_comp_rule"),
    (
        "stock_close_period_line_comp_rule",
        "stock_period_evaluation_line_comp_rule",
    ),
    ("stock_close_period_tree", "stock_period_evaluation_tree"),
    ("stock_close_period_form", "stock_period_evaluation_form"),
    ("stock_close_period_line_tree", "stock_period_evaluation_line_tree"),
    ("stock_close_period_line_search", "stock_period_evaluation_line_search"),
    (
        "access_stock_close_period_stock_manager",
        "access_stock_period_evaluation_stock_manager",
    ),
    (
        "access_stock_close_period_stock_user",
        "access_stock_period_evaluation_stock_user",
    ),
    (
        "access_stock_close_period_line_stock_manager",
        "access_stock_period_evaluation_line_stock_manager",
    ),
    (
        "access_stock_close_period_line_stock_user",
        "access_stock_period_evaluation_line_stock_user",
    ),
]

OLD_CONFIG_PARAMETER = "stock_close_period.last_close_date"
NEW_CONFIG_PARAMETER = "stock_period_evaluation.last_close_date"

# These modules have no counterpart in 18.0: mark them for removal so that
# Odoo does not keep them installed without their code.
OBSOLETE_MODULES = [
    "stock_close_period_landed_costs",
    "stock_close_period_landed_tariff_logistic",
]


def _rename_config_parameter(env):
    """Move the last close date to the new key used by the module."""
    parameters = env["ir.config_parameter"].sudo()
    old_parameter = parameters.search([("key", "=", OLD_CONFIG_PARAMETER)])
    if not old_parameter:
        return
    new_parameter = parameters.search([("key", "=", NEW_CONFIG_PARAMETER)])
    if new_parameter:
        # The module data already created the new parameter: drop the old one.
        old_parameter.unlink()
    else:
        old_parameter.key = NEW_CONFIG_PARAMETER


def _remove_obsolete_modules(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_module_module
        SET state = 'to remove'
        WHERE name = ANY(%s)
          AND state NOT IN ('uninstalled', 'to remove')
        """,
        (OBSOLETE_MODULES,),
    )


@openupgrade.migrate()
def migrate(env, version):
    _remove_obsolete_modules(env)
    for model, table, old_field, new_field in FIELD_RENAMES:
        if column_exists(env.cr, table, old_field) and not column_exists(
            env.cr, table, new_field
        ):
            openupgrade.rename_fields(env, [(model, table, old_field, new_field)])
    openupgrade.rename_xmlids(
        env.cr,
        [
            (f"{MODULE}.{old_name}", f"{MODULE}.{new_name}")
            for old_name, new_name in XMLID_RENAMES
        ],
    )
    _rename_config_parameter(env)
