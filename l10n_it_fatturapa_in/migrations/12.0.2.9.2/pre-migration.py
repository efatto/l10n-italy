# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    if not version:
        return
    if not openupgrade.column_exists(cr, 'fatturapa_attachment_in', 'is_self_invoice'):
        openupgrade.logged_query(
            cr,
            """
        ALTER TABLE fatturapa_attachment_in
            ADD COLUMN IF NOT EXISTS is_self_invoice BOOLEAN
        """,
        )
        openupgrade.logged_query(
            cr,
            """
        UPDATE fatturapa_attachment_in
            SET is_self_invoice = false
        """,
        )
