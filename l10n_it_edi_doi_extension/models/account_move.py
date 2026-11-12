# Copyright 2025 Nextev Srl

from odoo import Command, _, api, fields, models, tools
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    doi_type = fields.Selection(
        [("in", "Issued from company"), ("out", "Received from customers")],
        compute="_compute_l10n_it_edi_doi_type",
    )

    # Multiple declarations of intent support
    l10n_it_edi_doi_ids = fields.One2many(
        "account.move.doi",
        "move_id",
        string="Declarations of Intent",
        help="Multiple declarations of intent linked to this invoice. "
        "Use this when the invoice amount exceeds a single declaration's threshold.",
    )
    l10n_it_edi_doi_count = fields.Integer(
        compute="_compute_l10n_it_edi_doi_count",
        string="DOI Count",
    )
    l10n_it_edi_doi_total_amount = fields.Monetary(
        compute="_compute_l10n_it_edi_doi_total_amount",
        string="Total DOI Amount",
        help="Total amount covered by all linked declarations of intent.",
    )

    @api.depends("l10n_it_edi_doi_ids")
    def _compute_l10n_it_edi_doi_count(self):
        for move in self:
            move.l10n_it_edi_doi_count = len(move.l10n_it_edi_doi_ids)

    @api.depends("l10n_it_edi_doi_ids.amount")
    def _compute_l10n_it_edi_doi_total_amount(self):
        for move in self:
            move.l10n_it_edi_doi_total_amount = sum(
                move.l10n_it_edi_doi_ids.mapped("amount")
            )

    @api.onchange("l10n_it_edi_doi_ids")
    def _onchange_l10n_it_edi_doi_ids(self):
        """Sync the first declaration with the standard field."""
        if self.l10n_it_edi_doi_ids:
            self.l10n_it_edi_doi_id = self.l10n_it_edi_doi_ids[0].declaration_id
        else:
            self.l10n_it_edi_doi_id = False

    @api.depends("move_type")
    def _compute_l10n_it_edi_doi_type(self):
        purchase_types = self.env["account.move"].get_purchase_types()
        sale_types = self.env["account.move"].get_sale_types()
        for move in self:
            if move.move_type in purchase_types:
                move.doi_type = "in"
            elif move.move_type in sale_types:
                move.doi_type = "out"
            else:
                move.doi_type = False

    def _compute_l10n_it_edi_doi_use(self):
        purchase_move_ids = self.filtered(lambda x: x.doi_type == "in")
        other_move_ids = self - purchase_move_ids
        super(AccountMove, other_move_ids)._compute_l10n_it_edi_doi_use()
        for move in purchase_move_ids:
            move.l10n_it_edi_doi_use = (
                move.l10n_it_edi_doi_id or move.country_code == "IT"
            )
        return  # W8110

    def _build_threshold_warning(self, declaration, declared_amount):
        """Threshold warning of ``declaration`` once this move is posted.

        Same computation as core, with the amount of this move that the
        declaration covers given as a parameter: core uses the DOI amount of
        the whole invoice, while a declaration only covers the amount of its
        bridge row.
        ``declared_amount`` is signed, like the amount that core adds.
        """
        self.ensure_one()
        declaration_invoiced = declaration.invoiced
        declaration_not_yet_invoiced = declaration.not_yet_invoiced
        if self.state != "posted":
            # Here we replicate what would happen when posting the invoice.
            declaration_invoiced += declared_amount
            additional_invoiced_qty = {}
            is_purchase = self.is_purchase_document()
            linked_orders = (
                self.env["purchase.order"] if is_purchase else self.env["sale.order"]
            )
            for invoice_line in self.invoice_line_ids:
                order_lines = (
                    invoice_line.purchase_line_id
                    if is_purchase
                    else invoice_line.sale_line_ids
                )
                for order_line in order_lines:
                    order = order_line.order_id
                    if order.l10n_it_edi_doi_id == declaration:
                        linked_orders |= order
                    qty_invoiced = (
                        invoice_line.product_uom_id._compute_quantity(
                            invoice_line.quantity, order_line.product_uom
                        )
                        * -self.direction_sign
                    )
                    order_line_id = order_line.ids[
                        0
                    ]  # do not just use `id` in case of NewId
                    additional_invoiced_qty[order_line_id] = (
                        additional_invoiced_qty.get(order_line_id, 0) + qty_invoiced
                    )

            for order in linked_orders:
                not_yet_invoiced = order.l10n_it_edi_doi_not_yet_invoiced
                not_yet_invoiced_after_posting = (
                    order._l10n_it_edi_doi_get_amount_not_yet_invoiced(
                        declaration,
                        additional_invoiced_qty=additional_invoiced_qty,
                    )
                )
                declaration_not_yet_invoiced -= (
                    not_yet_invoiced - not_yet_invoiced_after_posting
                )

        return declaration._build_threshold_warning_message(
            declaration_invoiced, declaration_not_yet_invoiced
        )

    def _build_extended_threshold_warning(self):
        """Threshold warning of every declaration linked through the bridge rows.

        Bridge rows are always positive; the amount of a refund is not, and a
        refund lowers what the declaration has invoiced instead of consuming
        it again.
        """
        self.ensure_one()
        is_refund = self.move_type in ("in_refund", "out_refund")
        warnings = []
        for declaration_line in self.l10n_it_edi_doi_ids:
            declared_amount = declaration_line.amount
            if is_refund:
                declared_amount = -declared_amount
            threshold_warning = self._build_threshold_warning(
                declaration_line.declaration_id, declared_amount
            )
            if threshold_warning:
                warnings.append(threshold_warning)
        return "\n".join(warnings)

    def _build_core_threshold_warning(self):
        """Threshold warning that core builds for ``l10n_it_edi_doi_id``.

        Core reports the first declaration only, checking it against the DOI
        amount of the whole invoice. That message is replaced by the one built
        on the bridge rows, so it has to be recognized inside the core string.
        """
        self.ensure_one()
        if not (
            self.l10n_it_edi_doi_id
            and self.is_sale_document(include_receipts=False)
            and self.state != "cancel"
        ):
            return ""
        return self._build_threshold_warning(
            self.l10n_it_edi_doi_id, self.l10n_it_edi_doi_amount
        )

    @api.depends("l10n_it_edi_doi_total_amount", "l10n_it_edi_doi_ids.amount")
    def _compute_l10n_it_edi_doi_warning(self):
        """Append the multi-declaration warnings to the core ones.

        Core only knows the first declaration (``l10n_it_edi_doi_id``) and
        checks it against the DOI amount of the whole invoice: keep its
        validity warnings, but not that threshold warning, which the bridge
        rows make inaccurate. Append instead, for every linked declaration,
        its own threshold warning and, when the declarations do not cover the
        invoice DOI amount, a coverage warning.
        """
        super()._compute_l10n_it_edi_doi_warning()
        for move in self.filtered("l10n_it_edi_doi_ids"):
            # Sale documents carry a signed amount (core), purchase ones do not
            doi_amount = abs(move.l10n_it_edi_doi_amount)
            warnings = move.l10n_it_edi_doi_warning.split("\n\n")
            core_threshold_warning = move._build_core_threshold_warning()
            if core_threshold_warning:
                warnings = [
                    warning for warning in warnings if warning != core_threshold_warning
                ]
            if threshold_warning := move._build_extended_threshold_warning():
                warnings.append(threshold_warning)
            if (
                move.currency_id.compare_amounts(
                    move.l10n_it_edi_doi_total_amount, doi_amount
                )
                < 0
            ):
                covered = (
                    f"{move.l10n_it_edi_doi_total_amount:.2f} "
                    f"{move.currency_id.symbol}"
                )
                total = f"{doi_amount:.2f} {move.currency_id.symbol}"
                warnings.append(
                    _(
                        "Warning: The total amount covered by declarations "
                        "(%(covered)s) is less than the invoice DOI amount "
                        "(%(total)s). Please adjust the amounts or add more "
                        "declarations.",
                        covered=covered,
                        total=total,
                    )
                )
            move.l10n_it_edi_doi_warning = "\n\n".join(filter(None, warnings))
        return  # W8110

    def _compute_l10n_it_edi_doi_amount(self):
        purchase_move_ids = self.filtered(lambda x: x.doi_type == "in")
        other_move_ids = self - purchase_move_ids
        super(AccountMove, other_move_ids)._compute_l10n_it_edi_doi_amount()
        for move in purchase_move_ids:
            tax = move._l10n_it_edi_doi_ext_get_declaration_tax()
            if not tax or not move.l10n_it_edi_doi_id:
                move.l10n_it_edi_doi_amount = 0
                continue
            declaration_lines = move._l10n_it_edi_doi_ext_get_declaration_lines(tax)
            move.l10n_it_edi_doi_amount = sum(declaration_lines.mapped("price_total"))
        return  # W8110

    def _compute_l10n_it_edi_doi_id(self):
        purchase_move_ids = self.filtered(lambda x: x.doi_type == "in")
        other_move_ids = self - purchase_move_ids
        super(AccountMove, other_move_ids)._compute_l10n_it_edi_doi_id()
        for move in purchase_move_ids:
            if not move.l10n_it_edi_doi_use or (
                move.state != "draft" and not move.l10n_it_edi_doi_id
            ):
                move.l10n_it_edi_doi_id = False
                continue

            partner = move.partner_id.commercial_partner_id
            validity_warnings = move.l10n_it_edi_doi_id._get_validity_warnings(
                move.company_id, partner, move.currency_id, move.l10n_it_edi_doi_date
            )
            if move.l10n_it_edi_doi_id and not validity_warnings:
                continue

            declaration = self.env[
                "l10n_it_edi_doi.declaration_of_intent"
            ]._fetch_valid_declaration_of_intent(
                move.company_id,
                partner,
                move.currency_id,
                move.l10n_it_edi_doi_date,
                doi_type="in",
            )
            move.l10n_it_edi_doi_id = declaration
        return  # W8110

    def _l10n_it_edi_doi_ext_get_declaration_tax(self):
        """Get the DoI Tax to use with this line."""
        company = self.company_id
        return (
            company.l10n_it_edi_doi_bill_tax_id
            if self.is_purchase_document()
            else company.l10n_it_edi_doi_tax_id
        )

    def _l10n_it_edi_doi_ext_get_declaration_lines(self, doi_tax):
        """Extract the lines to be counted for DoI."""
        self.ensure_one()
        if self.l10n_it_edi_doi_id:
            lines = self.invoice_line_ids.filtered(
                lambda line, doi_tax=doi_tax: line._is_counted_for_doi(doi_tax)
            )
        else:
            lines = self.env["account.move.line"].browse()
        return lines

    def _l10n_it_edi_doi_ext_get_lines_messages(self, doi_tax):
        """Check that all the invoice lines are valid for the DoI."""
        self.ensure_one()
        errors = []
        for line in self.invoice_line_ids:
            if error := line._l10n_it_edi_doi_ext_get_validation_message(doi_tax):
                errors.append(error)
        return errors

    def _l10n_it_edi_doi_ext_get_declarations(self):
        """Return the declarations to use for this invoice, in date order."""
        self.ensure_one()
        if self.l10n_it_edi_doi_ids:
            return self.l10n_it_edi_doi_ids.declaration_id.sorted(
                lambda declaration: (declaration.start_date, declaration.id)
            )
        return self.env[
            "l10n_it_edi_doi.declaration_of_intent"
        ]._fetch_valid_declarations_of_intent(
            self.company_id,
            self.partner_id.commercial_partner_id,
            self.currency_id,
            self.l10n_it_edi_doi_date,
            doi_type="in" if self.is_purchase_document() else "out",
        )

    def _l10n_it_edi_doi_ext_get_declarations_used_amounts(self, declarations):
        """Get the amount of this invoice to assign to each declaration."""
        self.ensure_one()
        declarations_available_amounts = {
            declaration.id: declaration.remaining for declaration in declarations
        }
        declarations_used_amounts = {}
        doi_tax = self._l10n_it_edi_doi_ext_get_declaration_tax()
        if not doi_tax or not declarations:
            return declarations_used_amounts
        for line in self.invoice_line_ids.filtered(
            lambda line: line._is_counted_for_doi(doi_tax)
        ):
            amount = abs(line.price_subtotal)
            for declaration in declarations:
                declarations_used_amounts.setdefault(declaration.id, 0)
                if declaration == declarations[-1]:
                    # If this is the last available declaration,
                    # assign all the remaining amount.
                    declaration_used_amount = amount
                else:
                    declaration_used_amount = min(
                        amount, declarations_available_amounts[declaration.id]
                    )
                declarations_available_amounts[declaration.id] -= (
                    declaration_used_amount
                )
                declarations_used_amounts[declaration.id] += declaration_used_amount
                amount -= declaration_used_amount
                if self.currency_id.compare_amounts(amount, 0) <= 0:
                    break
        return declarations_used_amounts

    def _l10n_it_edi_doi_ext_update_declarations(self):
        """Create bridge rows when the invoice exceeds a single declaration."""
        self.ensure_one()
        if self.l10n_it_edi_doi_ids:
            return
        declarations = self._l10n_it_edi_doi_ext_get_declarations()
        if not declarations:
            return
        declarations_used_amounts = (
            self._l10n_it_edi_doi_ext_get_declarations_used_amounts(declarations)
        )
        used_declarations = declarations.filtered(
            lambda declaration: declarations_used_amounts.get(declaration.id)
        )
        if len(used_declarations) <= 1:
            return
        for declaration in used_declarations:
            self.env["account.move.doi"].create(
                {
                    "move_id": self.id,
                    "declaration_id": declaration.id,
                    "amount": declarations_used_amounts[declaration.id],
                }
            )

    def _post(self, soft=True):
        errors = []
        for move in self:
            declaration = move.l10n_it_edi_doi_id
            doi_tax = move._l10n_it_edi_doi_ext_get_declaration_tax()
            if not doi_tax:
                continue
            declaration_lines = move._l10n_it_edi_doi_ext_get_declaration_lines(doi_tax)
            if declaration_lines and not declaration:
                errors.append(
                    _(
                        "Given the tax %s is applied, there should be a "
                        "Declaration of Intent selected.",
                        doi_tax.name,
                    )
                )
            if declaration:
                if not declaration_lines:
                    errors.append(
                        move.env._(
                            "Given the Declaration of Intent %(doi_name)s "
                            "is linked to this Move, at least one line "
                            "should contain the Tax %(doi_tax_name)s.",
                            doi_name=declaration.display_name,
                            doi_tax_name=doi_tax.name,
                        )
                    )
                if line_errors := move._l10n_it_edi_doi_ext_get_lines_messages(doi_tax):
                    errors.extend(line_errors)
                currency = move.currency_id
                # Sale documents carry a signed amount (core), purchase ones do
                # not, while the bridge rows are always unsigned: compare the
                # absolute values so that credit notes are checked too.
                doi_amount = abs(move.l10n_it_edi_doi_amount)
                doi_total = abs(move.l10n_it_edi_doi_total_amount)
                if currency.compare_amounts(doi_total, doi_amount) > 0:
                    errors.append(
                        move.env._(
                            "The Total Amount for "
                            "the Declaration of Intent %(doi_total)s "
                            "cannot be greater than "
                            "the Declaration of Intent Amount %(doi_amount)s.\n"
                            "Please set a different amount "
                            "in the Declaration of Intent lines.",
                            doi_total=tools.formatLang(
                                move.env, doi_total, currency_obj=currency
                            ),
                            doi_amount=tools.formatLang(
                                move.env, doi_amount, currency_obj=currency
                            ),
                        )
                    )
        if errors:
            raise UserError("\n".join(errors))
        for move in self:
            move._l10n_it_edi_doi_ext_update_declarations()
        return super()._post(soft)

    def copy_data(self, default=None):
        """Carry the bridge lines onto credit notes only.

        A credit note must reverse the same declarations with the same amounts.
        A duplicate follows core instead: the split between declarations depends
        on their remaining amount at invoicing time, so it is not copied.
        Core _reverse_moves builds the credit note with copy(), so the lines are
        created while the move is still draft.
        The lines are copied whatever the current state of the declaration: a
        credit note reverses a consumption that already happened, so it must
        point to the same declaration even if it was terminated or revoked since.
        Core copy_data keeps l10n_it_edi_doi_id in that case as well (state and
        dates are not blocking when the amount is not positive).
        """
        data_list = super().copy_data(default)
        if not (default and default.get("reversed_entry_id")):
            return data_list
        for move, data in zip(self, data_list, strict=True):
            data["l10n_it_edi_doi_ids"] = [
                Command.create(
                    {
                        "declaration_id": doi_link.declaration_id.id,
                        "amount": doi_link.amount,
                        "sequence": doi_link.sequence,
                    }
                )
                for doi_link in move.l10n_it_edi_doi_ids
                # Migrated rows with amount 0 would fail the positive amount check
                if doi_link.amount
            ]
        return data_list

    def action_open_declaration_of_intent(self):
        """Open declaration(s) of intent.

        If there are multiple declarations, open a list view.
        If there's only one, open its form view.
        """
        self.ensure_one()
        declaration_ids = self.l10n_it_edi_doi_ids.mapped("declaration_id").ids
        if not declaration_ids:
            declaration_ids = (
                [self.l10n_it_edi_doi_id.id] if self.l10n_it_edi_doi_id else []
            )

        if len(declaration_ids) > 1:
            return {
                "name": _("Declarations of Intent for %s", self.display_name),
                "type": "ir.actions.act_window",
                "view_mode": "list,form",
                "res_model": "l10n_it_edi_doi.declaration_of_intent",
                "domain": [("id", "in", declaration_ids)],
            }
        elif declaration_ids:
            return {
                "name": _("Declaration of Intent for %s", self.display_name),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "l10n_it_edi_doi.declaration_of_intent",
                "res_id": declaration_ids[0],
            }
        else:
            raise UserError(
                _("No Declaration of Intent found for %s.", self.display_name)
            )
