<%page args="rb" />
<style>
<%include file="rectificative_banner.css" />
</style>
% if rb.is_visible:
    <div class="rectificative_banner">
    <h1 class="rectificative_warn">${_(u"FACTURA RECTIFICATIVA PER IVA")}</h1>
        <p>
            ${_(u"Factura rectificativa de %s de data %s per causa de modificacio de base imposable i anulació de la quota repercutida conforme art. 80 Llei 24 RD 162/1992 IVA. Quota anulada: %s €") % (rb.invoice, rb.date, formatLang(rb.quota))}
        </p>
    </div>
% endif
