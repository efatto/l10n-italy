# Copyright 2026 Nextev Srl
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import tagged

from odoo.addons.l10n_it_edi.tests.common import TestItEdi


@tagged("post_install", "-at_install")
class TestEdiDeliveryNote(TestItEdi):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Product
        cls.product = (
            cls.env["product.product"]
            .with_company(cls.company)
            .create(
                {
                    "name": "Test Product",
                    "type": "consu",
                    "list_price": 100.0,
                    "invoice_policy": "delivery",
                }
            )
        )

    def test_deferred_invoice_with_delivery_note(self):
        """
        Test that a deferred invoice (TD24) with delivery notes
        includes DatiDDT in the FatturaPA XML.
        """
        from datetime import timedelta

        # Create sale order
        sale_order = (
            self.env["sale.order"]
            .with_company(self.company)
            .create(
                {
                    "partner_id": self.italian_partner_a.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product.id,
                                "product_uom_qty": 5,
                                "price_unit": 100.0,
                                "tax_id": [(6, 0, self.default_tax.ids)],
                            },
                        )
                    ],
                }
            )
        )
        sale_order.action_confirm()

        # Deliver products
        picking = sale_order.picking_ids
        picking.move_ids.quantity = 5
        picking.button_validate()

        # Create delivery note from picking
        wizard = (
            self.env["stock.delivery.note.create.wizard"]
            .with_context(
                active_model="stock.picking",
                active_ids=picking.ids,
            )
            .create(
                {
                    "partner_shipping_id": self.italian_partner_a.id,
                }
            )
        )
        wizard.confirm()

        delivery_note = self.env["stock.delivery.note"].search(
            [("picking_ids", "in", picking.ids)]
        )
        self.assertTrue(delivery_note, "Delivery note should be created")

        # Validate delivery note
        delivery_note.action_confirm()

        # Create invoice from delivery note (deferred)
        invoice_wizard = (
            self.env["stock.delivery.note.invoice.wizard"]
            .with_context(
                active_model="stock.delivery.note",
                active_ids=delivery_note.ids,
            )
            .create({})
        )
        invoice_wizard.create_invoices()

        # Get the created invoice
        invoice = self.env["account.move"].search(
            [("partner_id", "=", self.italian_partner_a.id)],
            order="id desc",
            limit=1,
        )
        self.assertTrue(invoice, "Invoice should be created")

        # Check that delivery_note_ids is populated
        self.assertEqual(
            len(invoice.delivery_note_ids),
            1,
            "Invoice should be linked to 1 delivery note",
        )

        # Set invoice date to a different day from delivery to make it deferred (TD24)
        # This simulates the real scenario: delivery today, invoice later
        invoice.invoice_date = picking.date_done.date() + timedelta(days=1)

        # Post invoice
        invoice.action_post()

        # Generate XML
        xml_content = invoice._l10n_it_edi_render_xml()
        self.assertTrue(xml_content, "XML should be generated")

        # Parse XML using local-name() to avoid namespace issues
        root = etree.fromstring(xml_content)

        # Check that DatiDDT exists
        dati_ddt = root.xpath("//*[local-name()='DatiDDT']")
        self.assertTrue(dati_ddt, "DatiDDT should be present in XML")

        # Check NumeroDDT
        numero_ddt = root.xpath(
            "//*[local-name()='DatiDDT']/*[local-name()='NumeroDDT']"
        )
        self.assertTrue(
            len(numero_ddt) >= 1, "Should have at least one NumeroDDT element"
        )
        # Verify one of them matches our delivery note
        numero_ddt_texts = [n.text for n in numero_ddt]
        self.assertIn(
            delivery_note.name,
            numero_ddt_texts,
            f"NumeroDDT should contain delivery note name {delivery_note.name}",
        )

        # Check DataDDT
        data_ddt = root.xpath("//*[local-name()='DatiDDT']/*[local-name()='DataDDT']")
        self.assertTrue(len(data_ddt) >= 1, "Should have at least one DataDDT element")

        # Check document type is TD24 for deferred invoice (different day delivery)
        tipo_documento = root.xpath(
            "//*[local-name()='DatiGeneraliDocumento']/*[local-name()='TipoDocumento']"
        )
        self.assertEqual(
            tipo_documento[0].text,
            "TD24",
            "Should be TD24 (deferred) invoice with DDT on different date",
        )
