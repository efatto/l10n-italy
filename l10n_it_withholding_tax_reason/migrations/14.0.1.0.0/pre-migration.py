from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, installed_version):
    if not installed_version:
        return
    old_payment_reason = "causale_pagamento_id"
    new_payment_reason = "payment_reason_id"
    if not openupgrade.column_exists(env.cr, "account_move_line", new_payment_reason):
        openupgrade.rename_fields(
            env.cr,
            [
                (
                    "withholding.tax",
                    "withholding_tax",
                    old_payment_reason,
                    new_payment_reason,
                ),
            ],
        )
