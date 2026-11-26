# webclient-docker

Contenidor que serveix el [webclient de GISCE](https://github.com/gisce/webclient) a partir de la darrera release publicada al repositori privat, i s'auto-actualitza cada 6 hores.

## Què fa

- Aixeca un `nginx:alpine` que escolta al port **8081** del host per defecte.
- A l'arrencada i cada `CHECK_INTERVAL` segons, consulta la release indicada per `WEBCLIENT_TAG` o, si no s'ha fixat cap tag, `latest`. Compara el `tag_name` amb el que té guardat i, si és nou, descarrega el `.zip` de la release i el descomprimeix a `/usr/share/nginx/html`.
- Exposa un `location /api` que fa proxy a `http://localhost:8068` (l'ERP del host).
- Fa servir `network_mode: host`, així que `localhost` dins el contenidor és el host real (necessari per arribar al túnel SSH lligat a 127.0.0.1).

## Requisits

- Docker i Docker Compose v2 (`docker compose ...`).
- El port 8081 del host lliure.
- L'ERP escoltant al 8068 del host (típicament via túnel SSH).
- Un **GitHub personal access token** amb permís de lectura al repo privat `gisce/webclient`:
  - **Fine-grained**: ha d'incloure l'organització `gisce`, el repo `webclient` i permís `Contents: Read` (no s'ha provat).
  - **Classic**: scope `repo`.

## Posada en marxa

1. Crea el fitxer `.env` al costat del `docker-compose.yml`:

   ```
   GITHUB_TOKEN=ghp_el_teu_token
   CHECK_INTERVAL=21600
   WEBCLIENT_REPO=gisce/webclient
   WEBCLIENT_TAG=
   WEBCLIENT_LISTEN_PORT=8081
   WEBCLIENT_API_UPSTREAM=http://localhost:8068/
   ```

   El fitxer `.env` està ignorat per Git. No hi posis cometes ni espais al voltant del `=`. També pots ometre variables: s'utilitzaran els valors per defecte de la taula de configuració. Si `GITHUB_TOKEN` ja està exportat a l'entorn des d'on executes Compose, no cal definir-lo al `.env`.

2. Arrenca:

   ```bash
   docker compose up -d --build
   ```

3. Comprova:

   ```bash
   docker compose ps
   docker compose logs -f
   ```

   El log ha de mostrar `[update-webclient] Installed <tag>`. Llavors el webclient es serveix a http://localhost:8081.

## Configuració (`.env`)

Compose llegeix aquestes variables del `.env` i les passa al contenidor. Les variables exportades a l'entorn del procés que executa Compose també es poden utilitzar.

| Variable | Valor per defecte | Descripció |
|---|---|---|
| `GITHUB_TOKEN` | buit | Token amb lectura a `gisce/webclient`. Necessari perquè el repo és privat. |
| `CHECK_INTERVAL` | `21600` | Segons entre comprovacions de noves releases (21600 = 6h). |
| `WEBCLIENT_REPO` | `gisce/webclient` | Repositori `owner/name` d'on agafar les releases. |
| `WEBCLIENT_TAG` | buit | Tag exacte de la release que es vol instal·lar, per exemple `v4.0.0-alpha.329`. Si és buit, s'utilitza `latest`. |
| `WEBCLIENT_LISTEN_PORT` | `8081` | Port on escolta Nginx al host. |
| `WEBCLIENT_API_UPSTREAM` | `http://localhost:8068/` | Destinació del proxy de `/api`. Amb `network_mode: host`, `localhost` és el host. |

Per canviar la release, edita `WEBCLIENT_TAG` al `.env` i executa `docker compose up -d`. El tag ha de coincidir exactament amb el publicat a GitHub. Compose recrearà el contenidor si detecta que la configuració ha canviat; no cal reconstruir la imatge per canviar variables del `.env`. El volum `webclient-state` es conserva.

## Canviar el port del host

Canvia `WEBCLIENT_LISTEN_PORT` al `.env` i aplica-ho amb:

```bash
docker compose up -d
```

## Canviar l'upstream de `/api`

Canvia `WEBCLIENT_API_UPSTREAM` al `.env` i executa `docker compose up -d`. Si l'ERP corre en un contenidor o màquina remota, recorda que `localhost` vol dir el host perquè el servei utilitza `network_mode: host`.

## CSS local (`custom.css`)

Pots crear `webclient-docker/custom.css` per afegir estils locals. Aquest fitxer està ignorat per Git i no s'inclou a la imatge. Compose munta la carpeta de `webclient-docker` com a només lectura a `/opt/webclient-local`; Nginx serveix `/custom.css` directament des d'aquesta carpeta. El webclient ja carrega el full d'estils si existeix.

Desa els canvis a `custom.css` i recarrega el navegador: no cal reiniciar ni recrear el contenidor. Nginx envia capçaleres perquè el navegador no reutilitzi una còpia en caché. El fitxer sobreviu a les actualitzacions del webclient perquè no es copia ni s'esborra de la carpeta que conté els fitxers de la release.

Els canvis a `nginx.conf.template` sí que requereixen reconstruir la imatge:

```bash
docker compose up -d --build
```

## Forçar una actualització ara mateix

```bash
docker compose exec webclient /usr/local/bin/update-webclient.sh
```

Si no hi ha una release nova, dirà `Already at <tag>`. Per forçar la redescarrega, esborra primer l'estat:

```bash
docker compose exec webclient rm -f /var/lib/webclient/current_tag
docker compose exec webclient /usr/local/bin/update-webclient.sh
```

## Troubleshooting

### El contenidor està en `Restarting`

L'script d'actualització ha fallat i l'entrypoint no arrenca nginx fins que la primera descàrrega tingui èxit (millor això que servir un 404 buit). Mira els logs:

```bash
docker compose logs --tail 50
```

### `curl: (22) The requested URL returned error: 401`

El token arriba al contenidor però GitHub el rebutja. Ordre de comprovacions:

1. El token funciona fora de Docker?
   ```bash
   curl -sI -H "Authorization: Bearer $GITHUB_TOKEN" \
     https://api.github.com/repos/gisce/webclient/releases/latest | head -3
   ```
2. Si dona 200 aquí i 401 dins, comprova que el contenidor rep un token (sense imprimir-lo):
    ```bash
    docker compose exec webclient sh -c 'test -n "$GITHUB_TOKEN" && echo "GITHUB_TOKEN present" || echo "GITHUB_TOKEN buit"'
    ```
3. Si dona 401 també fora: token expirat, sense SSO autoritzat a `gisce`, o sense scope suficient.

Després de corregir el `.env`, aplica el valor nou amb:

```bash
docker compose up -d
```

### `curl: (22) The requested URL returned error: 404`

Token vàlid però sense accés al repo `gisce/webclient`. Si és fine-grained, probablement no tens el repo seleccionat en crear-lo. Si és classic, necessita l'scope `repo`.

### El webclient carrega però `/api` dona 502 o no respon

L'ERP al host no és accessible des del contenidor. Comprova:

```bash
ss -ltn | grep :8068
```

Ha de sortir `0.0.0.0:8068` o `127.0.0.1:8068`. Com que el contenidor fa servir `network_mode: host`, qualsevol de les dues val.

### El port 8081 està ocupat

```bash
ss -ltn | grep :8081
```

Si hi ha una altra cosa, canvia `WEBCLIENT_LISTEN_PORT` al `.env` i executa `docker compose up -d`.

## Estructura del directori

```
webclient-docker/
├── Dockerfile              # nginx:alpine + curl/unzip/jq
├── docker-compose.yml      # network_mode: host, configura variables i munta overrides locals
├── nginx.conf.template     # plantilla de nginx per listen, /api i custom.css
├── entrypoint.sh           # update inicial + bucle + exec nginx
├── update-webclient.sh     # descàrrega/instal·lació del zip de la release
├── .dockerignore
├── .env                    # configuració local ignorada per Git
├── custom.css              # CSS local opcional, ignorat per Git
└── README.md
```

Les regles que ignoren `.env` i `custom.css` són al `.gitignore` de l'arrel del repositori.

## Aturar i netejar

```bash
docker compose down            # atura i esborra el contenidor
docker compose down -v         # també esborra el volum amb l'estat (forçarà redescarrega la propera vegada)
```
