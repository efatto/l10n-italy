# Common methods for migrations
from openupgradelib import openupgrade


def _remove_module(env, module_name):
    query_params = {
        "name": module_name,
    }
    env.cr.execute(
        "SELECT id FROM ir_module_module WHERE name = %(name)s",
        query_params,
    )
    if bool(env.cr.fetchone()):
        openupgrade.logged_query(
            env.cr,
            "UPDATE ir_module_module SET state = 'to remove' WHERE name = %(name)s",
            query_params,
        )
