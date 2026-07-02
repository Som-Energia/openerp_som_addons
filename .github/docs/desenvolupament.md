# Guia de desenvolupament per a Som Energia (OpenERP 5.0)

## Documentació principal

Aquest fitxer recull informació d'alt nivell i decisions tècniques. Per a receptes pràctiques:

- **Receptes**: [docs/patterns/](../docs/patterns/)
- **Guies**: [Guies](../docs/guides/)
- **Skills**: [.agents/skill-registry.md](../../.agents/skill-registry.md)

---

## Estil de programació

Seguir [.github/docs/estil.md](estil.md) i [.github/docs/evitar.md](evitar.md).

---

## Convenció de commits

Els missatges de commit segueixen el format:

```
<emoji> <description>
```

La descripció ha d'estar en anglès, en imperatiu, i no ha d'incloure `feat:`, `fix:` ni cap altre type textual.

Emojis disponibles (basats en [gitmoji](https://gitmoji.dev/)):

| Emoji | Tipus |
|-------|-------|
| ✨ | Nova funcionalitat (feat) |
| 🐛 | Correcció de bug (fix) |
| 🩹 | Correcció menor (mini-fix) |
| 👔 | Lògica de negoci (business logic) |
| 🗃️ | Dades XML (data xml) |
| 🏗️ | Build / estructura |
| 🔧 | CI / configuració |
| 📝 | Documentació |
| ⚡️ | Rendiment (perf) |
| ♻️ | Refactorització |
| 🎨 | Estil de codi |
| 🧹 | Neteja (cleanup) |
| 🦺 | Codi robust |
| ✅ | Testos |
| 🚧 | Treball en curs (WIP) |
| 🌐 | Traduccions (i18n) |
| 💄 | Visual |
| 🏳️ | Abandonat (giveup) |
| 🐬 | Informes (reports) |
| 🔨 | Script de migració |

Exemples:
```
🐛 fix invoice calculation error
✨ add assigned_betas_kw field to CAU
♻️ refactor _is_m1_closable flow
✅ add tests for beta totals
```

---

## SDD (Spec-Driven Development)

El projecte utilitza SDD per gestionar canvis:

| Fase | Descripció |
|------|------------|
| `sdd-explore` | Investigar i entendre |
| `sdd-propose` | Crear proposta |
| `sdd-spec` | Escriure especificacions |
| `sdd-design` | Disseny tècnic |
| `sdd-tasks` | Dividir en tasques |
| `sdd-apply` | Implementar |
| `sdd-verify` | Verificar contra specs |
| `sdd-archive` | Archivar canvi |

---

## Dependències externes clau

L'entorn ERP depén de diversos repositoris clonats al mateix nivell que aquest repo (`../`):

- `Som-Energia/erp` (PowerERP/OpenERP core, privat)
- `Som-Energia/libFacturacioATR`
- `Som-Energia/omie-modules` + `Som-Energia/OMIE`
- `Som-Energia/somenergia-generationkwh`
- `gisce/oorq` (cua de jobs asíncrons)
- `poweremail`, `openerp-sentry`, `ws_transactions`, `ir_attachment_mongodb`, `mongodb_backend`

---

## Regla crítica sobre `__terp__.py`

Abans d'afegir una dependència nova a `depends`, comprovar si el mòdul destí ja depèn del mòdul actual.

**No es poden introduir dependències circulars entre addons.**

Exemple de què **no** s'ha de fer:

- `som_polissa_condicions_generals` depèn de `som_leads_polissa`
- afegir després `som_polissa_condicions_generals` a `depends` de `som_leads_polissa`

Aquest patró trenca la càrrega de mòduls, pot impedir arrencar el servidor i també pot bloquejar l'execució de tests.

Si falta wiring entre dos mòduls que ja tenen una direcció de dependència definida, cal resoldre-ho d'una d'aquestes maneres:

- moure el botó / report / vista al mòdul que ja és a la part alta de la dependència
- crear un mòdul pont específic
- desacoblar l'accés mitjançant herència o extensió, però **sense** invertir la dependència

---

## Decisions arquitectòniques

Per entendre per què fem servir certes eines i patrons, consulta:

- [.github/docs/arquitectura.md](arquitectura.md) — Decisions d'arquitectura
- [.github/docs/estil.md](estil.md) — Estil de codi
- [.github/docs/evitar.md](evitar.md) — Patrons a evitar
