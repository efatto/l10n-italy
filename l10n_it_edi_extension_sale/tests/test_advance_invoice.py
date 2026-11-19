# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command

from odoo.addons.l10n_it_edi.tests.common import TestItEdi


class TestAdvanceInvoice(TestItEdi):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.advance_document_type = cls.env["l10n_it.document.type"].search(
            [("code", "=", "TD02")], limit=1
        )
        cls.env["account.journal"].search([("type", "=", "sale")]).write(
            {
                "l10n_it_advance_document_type_id": cls.advance_document_type.id,
            }
        )

    def _create_order(self):
        order = (
            self.env["sale.order"]
            .with_context(tracking_disable=True)
            .create(
                {
                    "partner_id": self.italian_partner_a.id,
                    "order_line": [
                        Command.create(
                            {
                                "product_id": self.product_a.id,
                                "product_uom_qty": 1,
                            }
                        )
                    ],
                }
            )
        )
        order.action_confirm()
        return order

    def _create_invoice(self, order, payment_method):
        wizard_vals = {"advance_payment_method": payment_method}
        if payment_method == "fixed":
            wizard_vals["fixed_amount"] = 10.0
        elif payment_method == "percentage":
            wizard_vals["amount"] = 10.0
        wizard = (
            self.env["sale.advance.payment.inv"]
            .with_context(active_ids=order.ids)
            .create(wizard_vals)
        )
        action = wizard.create_invoices()
        return self.env["account.move"].browse(action["res_id"])

    def test_advance_invoice_document_type(self):
        """Down payment invoices get the document type of their journal."""
        for payment_method in ("fixed", "percentage"):
            invoice = self._create_invoice(self._create_order(), payment_method)
            self.assertEqual(
                invoice.l10n_it_document_type,
                self.advance_document_type,
                f"Document type not set for {payment_method} down payment",
            )

    def test_regular_invoice_document_type(self):
        """Regular invoices do not get the advance document type."""
        invoice = self._create_invoice(self._create_order(), "delivered")
        self.assertNotEqual(
            invoice.l10n_it_document_type,
            self.advance_document_type,
        )
