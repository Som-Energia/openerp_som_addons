<%page args="id_tec271" />
<style>
<%include file="invoice_details_tec271.css" />
</style>
    % if id_tec271.is_visible:
        <div class="destination">
            <div class="supl">
                <h1 style="font-weight: bold; font-size:1.2em; padding: 0em 0.5em 0.5em 0.5em;">${_(u"TAULA DETALLADA DELS SUPLEMENTS AUTONÒMICS 2013 (*)")}</h1>
                ${id_tec271.html_table}
                En caso de que el importe total de la regularización supere los dos euros, sin incluir impuestos, el mismo será fraccionado en partes iguales superiores a 1€ por las empresas comercializadoras en las facturas que se emitan en el plazo de 12 meses a partir de la primera regularización
                <br>
                * Tabla informativa conforme a lo establecido en la TEC/271/2019 de 6 de marzo, por la cual le informamos de los parámetros para el cálculo de los suplementos territoriales facilitados por su empresa distribuidora ${id_tec271.distri_name}
                <br>
                ${id_tec271.text}
            </div>
        </div>
    % endif
