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
<emoji> (<modul o context>) Cosa que fa el commit
```

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
🐛 (polissa) Fix error en càlcul de factura
✨ (gurb) Afegir camp assigned_betas_kw al CAU
♻️ (switching) Refactoritzar _is_m1_closable
✅ (gurb) Afegir test per a totals de betes
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

## Decisions arquitectòniques

Per entendre per què fem servir certes eines i patrons, consulta:

- [.github/docs/arquitectura.md](arquitectura.md) — Decisions d'arquitectura
- [.github/docs/estil.md](estil.md) — Estil de codi
- [.github/docs/evitar.md](evitar.md) — Patrons a evitar
