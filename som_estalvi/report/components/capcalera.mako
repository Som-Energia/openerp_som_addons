<%def name="capcalera(titular)">
    <div class="container">
        <div class="dades-titular">
            <table>
                <tr>
                    <td>${_(u"Nom:")}</td>
                    <td><b>${titular['nom']}</b></td>
                </tr>
                <tr>
                    <td>${_(u"Adreça:")}</td>
                    <td><b>${titular['adreca']}</b></td>
                </tr>
                <tr>
                    <td>${_(u"CUPS:")}</td>
                    <td><b>${titular['cups']}</b></td>
                </tr>
                <tr>
                    <td>${_(u"Peatge:")}</td>
                    <td><b>${titular['peatge']}</b></td>
                </tr>
                <tr>
                    <td>${_(u"Tarifa:")}</td>
                    <td><b>${titular['tarifa']}</b></td>
                </tr>
            </table>
        </div>
        <div class="titol">
            <span>${_(u"INFORME ANUAL")}</span>
            <img class="logo" src="${addons_path}/som_assets/img/logo.svg" alt="Logo SomEnergia">
        </div>
    </div>
</%def>
