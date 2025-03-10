<%def name="dades_nota(info)">
    <table class="generic-table colored-window secondary-color full-width margin-bottom-15" style="text-align: left;">
        <thead>
            <tr>
                <th colspan="3">
                    <div>
                        <div>${_(u"DADES DE LA NOTA DE CÀRREC/ABONAMENT")}</div>
                    </div>
                </th>
            </tr>
        </thead>
        <tbody>
            <table>
                <tbody>
                    <tr>
                        <td>${_(u"Referència nota de càrrec")}: </td>
                        <td>${info['note_reference']}</td>
                        <td></td>
                    </tr>
                    <tr>
                        <td>${_(u"Data de la nota de càrrec")}: </td>
                        <td>${info['note_create_date']}</td>
                        <td></td>
                    </tr>
                    <tr>
                        <td>${_(u"Resum de la nota de càrrec")}: </td>
                        %if info['payment_direction'] == 'receivable':
                            <td><b>${_(u"A Cobrar")}</b></td>
                        %else:
                            <td><b>${_(u"A Pagar")}</b></td>
                        %endif
                        <td><b>${info['amount_total']}</b></td>
                    </tr>
                    <tr>
                        <td>${_(u"Data Bancàries")}: </td>
                        %if info['bank_details']:
                            <td>${info['bank_details'][:-4]} + '****'</td>
                        %else:
                            <td></td>
                        %endif
                        <td></td>
                    </tr>
                    <tr>
                        <td>${_(u"Forma de pagament")}: </td>
                        %if info['payment_method'] == 'transfer':
                            <td>${_(u"Transferència")}</td>
                        %else:
                            <td>${_(u"Rebut domiciliat")}</td>
                        %endif
                        <td></td>
                    </tr>
                </tbody>
            </table>
        </tbody>
        <tfoot>
            <tr>
                <td colspan="3"></td>
            </tr>
        </tfoot>
    </table>
</%def>