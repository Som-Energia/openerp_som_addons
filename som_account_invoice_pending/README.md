# som_account_invoice_pending

Mòdul que extend el mòdul de GISCE account_invoice_pending i serveix per gestionar el fluxe d'estats de les factures impagades

## Models

* account.invoice.pending.history: Extés de GISCE. Històric d'estats pendents.
* norma57.file.line: Extés de GISCE. Per generar un fitxer de cobrament tipus N57 amb codi de barres.
* update.pending.states: Permet fer accions concrets en fer el canvi a qualsevol estat (enviar email, sms,etc...)
* som_account_invoice_pending_exceptions.py: Conjunt excepcions específiques del mòdul.

## Funcionalitats

* Factura -> Canvi estat pendent: Perment canviar l'estat de pagament d'una factura.

## Cicle de vida

* Quan una factura esdevé impagada (es carrega una devolució del banc) avança els estats (segons el procés de tall: Per defecte / Bo social) mentre no es paga, fins a l'estat de Tall on s'acaba generant una Baixa i enviament a la CUR. Abans d'això s'enviaran varis emails i SMS de recordatori de tall.

## Responsable

* Equip de Gestió de Cobraments
