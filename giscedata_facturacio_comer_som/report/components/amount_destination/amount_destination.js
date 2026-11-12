var w = 750;
var h = 200;

var marges = {left: 5, right: 5 , top: 5 , bottom: 5};

var graf_h = h - marges.top - marges.bottom;
var graf_w = w - marges.left - marges.right;

var dades_chart = [];
var acum = 0;

// pie border
var pie_border = 5;

//pie start_position
var pie_left = 130;

var bar_margin = 100;
var bar_border = 5;
var bar_width = 65;

var pie_center = [(pie_left + (h / 2) - marges.top - marges.bottom), (h/2)]
var bar_offset = (pie_center[0] + (h / 2) - marges.top - marges.bottom + bar_margin)

dades_chart.push({perc0:0, perc1:100, codi: 'FONS', text:'', w:0});
for(var i=0;i<pie_data.length;i++){
    perc = (pie_data[i].val / pie_total) * 100
    dades_chart.push({perc0: acum,
                      perc1: (acum + perc),
                      codi: (pie_data[i].code),
                      //text: " " + perc + "%:",
                      text: pie_etiquetes[pie_data[i].code].t,
                      w: pie_etiquetes[pie_data[i].code].w})

    acum += perc;
}

var svg = d3_antic.select("#chart_desti_" + factura_id)
        .append("svg")
        .attr("width", w)
        .attr("height", h);

var escala = d3_antic.scale.linear().domain([0, 100]).range([0, 2 * Math.PI]);

var arc = d3_antic.svg.arc()
        .innerRadius('0')
        .outerRadius(function (d) {return (h / 2) - marges.top - marges.bottom - (d.codi=='FONS' ? 0 : pie_border)})
        .startAngle(function (d){return escala(d.perc0)}) // alert(escala(d['perc0']))
        .endAngle(function (d){ return escala(d.perc1)});

var fons = d3_antic.svg.arc()
        .innerRadius('0')
        .outerRadius(function (d) {return (h / 2) - marges.top - marges.bottom})
        .startAngle(0)
        .endAngle(360)

var porcions = svg.selectAll("path")
    .data(dades_chart)
        .enter()
    .append("g");

porcions.append("path")
        .attr("d", arc)
        .attr("transform", function (d) {return "translate(" + pie_center[0] + " , " + pie_center[1] + ")"})
        .attr("class", function(d) {return("porcio " + d.codi)});

function label_pos(d) {
    c = arc.centroid(d);
    return "translate(" + (c[0] + pie_center[0] - (c[0]<0 ? d.w : 0)) + ", " + (c[1] + pie_center[1]) + ")"
}

function label_reparto_pos(d) {
    return "translate(" + (bar_width - (bar_border)) + ", 0)"
}

var pie_etiquetes = porcions.append("foreignObject")
         .attr("class",function(d) {return(d.codi)})
         .attr("transform", label_pos)
         .attr("width", function(d) {return d.w})
         .attr("height", "100%")
         .append("xhtml:body")
         .append("div")
         .attr("class","etiqueta ")
         .selectAll("p")
            .data(function(d) {return(d.text)})
            .enter()
         .append("p")
            .text(function(d) {return d})

// BAR DATA
var y = d3_antic.scale.linear()
        .range([0, graf_h - bar_border * 2 ])
        .domain([0, 100])

svg.append("g")
      .attr("transform", function(d) {return "translate(" + bar_offset + "," + (marges.top + bar_border) + ")"})
      .append("rect")
      .attr("width", bar_width + 2 * bar_border)
      .attr("x",0)
      .attr("y",-marges.bottom)
      .attr("height",graf_h)
      .attr("class", "bar_f");

var barra = svg.selectAll("g .reparto")
              .data(dades_reparto)
            .enter()
            .append("g")
            .attr("transform", function(d){return "translate(" + bar_offset + "," + (marges.top + bar_border) + ")"})

barra.append("rect")
            .attr("width", bar_width)
            .attr("y",function(d) {return y(d[0][0])})
            .attr("height",function(d) {return y((d[0][1] - d[0][0]))})
            .attr("x", bar_border)
            .attr("class", function (d) {return "bar_" + d[1]})

barra.append("text")
            .attr("y",function(d){return y(d[0][0] + ((d[0][1] - d[0][0])/2))})
            .attr("x", bar_width / 2)
            .attr("class", function (d) {return "bar_t_" + d[1]})
            .text(function(d){return d[3] + "€"})
            .style("fill", "#ffffff")
            .style("text-anchor", "middle")

reparto_etiquetes = barra.append("foreignObject")
         .attr("class",function(d) {return(d.codi)})
         .attr("transform", label_reparto_pos)
         .attr("width", 300)
         .attr("height", "100%")
         .attr("y", function(d){return y(d[0][0] + ((d[0][1] - d[0][0])/2)) - 10})
         .append("xhtml:body")
         .append("div")
         .attr("class","etiqueta_reparto")
         .append("p")
            .text(function(d) {return d[2]})

// LINIES
svg.append("g")
    .append("line")
    .attr("x1", pie_center[0])
    .attr("x2", bar_offset + bar_border)
    .attr("y1", marges.top + pie_border + pie_border)
    .attr("y2", marges.top + bar_border + 1)
    .style("stroke", "#000000")
    .style("stroke-width", 1)


var x_norm = Math.sin(escala(dades_chart[1].perc1))
var y_norm = Math.cos(escala(dades_chart[1].perc1))

svg.append("g")
    .append("line")
    .attr("x1", pie_center[0] + x_norm * ((h / 2) - marges.top - marges.bottom - pie_border))
    .attr("x2", bar_offset + bar_border)
    .attr("y1", pie_center[1] - (y_norm * ((h / 2) - marges.top - marges.bottom - pie_border)))
    .attr("y2", graf_h)
    .style("stroke", "#000000")
    .style("stroke-width", 1)
