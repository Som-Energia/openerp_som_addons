<%page args="d" />
    <br />
    <br />
    <br />
    % if d.show_atr_disclaimer:
        ${_("<b>Informació addicional: Si ho requereix aquest organisme, SOM ENERGIA SCCL s’ofereix a entregar els arxius .xml en format original.</b>")}<br />
        <br />
    % endif
    ${_(u"Data de generació del document:")} ${d.create_date}<br />
    ${_(u"Informe automàtic generat des de Som Energia")}<br />
