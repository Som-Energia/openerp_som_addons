<%def name="detall_nota(linies, info)">
    <table class="generic-table colored-window secondary-color full-width margin-bottom-15">
        <thead>
            <tr>
                <th colspan="2">
                    <div>
                        <div>${_(u"DETALL DE LA NOTA DE CÀRREC/ABONAMENT")}</div>
                    </div>
                </th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td colspan="2">
                    <table class="secondary-table invoice-data-table secondary-color colored-window w-90">
                        <thead>
                            <tr>
                                <th>
                                    <div>
                                        <div>${_(u"Nº Factura")}</div>
                                    </div>
                                </th>
                                <th>
                                    <div>
                                        <div>${_(u"Data factura")}</div>
                                    </div>
                                </th>
                                <th>
                                    <div>
                                        <div>${_(u"Concepte")}</div>
                                    </div>
                                </th>
                                <th>
                                    <div>
                                        <div>${_(u"Tipus factura")}</div>
                                    </div>
                                </th>
                                <th>
                                    <div>
                                        <div>${_(u"Moviment")}</div>
                                    </div>
                                </th>
                                <th class="border-l-black">
                                    <div>
                                        <div>${_(u"Total Factura")}</div>
                                    </div>
                                </th>
                            </tr>
                        </thead>
                        %for linia in linies:
                            <tbody>
                                %if len(linies) > 1:
                                    <tr>
                                        <td colspan="6" class="bold">
                                            <div>
                                                <div>${linia['header']}</div>
                                            </div>
                                        </td>
                                    </tr>
                                %endif
                                %for index, invoice in enumerate(linia['invoices']):
                                    <tr>
                                        <td>${invoice['number']}</td>
                                        <td>${invoice['date_invoice']}</td>
                                        <td>${invoice['concept']}</td>
                                        <td>${invoice['type']}</td>
                                        <td>${invoice['move_direction']}</td>
                                        <td class="border-l-black">${invoice['amount']}</td>
                                    </tr>
                                %endfor
                                <tr>
                                    <td colspan="5" class="h-5-mm"></td>
                                    <td class="h-5-mm border-l-black"></td>
                                </tr>
                            </tbody>
                        %endfor
                        <tfoot>
                            <tr>
                            </tr>
                            <tr>
                                <td colspan="4"></td>
                                <td class="hightlighted-field border-black">
                                    <div>
                                        <div>${_(u"Total")}</div>
                                    </div>
                                </td>
                                <td class="hightlighted-field border-black">
                                    <div>
                                        <div>${info['amount_total']} €</div>
                                    </div>
                                </td>
                            </tr>
                        </tfoot>
                    </table>
                </td>
            </tr>
        </tbody>
        <tfoot>
            <tr>
                <td colspan="2"></td>
            </tr>
        </tfoot>
    </table>
</%def>