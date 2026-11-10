**English**

This module extends the functionality of l10n_it_edi_doi, enabling the
use of the Declaration of Intent (Dichiarazione di Intento) for incoming
vendor bills and purchase orders, and the automatic assignment of the
received declarations to customer invoices created from sale orders.

Key features:
 - Support for multiple Declarations of Intent per invoice
 - Dedicated tab in invoice form for managing DOI associations
 - Automatic assignment of valid declarations to customer invoices created
   from sale orders without a declaration, using one or more declarations
   to cover the invoice amount
 - Automatic validation of DOI amounts and available thresholds
 - Smart warnings when invoice amounts don't match DOI coverage
 - Backward compatibility with single-declaration workflow
 - Check that the move lines only include the DoI Tax, when present
 - Check that at least one move line contains the DoI Tax when the DoI is set in the Move
 - In the Company form, only find Purchase/Sale Taxes of the shown Company for issued/received Declarations

**Italiano**

Questo modulo estende la funzionalità di l10n_it_edi_doi, permettendo
l'utilizzo della Dichiarazione di Intento per le fatture di acquisto in
ingresso e gli ordini di acquisto, e l'assegnazione automatica delle
dichiarazioni ricevute alle fatture clienti create da ordini di vendita.

Caratteristiche principali:
 - Supporto per dichiarazioni di intento multiple per fattura
 - Tab dedicato nel form fattura per gestire le associazioni DOI
 - Assegnazione automatica delle dichiarazioni valide alle fatture clienti
   create da ordini di vendita senza dichiarazione, usando una o più
   dichiarazioni per coprire l'importo della fattura
 - Validazione automatica degli importi e soglie disponibili
 - Avvisi intelligenti quando gli importi non corrispondono
 - Retrocompatibilità con il flusso a dichiarazione singola
 - Verifica che i movimenti contabili includano soltanto l'imposta per la DI, quando presente
 - Verifica che almeno un movimento contabile contenga l'imposta per la DI quando la DI è impostata nella registrazione
 - Nel form dell'azienda, trova solo le imposte di acquisto/vendita dell'azienda mostrata per le dichiarazioni emesse/ricevute
