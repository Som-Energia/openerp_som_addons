function data_sum(d) {
    var maxim = d.P1;
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
    return maxim
}

function data_average() {
    total_sum = 0;
    data_consum.forEach(function(d) {
        total_sum = total_sum + data_sum(d);
    });
    return total_sum / data_consum.length;
}

if(!esgran) {
    num_bars = data_consum[0].P2 != null ? data_consum[0].P3 != null ? data_consum[0].P4 != null ?data_consum[0].P5 != null ?data_consum[0].P6 != null ? 6 : 5 : 4 : 3 : 2 : 1;
} else {
    num_bars = 1;
}

w = 650;
h = 200;

var marges = {left: 60, right: 5 , top: 10 , bottom: 40};

var graf_h = h - marges.top - marges.bottom;
var graf_w = w - marges.left - marges.right;

// Main graphic (container)
var svg = d3.select("#chart_consum_" + factura_id)
  .append("svg")
    .attr("width", w)
    .attr("height", h)
  .append("g")
    .attr("transform",
          "translate(" + marges.left + "," + marges.top + ")");

// List of subgroups (periodes)
var subgroups = Object.keys(data_consum[0]).filter(function(key){return key[0] == "P"}).sort()

// List of groups (months)
var groups = d3.map(data_consum, function(d){return(d.mes)}).keys()

// <-- X AXIS -------------
var x = d3.scaleBand()
    .domain(groups)
    .range([0, graf_w])
    .padding([0.2])
svg.append("g")
  .attr("class", "xaxis")
  .attr("transform", "translate(0," + graf_h + ")")
  .call(d3.axisBottom(x).tickSizeOuter(0));
// -- X AXIS ------------->

// <-- Y AXIS -------------
var y = d3.scaleLinear()
  .domain([0, d3.max(data_consum, data_sum)])
  .range([ graf_h, 0 ]);
svg.append("g")
.attr("class", "yaxis")
.call(
  d3.axisLeft(y)
  .tickFormat(function(d) {return (d == 0 && num_bars == 1) ? "" : d + " kWh";}));

svg.selectAll(".yaxis line")
    .attr("x2", w)
    .attr("x1", 0);

svg.selectAll("g .tick")
.append("line")
    .attr("class", "yaxis_l")
.call(y);

textWidth = d3.max(svg.selectAll(".yaxis .tick text").nodes(), function(d) {return d.getBBox().width});
svg.selectAll(".yaxis_l")
    .attr("x2", - marges.left)
    .attr("x1", - textWidth - 14 );
// -- Y AXIS ------------->

if (num_bars == 1 ){ // 3X and 6X
    var gradient = svg.append("defs").append("linearGradient")
    .attr("id", "svgGradient")
    .attr("x1", "0%")
    .attr("x2", "100%")
    .attr("y1", "0%")
    .attr("y2", "100%");
    gradient.append("stop")
    .attr('class', 'start')
    .attr("offset", "0%")
    .attr("stop-color", "#dde85f")
    .attr("stop-opacity", 1);
    gradient.append("stop")
    .attr('class', 'end')
    .attr("offset", "100%")
    .attr("stop-color", "#bdc83f")
    .attr("stop-opacity", 1);

    // Show the bars
    svg.append("g")
    .selectAll("g")
    .data(data_consum)
    .enter().append("rect")
    .attr("x", function(d) { return x(d.mes); })
    .attr("y", function(d) { return y(data_sum(d)); })
    .attr("height", function(d) {return (graf_h) - y(data_sum(d))})
    .attr("width",x.bandwidth())
    .attr("fill", "url(#svgGradient)");

} else { // 20TD
    // color palette = one color per subgroup (periode)
    var color = d3.scaleOrdinal()
    .domain(subgroups)
    .range(['#dde85f','#bdc83f','#0B2E34'])

    // stack per subgroup (periode)
    var stackedData = d3.stack()
    .keys(subgroups)
    (data_consum)

    // Show the bars
    svg.append("g")
    .selectAll("g")
    // Enter in the stack data = loop key per key = group per group (month)
    .data(stackedData)
    .enter().append("g")
    .attr("fill", function(d) { return color(d.key); })
    .selectAll("rect")
    // enter a second time = loop subgroup per subgroup (periode) to add all rectangles
    .data(function(d) { return d; })
    .enter().append("rect")
        .attr("x", function(d) { return x(d.data.mes); })
        .attr("y", function(d) { return y(d[1]); })
        .attr("height", function(d) { return y(d[0]) - y(d[1]); })
        .attr("width",x.bandwidth())

    // Average line
    average = data_average()
    svg.append("line")
    .attr("x1", x(1))
    .attr("x2", graf_w)
    .attr("y1", y(average))
    .attr("y2", y(average))
    .attr("stroke", "#446bc1")
    .attr("stroke-width", 1);

    // <-- LEGEND -------------
    legendSpace = (graf_w/(subgroups.length+1)); // spacing for the legend
    subgroups.forEach(function(d,i) {

    svg.append("circle")
        .attr("cx", (legendSpace/2)+i*legendSpace)  // space legend
        .attr("cy", graf_h + (marges.bottom/2) + 8)
        .attr("r", 5)
        .style("fill", function(){ return d.color = color(d)})

    svg.append("text")
        .attr("x", 10+(legendSpace/2)+i*legendSpace)  // space legend
        .attr("y", graf_h + (marges.bottom/2)+ 10)
        .attr("class", "legend")    // style the legend
        .text(function(){
            if ("labels" in data_consum[0]){
                return data_consum[0]["labels"][d]
            } else {return d}}
        );

    });
    svg.append("line")
    .attr("x1", (legendSpace/2)+subgroups.length*legendSpace)
    .attr("x2", 7+(legendSpace/2)+subgroups.length*legendSpace)
    .attr("y1", graf_h + (marges.bottom/2) + 8)
    .attr("y2", graf_h + (marges.bottom/2) + 8)
    .attr("stroke", "#446bc1")
    .attr("stroke-width", 1);

    svg.append("text")
    .attr("x", 10+(legendSpace/2)+subgroups.length*legendSpace)  // space legend
    .attr("y", graf_h + (marges.bottom/2)+ 10)
    .attr("class", "legend")    // style the legend
    .text(average_text);
    // -- LEGEND ------------->
}
