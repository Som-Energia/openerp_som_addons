<%
def fix_name(name):
    return '<br>'.join(reversed([x.strip() for x in name.split(',')]))

def localize_period(period, locale):
    import babel
    from datetime import datetime
    dt = datetime.strptime(period, '%Y%m')
    return babel.dates.format_datetime(dt, 'LLLL yyyy', locale=locale)

def get_base_locale(locale):
    if not locale:
        return 'es'
    else:
        return locale.split('_')[0]

%>

<!doctype html>
<meta charset="utf-8">
<script type="text/javascript" src="${addons_path}/som_empowering/report/empoweringjs/bower_components/jquery/dist/jquery.min.js"></script>
<script type="text/javascript" src="${addons_path}/som_empowering/report/empoweringjs/bower_components/handlebars/handlebars.min.js"></script>
<script type="text/javascript" src="${addons_path}/som_empowering/report/empoweringjs/bower_components/bootstrap/dist/js/bootstrap.min.js"></script>
<link href="${addons_path}/som_empowering/report/empoweringjs/bower_components/bootstrap/dist/css/bootstrap.min.css" rel="stylesheet" type="text/css" charset="utf-8"/>
<script type="text/javascript" src="${addons_path}/som_empowering/report/empoweringjs/bower_components/d3/d3.min.js"></script>
<link href="${addons_path}/som_empowering/report/empoweringjs/bower_components/font-awesome/css/font-awesome.min.css" rel="stylesheet" type="text/css" charset="utf-8"/>

<script src="${addons_path}/som_empowering/report/empoweringjs/src/empowering.js" charset="utf-8"></script>
<link href="${addons_path}/som_empowering/report/empoweringjs/src/empowering.css" rel="stylesheet" type="text/css" charset="utf-8"/>

<link href="${addons_path}/som_empowering/report/report_informe_energetic.css" rel="stylesheet" type="text/css" charset="utf-8"/>
<link href="${addons_path}/som_empowering/report/style.css" rel="stylesheet" type="text/css" charset="utf-8"/>


