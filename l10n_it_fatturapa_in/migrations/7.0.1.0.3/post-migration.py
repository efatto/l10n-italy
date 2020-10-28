# -*- coding: utf-8 -*-
# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(cr, version):
    if not version:
        # create ftpa_withholding_ids from ftpa_withholding_type
        cr.execute(
            """
            INSERT INTO withholding_data_line
            (
                name,
                rate,
                reason,
                invoice_id,
                create_uid,
                create_date,
                write_date,
                write_uid
            )
            SELECT
                ai.ftpa_withholding_type_legacy7,
                ai.ftpa_withholding_rate_legacy7,
                ai.ftpa_withholding_payment_reason_legacy7,
                ai.id,
                ai.create_uid,
                ai.create_date,
                ai.write_date,
                ai.write_uid
            FROM account_invoice ai
            WHERE ai.ftpa_withholding_type_legacy7 IS NOT NULL;
            """
        )
