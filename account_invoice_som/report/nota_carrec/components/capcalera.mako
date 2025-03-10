<%def name="capcalera(issuer, recipient, banners)">
    <%
        logo_company = banners.get('logo', False)
    %>
    <div class="flex-container header">
        %if logo_company:
            <div>
                <img src="data:image/png;base64,${logo_company}" alt="Company logo" style="max-height: 50px;"/>
            </div>
        %endif
        <div>
            ${_(u"NOTA DE CÀRREC/ABONAMENT")}
        </div>
    </div>
    <div class="flex-container margin-bottom-15">
        <table class="generic-table colored-window secondary-color w-50mm">
            <thead>
                <tr>
                    <th colspan="2">
                        <div>
                            <div>${_(u"EMISSORA")}</div>
                        </div>
                    </th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>${issuer['name']}</td>
                </tr>
                <tr>
                    <td>${issuer['vat']}</td>
                </tr>
                <tr>
                    <td>${issuer['street']}</td>
                </tr>
                <tr>
                    <td>${issuer['city']}</td>
                </tr>
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="2"></td>
                </tr>
            </tfoot>
        </table>
        <table class="generic-table colored-window secondary-color generic-table-green w-50mm">
            <thead>
                <tr>
                    <th colspan="2">
                        <div>
                            <div>${_(u"DESTINATÀRIA")}</div>
                        </div>
                    </th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>${recipient['name']}</td>
                </tr>
                <tr>
                    <td>${recipient['vat']}</td>
                </tr>
                <tr>
                    <td>${recipient['street']} - ${recipient['zip']} - ${recipient['city']}</td>
                </tr>
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="2"></td>
                </tr>
            </tfoot>
        </table>
    </div>
</%def>