<body>
%for contract in objects:
<% setLang(contract.titular.lang) %>
<div id="content">
    <div id="cap">
        <div id="left">
            <div id="logo"><img src="${addons_path}/som_empowering/report/logo.jpg" width="150" height="80" alt=""/></div>
            <div id="dades">
            <p class="bold">Som Energia, SCCL</p>
			<p>C/Pic de Peguera, 11. </p>
                        <p>17003- Girona</p>
			<p>infoenergia@somenergia.coop</p>
            </div>
        </div>

        <div id="right">
            <div id="informe"><h1>${_("Informe Energètic")} - <span style="font-weight:300;">${localize_period(str(period), contract.titular.lang)}</span></h1></div>
            <div id="dadespersonals">
                <div id="titolmodul" class="dadespersonals">${_("Dades personals")}</div>
                <div id="contingutpersonal">
                    <h2>${contract.titular.name | fix_name }</h2>
                    <p>${contract.cups.direccio}</p>
                    <p>${_("CUPS")}: ${contract.cups.name}</p>
                    <p>${_("Tarifa")}: ${contract.tarifa.name}</p>
                    <p>${_("Potència")}: ${contract.potencia} kW</p>
                </div>
            </div>
        </div>
    </div>
   <div style="clear:both;"></div>
    <div id="modul">
    <div id="titolmodul">${_("Comparació amb llars similars")}</div>
    <div id="continguts">
        <div id="col1">
            <p class="textpadding"><div id="ot" style="margin:2%;"><div id="ot101_template1_${contract.id}"></div></div></p>
            <p><div id="ot101_graphic_${contract.id}" style="margin:2%;"></div></p>
            <span class="peugrafica"><div id="ot101_template2_${contract.id}"></div></span>
        </div>
        <div id="col2">
            <div id="titolvaloracio">${_("Com ho estàs fent ?")}</div>
            <div id="ot101_template4_${contract.id}"></div>
            <div id="ot101_template5_${contract.id}"></div>
            <div id="ot101_template6_${contract.id}"></div>
            <br style="display:block; margin-top:10px; line-height:33px;"><span class="peugrafica"><div id="ot101_template3_${contract.id}"></div></span>
        </div>
    <div style="clear:both;"></div>
    </div>
    </div>
       <script>
            $.ajax({
                type: 'GET',
                dataType: 'json',
                url: '${heman_url}/OT101Results/${contract.name}/${period}',
                beforeSend: function (xhr) {
                    xhr.setRequestHeader("Authorization", "token ${contract.titular.empowering_token}");
                }}).done(function(data){
                    var payload = data._items[0];
                    var ot101 = Empowering.Graphics.OT101({
                        container: "#ot101_graphic_${contract.id}", data: payload,
                        height: 162, width: 250, labels: {
                            0: '${_("Llars similars")}',
                            1: '${_("Tu")}',
                            2: '${_("Llars similars eficients ")}'
                        }
                    });
                    var elem = $('#smiley_' + ot101.getRanking().toLowerCase());
                    var icon1_level = ((ot101.getRanking().toLowerCase() == "great")?'ON':'OFF');
                    var icon2_level = ((ot101.getRanking().toLowerCase() == "good")?'ON':'OFF');
                    var icon3_level = ((ot101.getRanking().toLowerCase() == "bad")?'ON':'OFF');
                    console.log(elem);
                    elem.addClass('active');
                    var template1 = Handlebars.compile(
                        '${_("Has consumit un")}' + ' <span class="empowering ot101 consumption">' +
                        '{{absInt diffAverageConsumption}}% ' +
                        '{{#positive diffAverageConsumption}}' + '${_("més")}' + '{{else}}' + '${_("menys")}' +
                        '{{/positive}}</span> ' +
                        '${_("que les llars similars i un")} ' + '<span class="ot101 consumption">' +
                        '{{absInt diffAverageEffConsumption}}% ' +
                        '{{#positive diffAverageEffConsumption}}' + '${_("més")}' + '{{else}}' + '${_("menys")}' +
                        '{{/positive}}</span> ' + '${_("que les llars similars eficients")}');
                    $('#ot101_template1_${contract.id}').html(template1(payload));

                    var template2 = Handlebars.compile(
                        '${_("Les llars similars són")}' + ' <strong>{{numberCustomers}}</strong> '
                    );
                    $('#ot101_template2_${contract.id}').html(template2(payload));

                    var percentEfficient = Math.round(ot101.getEfficientCustomersPercent());
                    var template3 = Handlebars.compile(
                        '${_("Les llars similars eficients són el")}' + ' {{pEff}}% ' + '${_("més eficient del grup de llars similars")}'
                    );
                    $('#ot101_template3_${contract.id}').html(template3({pEff: percentEfficient}));

                    $('#ot101_template4_${contract.id}').html(Handlebars.compile(
                       '<div id="icones"><div id="smiley_great"><span class="cara"><img src="${addons_path}/som_empowering/report/' + 'icon1_' + icon1_level + '.png" width="100%" alt="cara1"></span></div><span class="texticones_' + icon1_level + '">${_("Genial")}</span></div>'
                    ));
                    $('#ot101_template5_${contract.id}').html(Handlebars.compile(
                       '<br style="display:block; margin-top:10px; line-height:25px;"><div id="icones"><div id="smiley_great"><span class="cara"><img src="${addons_path}/som_empowering/report/' + 'icon2_' + icon2_level + '.png" width="100%" alt="cara1"></span></div><span class="texticones_' + icon2_level +'">${_("Bé")}</span></div>'
                    ));
                    $('#ot101_template6_${contract.id}').html(Handlebars.compile(
                       '<br style="display:block; margin-top:10px; line-height:25px;"><div id="icones"><div id="smiley_great"><span class="cara"><img src="${addons_path}/som_empowering/report/' + 'icon3_' + icon3_level + '.png" width="100%" alt="cara1"></span></div><span class="texticones_' + icon3_level + '">${_("Regular")}</span></div>'
                    ));
            });
        </script>

    <div id="modul">
    <div id="titolmodul">${_("Comparació últims 12 mesos")}</div>
    <div id="continguts">
    <p class="textpadding"><div id="ot103_template1_${contract.id}"></div></p>
    <div id="ot103_graphic_${contract.id}" style="background:#fff"></div>
    </div>
    </div>
        <script>
            $.ajax({
                type: 'GET',
                dataType: 'json',
                url: '${heman_url}/OT103Results/${contract.name}/${period}',
                beforeSend: function (xhr) {
                    xhr.setRequestHeader("Authorization", "token ${contract.titular.empowering_token}");
                }}).done(function(data){
                    var ot103 = Empowering.Graphics.OT103({
                        container: "#ot103_graphic_${contract.id}", data: data._items,
                        width: 560, height: 220, labels: {
                            0: '${_("Llars similars")}',
                            1: '${_("Tu")}',
                            2: '${_("Llars similars eficients")}'
                        }
                    });
                    var template1 = Handlebars.compile(
                        '${_("Has consumit un")}' + ' <span class="empowering ot103 consumption">' +
                        '{{absInt eff}}% ' +
                        '{{#positive eff}}' + '${_("més")}' + '{{else}}' + '${_("menys")}' +
                        '{{/positive}}</span> ' +
                        '${_("que les llars similars més eficients")}'
                    );
                    $('#ot103_template1_${contract.id}').html(template1(ot103.getDiffConsumption()));

                });

        </script>


    <!--
    <div style="clear:both;"></div>
    <div class="saltopagina"></div> -->
    <div id="modul">
    <div id="titolmodul">${_("Comparació amb el mateix mes de l'any anterior")}</div>
    <div id="continguts">
        <div id="col3"><div id="ot201_graphic_${contract.id}" style="margin:2.5%;"></div>
        </div>
        <div id="col4">
        <center><div id="ot201_template1_${contract.id}"></div></center>
        </div>
    <div style="clear:both;"></div>
    </div>
        <script>
            $.ajax({
                type: 'GET',
                dataType: 'json',
                url: '${heman_url}/OT201Results/${contract.name}/${period}',
                beforeSend: function (xhr) {
                    xhr.setRequestHeader("Authorization", "token ${contract.titular.empowering_token}");
                }}).done(function(data){
                    var ot201 = Empowering.Graphics.OT201({
                        container: "#ot201_graphic_${contract.id}", data: data._items[0],
                        width: 280, height: 200, labels: {
                            0: '${_("Consum any passat")}',
                            1: '${_("Consum actual")}'
                        }
                    });
                    var template1 = Handlebars.compile(
                      '<div id="ot201_diff{{#positive diff}}H{{else}}L{{/positive}}">' + '${_("Has consumit un")}' + '<div id="ot201_diff">{{absInt diff}}% {{#positive diff}}' + '${_("més")}' + '{{else}}' + '${_("menys")}' + '{{/positive}}' + '</div>' + '${_("que l&#39;any passat.")}</div>'
                    );
                    $('#ot201_template1_${contract.id}').html(template1({diff: ot201.getDiffConsumption()}));
                });

        </script>


    <div id="modul">
    <div id="titolmodul">${_("Consells personalitzats")}</div>
    <div id="continguts" style="height:220px;">
            <div id="ot401_graphic_${contract.id}"></div>
    </div>
    <div style="clear:both;"></div>
    </div>
        <script>
            $.ajax({
                type: 'GET',
                dataType: 'json',
                url: '${heman_url}/OT401Results/${contract.name}/${period}',
                beforeSend: function (xhr) {
                    xhr.setRequestHeader("Authorization", "token ${contract.titular.empowering_token}");
                }}).done(function(data){
                    Empowering.Graphics.OT401({
                        container: "#ot401_graphic_${contract.id}", data: data._items,
                        width: 500, height: 220, locale: "${get_base_locale(contract.titular.lang)}"
                    });
                });
        </script>
    <div id="modul">
    <div id="titolmodul">${_("Informació addicional")}</div>
    <div id="continguts">
    % if contract.tg == '1':
        - ${_("Disposes de comptador amb telegestió activada. A l'oficina virtual podràs accedir al teus consums horaris")}
    % else:
        - ${_("No disposes de comptador amb telegestió activada")}
    % endif
    </div>
    <div style="clear:both;"></div>
    </div>
<div id="footer"><p style="font-size:10px;">${_("Per a més informació pots accedir a l'oficina virtual")}.</p>
<p style="font-size:10px;">${_("Allà trobaràs serveis addicionals i tota la informació relacionada amb els teus contractes")}.</p>
<p style="font-size:10px;"><span class="destacat"><a href="http://oficinavirtual.somenergia.coop">http://oficinavirtual.somenergia.coop</a></span></p></div>
</div>
%endfor
</body>
</html>
