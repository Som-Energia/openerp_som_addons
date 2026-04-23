# webclient-docker

Contenidor que serveix el [webclient de GISCE](https://github.com/gisce/webclient) a partir de la darrera release publicada al repositori privat, i s'auto-actualitza cada 6 hores.

## Què fa

- Aixeca un `nginx:alpine` que escolta al port **8081** del host.
- A l'arrencada i cada `CHECK_INTERVAL` segons, consulta `api.github.com/repos/gisce/webclient/releases/latest`, compara el `tag_name` amb el que té guardat, i si és nou descarrega el `.zip` de la release i el descomprimeix a `/usr/share/nginx/html`.
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

1. Crea el fitxer `.env` al costat del `docker-compose.yml` (ja està a `.gitignore`):

   ```
   GITHUB_TOKEN=ghp_el_teu_token
   ```

   Sense cometes ni espais.

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

## Configuració (variables d'entorn)

| Variable | Defecte | Descripció |
|---|---|---|
| `GITHUB_TOKEN` | — | Token amb lectura a `gisce/webclient`. Obligatori (repo privat). |
| `CHECK_INTERVAL` | `21600` | Segons entre comprovacions de noves releases (21600 = 6h). |
| `WEBCLIENT_REPO` | `gisce/webclient` | Repositori `owner/name` d'on agafar les releases. |

## Canviar el port del host

Per defecte nginx escolta al 8081. Amb `network_mode: host` el port del contenidor és directament el port del host, així que per canviar-lo cal editar la directiva `listen` a `nginx.conf` i reconstruir:

```bash
docker compose up -d --build
```

## Canviar l'upstream de `/api`

Si l'ERP no és al 8068 del host, edita `nginx.conf`:

```nginx
location /api {
    proxy_pass http://localhost:NOU_PORT/;
    ...
}
```

i reconstrueix. Si l'ERP corre en un contenidor o màquina remota, recorda que `localhost` aquí vol dir el host (estem en `network_mode: host`).

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
2. Si dona 200 aquí i 401 dins: problema al `.env` (cometes, CRLF, espais). Mira què veu el contenidor:
   ```bash
   docker compose exec webclient printenv GITHUB_TOKEN
   ```
3. Si dona 401 també fora: token expirat, sense SSO autoritzat a `gisce`, o sense scope suficient.

Després de corregir el `.env`, cal recrear el contenidor perquè agafi el valor nou:

```bash
docker compose up -d --force-recreate
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

Si hi ha una altra cosa, canvia el `listen` a `nginx.conf` i reconstrueix.

## Estructura del directori

```
webclient-docker/
├── Dockerfile              # nginx:alpine + curl/unzip/jq
├── docker-compose.yml      # network_mode: host, llegeix .env
├── nginx.conf              # listen 8081 + location /api
├── entrypoint.sh           # update inicial + bucle + exec nginx
├── update-webclient.sh     # descàrrega/instal·lació del zip de la release
├── .dockerignore
├── .gitignore              # protegeix el .env local
├── .env                    # (no committejat) GITHUB_TOKEN=...
└── README.md
```

## Aturar i netejar

```bash
docker compose down            # atura i esborra el contenidor
docker compose down -v         # també esborra el volum amb l'estat (forçarà redescarrega la propera vegada)
```
