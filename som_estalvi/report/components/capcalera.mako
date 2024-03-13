<%def name="capcalera(titular)">
    <div class="container">
        <div class="dades-titular">
            <table>
                <tr>
                    <td>Nom:</td>
                    <td><b>${titular['nom']}</b></td>
                </tr>
                <tr>
                    <td>Adreça:</td>
                    <td><b>${titular['adreca']}</b></td>
                </tr>
                <tr>
                    <td>CUPS:</td>
                    <td><b>${titular['cups']}</b></td>
                </tr>
                <tr>
                    <td>Peatge:</td>
                    <td><b>${titular['peatge']}</b></td>
                </tr>
                <tr>
                    <td>Tarifa:</td>
                    <td><b>${titular['tarifa']}</b></td>
                </tr>
            </table>
        </div>
        <div class="titol">
            <span>INFORME ANUAL</span>
            <img class="logo" src="${addons_path}/som_estalvi/report/assets/logo.svg" alt="Logo SomEnergia">
        </div>
    </div>
</%def>
