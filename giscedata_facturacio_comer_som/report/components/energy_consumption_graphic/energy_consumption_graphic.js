function data_max(d) {
    var maxim = d.P1;
    if(!esgran) {
        if(d.P2 != null && maxim < d.P2){
            maxim = d.P2
        }
        if(d.P3 != null && maxim < d.P3){
            maxim = d.P3
        }
        if(d.P4 != null && maxim < d.P4){
            maxim = d.P4
        }
        if(d.P5 != null && maxim < d.P5){
            maxim = d.P5
        }
        if(d.P6 != null && maxim < d.P6){
            maxim = d.P6
        }
    } else {
        if(d.P2 != null){
            maxim = d.P1 + d.P2
        }
        if(d.P3 != null){
            maxim = maxim + d.P3
        }
        if(d.P4 != null){
            maxim = maxim + d.P4
        }
        if(d.P5 != null){
            maxim = maxim + d.P5
        }
        if(d.P6 != null){
            maxim = maxim + d.P6
        }
    }
    return maxim
}

//  num_bars = data_consum[0].P2 != null ? data_consum[0].P3 != null ? 3 : 2 : 1;

if(!esgran) {
    num_bars = data_consum[0].P2 != null ? data_consum[0].P3 != null ? data_consum[0].P4 != null ?data_consum[0].P5 != null ?data_consum[0].P6 != null ? 6 : 5 : 4 : 3 : 2 : 1;
} else {
    num_bars = 1;
}

var w = 320;
var h = 200;

if (es30 && !esgran){
    w = 650;
    h = 200;
}

// marges
var marges = {left: 60, right: 5 , top: 10 , bottom: 0};

if (num_bars > 1) {
    marges.bottom = 30;
}

var graf_h = h - marges.top - marges.bottom;
var graf_w = w - marges.left - marges.right;

var bar_group_padding = 3 * num_bars;
var max_bar_group_w = graf_w / 3;
var bar_group_w = Math.min((graf_w / (data_consum.length)), max_bar_group_w);

var bar_padding = 3;
var bar_w = (bar_group_w - bar_group_padding) / num_bars;


var grad_colors_1 = [['#bdc83f', '#dde85f']];

var grad_colors_3 = [['#dde85f', '#dde85f'],
                   ['#bdc83f', '#bdc83f'],
                   ['#5b5b5b', '#5b5b5b'],
                  ];

var grad_colors = (num_bars > 1 ? grad_colors_3 : grad_colors_1)

var y_axis_left_margin = 10;

var svg = d3_antic.select("#chart_consum_" + factura_id)
    .append("svg")
      .attr("width", w)
      .attr("height", h);

var y = d3_antic.scale.linear()
        .range([graf_h, 0])
        .domain([0, d3.max(data_consum, data_max)]);

var x = d3_antic.scale.linear()
    .range([0,w])
    .domain([0, w]);

function bar_group_pos_x(d,i) { return (bar_group_w) * i + marges.left}

function bar_pos_x(d,i) { return (bar_w) * i }

svg.append("defs")
  .append("linearGradient")
    .attr("id", "grad")
    .attr("x1", "0%")
    .attr("y1", "0%")
    .attr("x2", "0%")
    .attr("y2", "100%")
  .selectAll("stop")
  .data(grad_colors[0])
    .enter()
  .append("stop")
    .attr("offset", function(d, i) { return i*100 + "%"})
    .attr("style", function(d) {return "stop-color:" + d + ";stop-opacity:1"})

svg.select("defs")
  .selectAll("linearGradient")
  .data(grad_colors)
  .enter()
  .append("linearGradient")
    .attr("id", function(d, i){return "grad" + (i + 1)})
    .attr("x1", "0%")
    .attr("y1", "0%")
    .attr("x2", "0%")
    .attr("y2", "100%")
  .selectAll("stop")
  .data(function(d,i){return d})
    .enter()
  .append("stop")
    .attr("offset", function(d, i) { return i*100 + "%"})
    .attr("style", function(d) {return "stop-color:" + d + ";stop-opacity:1"});

