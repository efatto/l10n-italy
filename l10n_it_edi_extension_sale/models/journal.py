# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_it_advance_document_type_id = fields.Many2one(
        comodel_name="l10n_it.document.type",
        string="Advance Document Type",
        help="Document type set on the down payment invoices created "
        "from this journal.",
    )
