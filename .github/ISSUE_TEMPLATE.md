---
name: "🚀 Task for AI Agent"
about: Projecte de desenvolupament per a agents automàtics (PR generation)
title: "[TASK]: "
labels: ai-ready
assignees: ''
---

## 📝 Descripció del Problema / Objectiu
> Descriu clarament què vols aconseguir. Sigues específic amb la lògica de negoci d'OpenERP.
**Exemple:** "Necessitem afegir un nou camp 'data_finalitzacio' al model 'crm.lead' que es calculi automàticament."

## 🛠 Especificacions Tècniques
- **Mòdul afectat:** (Ex: `som_crm_custom`, `som_billing`)
- **Models implicats:** (Ex: `res.partner`, `account.invoice`)
- **Vistes a modificar:** (Ex: `view_partner_form`, `report_invoice_document`)
- **Lògica de Python:** (Descriu mètodes o constraints)

## 📂 Fitxers a crear o modificar
- [ ] `models/nom_del_fitxer.py`
- [ ] `views/nom_del_fitxer.xml`
- [ ] `security/ir.model.access.csv` (si calen nous permisos)
- [ ] `data/nom_del_fitxer.xml` (si calen dades inicials o cron jobs)

## 🧪 Requisits de Testing
- [ ] Crear un test a la carpeta `tests/` que validi la funcionalitat.
- [ ] El test ha de cobrir el cas d'ús: [Descriu el cas d'ús].

## ⚠️ Restriccions i Estil
- Segueix les convencions explicades aquí `.github/copilot-instructions.md`

---
**Nota per a l'agent:** Si us plau, genera una Pull Request amb el codi i una breu explicació del que has fet.
