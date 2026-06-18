FROM nginx:alpine

RUN apk add --no-cache bash curl unzip jq ca-certificates gettext

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY update-webclient.sh /usr/local/bin/update-webclient.sh
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/update-webclient.sh /usr/local/bin/entrypoint.sh \
    && mkdir -p /var/lib/webclient \
    && rm -rf /usr/share/nginx/html/*

EXPOSE 8081

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