function aNum(d){
    return parseInt(d)
}

yAxis = d3_antic.svg.axis()
    .scale(y)
    .orient("left")
    .tickFormat(function(d) {return (d == 0 && num_bars == 1) ? "" : d + " kWh";});

svg.append("g")
    .attr("class", "yaxis")
//    .attr("transform", "translate(" + marges.left + ", " + (h - marges.bottom) + ")")
       .attr("transform", "translate(" + (marges.left - y_axis_left_margin )+ " ," + marges.top + ")")
    .call(yAxis);

svg.selectAll(".yaxis line")
    .attr("x2", w)
    .attr("x1", 0);

textWidth = d3_antic.max(svg.selectAll("g .tick text")[0], function(d) {return d.getBBox().width});

// axis de l'esquerre
svg.selectAll("g .tick")
    .append("line")
      .attr("class", "yaxis_l")
    .call(yAxis);

svg.selectAll(".yaxis_l")
    .attr("x2", - marges.left)
    .attr("x1", - textWidth - 14 );

if (num_bars == 1 )
{
    var bar = svg.selectAll('g .bar')
          .data(data_consum)
        .enter()
        .append('g')
          .attr("transform", function(d,i) {return "rotate(180 "+ (bar_group_w / 2) + ", " + (y(aNum(data_max(d))/2) + marges.top) + ") translate(-" + bar_group_pos_x(d, i) + ", 0)"})

    bar.append("rect")
            .attr("y", function(d){return y(data_max(d)) + marges.top})
            .attr("width", bar_group_w - bar_group_padding)
            .attr("height", function(d){return (graf_h) - y(data_max(d))})

    bar.append("text")
        .attr("y", function(d) {return y(data_max(d)) + marges.top})
        .attr("x", (bar_group_w - bar_group_padding)/ 2)
        .attr("dy", ".35em")
        .text(function(d){return d.mes})
}
else
{
    var bars = [];

    for(var i=0;i<num_bars;i++){
        var selector = 'g .bar' + (i + 1);
        var valor = 'P' + (i + 1);
        bars[i] = svg.selectAll(selector)
              .data(data_consum)
            .enter()
            .append('g')
              .attr("class", "bar" +  (i + 1))
              .attr("transform", function(d,j) {return "rotate(180 "+ (bar_w / 2) + ", " + (y(aNum(d[valor])/2) + marges.top) + ") translate(-" + (bar_group_pos_x(d,j) + (bar_w * i)) + ", 0)"})

        bars[i].append("rect")
                .attr("y", function(d){return y(d[valor]) + marges.top})
                .attr("width", bar_w - bar_padding)
                .attr("height", function(d){return (graf_h) - y(d[valor])})

        bars[i].append("text")
                .attr("y", function(d) {return y(d[valor]) + marges.top - 15})
                .attr("x", (bar_w - bar_padding)/ 2)
                .attr("dy", ".35em")
                .text(function(d){return valor})

    }

    svg.selectAll('g .bar1')
        .data(data_consum)
        .enter()
        .append('text')
            .attr('class', 'mes')
/*          // VERTICAL
            .attr("transform", function(d,j) {return "rotate(180 " + (bar_w/2)+ ", 0 )"})
            .attr("y", - graf_h - marges.top)
            .attr("x", function (d,i) {return - bar_group_pos_x(d,i)})*/
          // HORITZONTAL
//            .attr("transform", function(d,j) {return "rotate(180 " + (bar_w/2)+ ", 0 )"})
            .attr("y", y(0) + marges.top + marges.bottom - 10)
            .attr("x", function (d,i) {return bar_group_pos_x(d,i) + (bar_group_w - bar_group_padding)/2})
            .attr("dy", ".35em")
            .text(function(d){return d.mes})
}
