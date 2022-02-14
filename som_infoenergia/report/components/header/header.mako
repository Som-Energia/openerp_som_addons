<%page args="d" />
<p class="data-oferta">${_(u'%s') % d.data_oferta}</p>
<p class="codi-oferta">${_(u'%s') % d.codi_oferta}</p>
<table class="header-oferta">
    <tr>
        <td style="text-align: left;">
            ${_(u'%s') % d.nom_titular}
        </td>
        <td style="text-align: right;">
            ${_(u'%s') % d.data_oferta}
        </td>
    </tr>
</table>