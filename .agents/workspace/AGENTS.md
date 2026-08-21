# Workspace Som Energia — dispatcher d'agents

Aquest fitxer és el dispatcher d'un workspace multirepositori. S'ha d'exposar com a `AGENTS.md` a l'arrel del workspace (vegeu [README.md](README.md)); Pi el carregarà per a qualsevol repositori fill.

## Regles de treball generals

- Identifica primer el repositori o repositoris afectats amb `git rev-parse --show-toplevel` i mantén els canvis limitats a l'abast acordat.
- Abans d'editar, indica quin repositori o worktree és actiu i revisa `git status`.
- Si una tasca afecta més d'un repositori, enumera'ls i confirma l'abast abans de modificar-los.
- No assumeixis que les convencions, versions de Python ni comandes de test d'un repositori s'apliquen als altres.
- Cerca i llegeix la documentació, `README`, fitxers de configuració i instruccions locals del repositori objectiu abans d'executar comandes de build, test o desplegament.

## OpenERP / Som Energia

Quan la tasca afecti `openerp_som_addons`, els seus mòduls, OpenERP v5, ERP, migracions, tests amb destral, Sentry, reports contractuals, branques, commits o PRs d'aquest repositori, llegeix **abans de fer cap edició** l'`AGENTS.md` de l'arrel del checkout `openerp_som_addons` del workspace.

Aquest fitxer és la font de veritat per a l'estil, les skills, l'SDD, els tests i la política de worktrees d'`openerp_som_addons`. En particular, no creïs worktrees ni modifiquis enllaços d'addons compartits sense seguir les seves instruccions.

## Mapa del workspace

Repositoris disponibles al workspace (la llista és orientativa; comprova sempre el repositori actiu):

- ERP i add-ons: `openerp_som_addons`, `erp`, `erp-empowering`, `destral`
- Facturació, switching i integracions: `giscedata_facturacio_indexada_som`, `switching`, `sii`, `sepa`, `sermepa`, `sippers`, `ws_transactions`, `distri-remesa-parser`
- Serveis i llibreries: `aeroo`, `cchloader`, `libComXML`, `libFacturacioATR`, `minio_backend`, `mongodb_backend`, `ooop`, `ooquery`, `oorq`
- Altres productes i mòduls: `arquia`, `crm_poweremail`, `empowering`, `enerdata`, `gestionatr`, `ir_attachment_mongodb`, `openerp-sentry`, `plantmeter`, `poweremail`, `poweremail-modules`, `qreu`, `somenergia-generationkwh`

Si no queda clar quin repositori és la font de veritat, atura't després de l'anàlisi i demana confirmació.
