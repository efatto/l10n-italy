# -*- coding: utf-8 -*-
# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
from openupgradelib import openupgrade


def copy_columns(cr, column_spec):
    for table_name in column_spec.keys():
        for (old, new, field_type) in column_spec[table_name]:
            if field_type is None:
                cr.execute("""
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE table_name=%s
                        AND column_name = %s;
                    """, (table_name, old))
                field_type = cr.fetchone()[0]
            cr.execute("""
                ALTER TABLE %(table_name)s
                ADD COLUMN IF NOT EXISTS %(new)s %(field_type)s;
                UPDATE %(table_name)s SET %(new)s=%(old)s;
                """ % {
                'table_name': table_name,
                'old': old,
                'field_type': field_type,
                'new': new,
            })


@openupgrade.migrate()
def migrate(cr, version):
    copy_columns(cr, {
        'account_invoice': [
            ('ftpa_withholding_type', 'ftpa_withholding_type_legacy7', None),
            ('ftpa_withholding_payment_reason',
             'ftpa_withholding_payment_reason_legacy7', None),
            ('ftpa_withholding_rate', 'ftpa_withholding_rate_legacy7', None),
        ],
    })
