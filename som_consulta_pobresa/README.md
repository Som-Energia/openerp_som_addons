# som_consulta_pobresa

Mòdul per gestionar les peticions de pobresa energètica dels contractes amb factures impades, als ajuntaments

## Models

* som.consulta.pobresa: Hereda de crm.case i representa una consulta a una administració pública sobre si aquell titular es una persona suscetible de ser considerada pobresa energètica
* agrupacions.supramunicipals: Administracions públiques competents per gestionar aquestes consultes

## Funcionalitats

* Polissa -> Acció 'Crear consulta pobresa': Assitent que des de una pòlissa, permet crear una consulta pobresa. Es pot cridar per múltiples pòlisses a la vegada.

## Cicle de vida

* S'obre una "Consulta de pobresa" energètica d'una pòlissa [oberta]
* Es fa la consulta a l'administració competent [pendent]
* Es tanca la "Consulta de pobresa" amb positiva / negativa en funció de la respota de l'administració pública [tancada]

## Responsable

* Equip de Gestió de Cobraments
