# som_account_invoice_pending

Mòdul que extend el mòdul de GISCE account_invoice_pending i serveix per gestionar el fluxe d'estats de les factures impagades. També l'utilitzem per gestionar les peticions de pobresa energètica dels contractes amb factures impades, als ajuntaments

## Models

* account.invoice.pending.history: Extés de GISCE. Històric d'estats pendents.
* norma57.file.line: Extés de GISCE. Per generar un fitxer de cobrament tipus N57 amb codi de barres.
* update.pending.states: Permet fer accions concrets en fer el canvi a qualsevol estat (enviar email, sms,etc...)
* som_account_invoice_pending_exceptions.py: Conjunt excepcions específiques del mòdul.
* som.consulta.pobresa: Hereda de crm.case i representa una consulta a una administració pública sobre si aquell titular es una persona suscetible de ser considerada pobresa energètica
* agrupacions.supramunicipals: Administracions públiques competents per gestionar aquestes consultes

## Funcionalitats

* Factura -> Canvi estat pendent: Perment canviar l'estat de pagament d'una factura.
* Polissa -> Acció 'Crear consulta pobresa': Assitent que des de una pòlissa, permet crear una consulta pobresa. Es pot cridar per múltiples pòlisses a la vegada.

## Cicle de vida d'una factura impagada

* Quan una factura esdevé impagada (es carrega una devolució del banc) avança els estats (segons el procés de tall: Per defecte / Bo social) mentre no es paga, fins a l'estat de Tall on s'acaba generant una Baixa i enviament a la CUR. Abans d'això s'enviaran varis emails i SMS de recordatori de tall.

## Cicle de vida d'una consulta pobresa

* S'obre una "Consulta de pobresa" energètica d'una pòlissa [oberta]
* Es fa la consulta a l'administració competent [pendent]
* Es tanca la "Consulta de pobresa" amb positiva / negativa en funció de la respota de l'administració pública [tancada]

## Responsable

* Equip de Gestió de Cobraments
