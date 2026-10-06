---
name: update-contract-report
description: >
  Actualitza plantilles de reports contractuals o legals a partir de documents font
  (docx o markdown) mantenint la lògica del report intacta.
  Trigger: Quan necessites actualitzar un report legal, condicions particulars,
  condicions específiques, plantilles .mako contractuals, o passar canvis d'un docx/md a un report.
metadata:
  author: fran
  version: "1.0"
---

## When to Use

Utilitza aquesta skill quan:
- Has d'actualitzar el contingut d'un report `.mako` a partir d'un document legal nou
- El text font està en `.docx`, `.md` o un document equivalent lliurat per negoci/legal
- Estàs treballant amb condicions particulars, condicions específiques o annexos contractuals
- Vols preservar la lògica existent del report i només canviar el contingut

## Patró Crític

### 1. La font de veritat mana

- Si l'usuari diu que el `.docx` és la font canònica, el `.docx` mana
- Si l'usuari diu que el `.md` és la font canònica, el `.md` mana
- No barrejar fonts sense confirmar quina és la bona

### 2. NO tocar la lògica si no cal

En aquest tipus de tasca, normalment **NO** s'ha de tocar:
- `report_backend_*.py`
- condicions de render com `mostra_indexada`
- selecció d'idioma
- registres XML del report

Només s'ha de tocar el que representa el text:
- plantilles `.mako`
- HTML intern del report
- notes al peu, enllaços, fórmules, subtítols

### 3. Ignorar marques editorials del document font

Si el `.docx` conté:
- text en vermell
- highlights
- comentaris
- canvis visuals de control

**No** s'han de traslladar al report final.

Només s'ha de conservar:
- contingut final
- estructura del document
- fórmules
- subíndexs/superíndexs
- notes al peu
- enllaços

### 4. Convertir format, no copiar Word/Markdown cegament

- `.docx` → extreure contingut i traslladar-lo a HTML/Mako net
- `.md` → convertir-lo manualment a HTML del report
- Mai enganxar markup cru de Word o Markdown dins del `.mako`

### 5. Preservar semàntica visual important

Cal conservar correctament:
- `<h3>` per seccions
- `<p>` per paràgrafs/clàusules
- `<ul>` / `<ol>` per llistes o subapartats
- `<sub>` / `<sup>` per fórmules (`P<sub>OsOm</sub>`, `h<sub>i</sub>`)
- notes al peu amb ancoratges coherents
- `<a href="...">` per enllaços

### 5.bis Preservar format semàntic contractual

En aquest tipus de report, el format també pot tenir valor contractual o estructural.

Cal preservar quan sigui consistent i clarament aprovat:
- negreta en termes definits o frases destacades
- subapartats numerats o alfabetitzats (`1.`, `2.`, `a.`, `b.`, `c.`)
- referències a annexos o conceptes jurídics destacats de manera consistent
- subratllat **només** si està confirmat com a part del document final aprovat

No s'ha de traslladar automàticament:
- text en vermell
- highlights
- comentaris
- diferències visuals puntuals o inconsistents entre idiomes no validades
- subratllats dubtosos o que no es repeteixen de forma consistent

Regla pràctica:
- si el dubte és de contingut o estructura, el `docx` mana
- si el dubte és de format visual final (per exemple negretes), i hi ha PDF final aprovat, el `pdf` és la font de veritat visual

### 6. Revisió CA/ES obligatòria

Si hi ha versió catalana i castellana:
- comprovar que tenen el mateix contingut de fons
- detectar diferències editorials o jurídiques
- no assumir que una és traducció perfecta de l'altra sense validar-ho

## Workflow Recomanat

### Pas 1: Identificar la font i els targets

Exemples típics:
- font: `*.docx` o `*.md`
- target: `report/*.mako`

### Pas 2: Verificar què és contingut i què és presentació editorial

Checklist:
- [ ] El color del document és semàntic o només visual?
- [ ] Hi ha comentaris o control de canvis que s'han d'ignorar?
- [ ] El document font ja és el text final aprovat?

### Pas 3: Comparar contra el `.mako` actual

Buscar:
- clàusules noves
- clàusules modificades
- correccions puntuals
- canvis de numeració
- fórmules i símbols
- canvis d'enllaços o notes

### Pas 3.bis: Verificar el format visual aprovat

Si hi ha dubtes d'estil o d'èmfasi:
- usar el `pdf` final com a font de veritat visual
- usar el `docx` com a font de text i estructura base
- comparar què va en negreta, què forma part d'una llista i què és només soroll editorial

Heurística recomanada:
- el `pdf` serveix per detectar què es veu en negreta real
- el `docx` serveix per reconstruir text, estructura i semàntica
- no automatitzar canvis de format a cegues si el PDF fragmenta spans o si CA/ES divergeixen

### Pas 4: Actualitzar el `.mako`

Regles:
- mantenir `<%def ...>`
- mantenir salts de pàgina i contenidors del report
- substituir només el cos textual necessari
- corregir typos evidents si l'usuari els ha confirmat com a typos
- quan el document font tingui subapartats aprovats, reflectir-los com a estructura HTML real (`<ol>`, `<ul>`, `<li>`) sempre que no trenqui el report
- traduir la negreta contractual a `<b>` o `<strong>` només als fragments que realment toqui
- no propagar subratllat si no està validat explícitament

### Pas 5: Revisió final

Verificar:
- HTML vàlid i llegible
- sense colors/editorials de Word
- sense syntax Markdown restant
- sense regressions a anchors/notes
- coherència entre versions idiomàtiques
- negretes contractuals preservades quan pertoqui
- llistes i subapartats reflectits correctament
- si `docx` i `pdf` discrepen en format, s'ha seguit el criteri confirmat per l'usuari o editorial

## Heurística de Formats

| Format font | Preferència | Notes |
|-------------|-------------|-------|
| `md` | Alta | Menys soroll, menys tokens, més fàcil de comparar |
| `docx` | Alta si és la font legal real | Més fidel a fórmules i estructura, però més càrrega de conversió |
| `pdf` text | Alta com a font visual | Molt útil per validar negretes i èmfasi finals, però pitjor per reconstruir estructura |
| imatge/pdf escanejat | Baixa | OCR i risc d'errors |

## Commands

```bash
# Inspeccionar fitxers del report
git diff -- report/path/file.mako

# Extreure el contingut XML d'un docx (read-only)
unzip -p "document.docx" word/document.xml

# Veure estat abans de commit
git status --short
```

## Checklist de sortida

- [ ] El `.mako` reflecteix el contingut del document font
- [ ] No s'ha copiat cap estil editorial temporal (vermell, highlights, etc.)
- [ ] La lògica Python del report no s'ha tocat innecessàriament
- [ ] Les fórmules i subíndexs s'han preservat bé
- [ ] CA i ES s'han revisat si existeixen les dues versions
- [ ] Les negretes contractuals del document aprovat s'han preservat
- [ ] Les llistes i subapartats (`1.`, `2.`, `a.`, `b.`, `c.`) s'han reflectit correctament
- [ ] No s'han traslladat subratllats o altres estils sense validació explícita
- [ ] Si `docx` i `pdf` discrepaven en format, s'ha seguit el criteri confirmat
