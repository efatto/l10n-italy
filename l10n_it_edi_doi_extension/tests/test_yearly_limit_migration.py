# Copyright 2026 Sergio Corato
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from openupgradelib import openupgrade

from ..hooks import (
    _OLD_YEARLY_LIMIT_TABLE,
    _migrate_yearly_limits_to_plafond,
)
from .common import Common


class TestYearlyLimitMigration(Common):
    """Yearly limits of the old module become annual plafonds.

    The old module kept the plafond of the Agenzia delle Entrate per company
    and year in ``res.company.declaration_yearly_limit_ids``; the issued
    declarations of the year drew their threshold from it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Issued declaration as migrated from the old module: it has no
        # plafond and it starts in 2023, the year of the yearly limit
        cls.migrated_doi = cls._create_declaration("in")
        cls.received_doi = cls._create_declaration("out")
        for declaration in cls.migrated_doi | cls.received_doi:
            cls.env.cr.execute(
                """
                UPDATE l10n_it_edi_doi_declaration_of_intent
                   SET plafond_id = NULL, start_date = %s, end_date = %s
                 WHERE id = %s
                """,
                (date(2023, 1, 1), date(2023, 12, 31), declaration.id),
            )
        cls.env.invalidate_all()

    def _create_old_yearly_limit(self, year, limit_amount):
        """Simulate the yearly limit table of the old module."""
        self.env.cr.execute(
            """
            CREATE TABLE IF NOT EXISTS l10n_it_declaration_of_intent_yearly_limit
                (id serial PRIMARY KEY,
                 company_id integer,
                 year varchar,
                 limit_amount double precision)
            """
        )
        self.env.cr.execute(
            """
            INSERT INTO l10n_it_declaration_of_intent_yearly_limit
                (company_id, year, limit_amount)
            VALUES (%s, %s, %s)
            """,
            (self.company.id, year, limit_amount),
        )

    def _get_plafond(self, year):
        return self.env["l10n_it_edi_doi_extension.plafond.year"].search(
            [("company_id", "=", self.company.id), ("year", "=", year)]
        )

    def test_yearly_limit_becomes_plafond(self):
        self._create_old_yearly_limit("2023", 12345.0)

        # Act
        _migrate_yearly_limits_to_plafond(self.env)
        self.env.invalidate_all()

        # Assert: one plafond with the old limit as total
        plafond = self._get_plafond(2023)
        self.assertEqual(len(plafond), 1)
        self.assertEqual(plafond.plafond_total, 12345.0)
        # the issued declaration of the year is linked, the received one is not
        self.assertEqual(self.migrated_doi.plafond_id, plafond)
        self.assertFalse(self.received_doi.plafond_id)
        # the old table is consumed
        self.assertFalse(openupgrade.table_exists(self.env.cr, _OLD_YEARLY_LIMIT_TABLE))

    def test_existing_plafond_is_kept(self):
        plafond = self.env["l10n_it_edi_doi_extension.plafond.year"].create(
            {
                "company_id": self.company.id,
                "year": 2023,
                "plafond_total": 50000.0,
            }
        )
        self._create_old_yearly_limit("2023", 12345.0)

        # Act
        _migrate_yearly_limits_to_plafond(self.env)
        self.env.invalidate_all()

        # Assert: the existing plafond is kept, and the declarations of the
        # year are linked to it
        self.assertEqual(self._get_plafond(2023), plafond)
        self.assertEqual(plafond.plafond_total, 50000.0)
        self.assertEqual(self.migrated_doi.plafond_id, plafond)

    def test_no_yearly_limit_table(self):
        """Nothing happens when the table of the old module is absent."""
        before = self.env["l10n_it_edi_doi_extension.plafond.year"].search_count([])

        _migrate_yearly_limits_to_plafond(self.env)

        self.assertEqual(
            self.env["l10n_it_edi_doi_extension.plafond.year"].search_count([]), before
        )
