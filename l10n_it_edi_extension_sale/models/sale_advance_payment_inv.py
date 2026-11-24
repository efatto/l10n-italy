# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _create_invoices(self, sale_orders):
        invoices = super()._create_invoices(sale_orders)
        if self.advance_payment_method in ("fixed", "percentage"):
            for invoice in invoices:
                document_type = invoice.journal_id.l10n_it_advance_document_type_id
                if document_type:
                    invoice.l10n_it_document_type = document_type
        return invoices
