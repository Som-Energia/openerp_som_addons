function toCommaNumber(value) {
    return value.toFixed(2).replace('.', ',');
}

var total_reparto = 0;
dades_reparto.forEach(function(item) {
    total_reparto += item.value;
});

var chartDesi = echarts.init(document.getElementById('chart_desti'), null, {
    renderer: 'svg',  // needed for wkhtmltopdf
});

var stackBarSeries = dades_reparto.map(function(item, index) {
    return {
    name: item.name,
    type: 'bar',
    stack: 'cargos',
    barWidth: 30,
    data: [item.value/total_reparto*100],
    label: {
        show: true,
        position: 'right',
        distance: 10,
        formatter: ' '+toCommaNumber(item.value)+'€: '+item.name,
        color: '#333',  // needed for wkhtmltopdf
        fontSize: 10,
        overflow: 'break',
    },
    labelLine: {
        show: true,
    },
    labelLayout: function() {
        return {
        moveOverlap: 'shiftY',
        width: 200,
        dy: (stackBarSeries.length-index)*5,  // improve separation between labels
        }
    },
    animation: false,
    silent: true,
    };
});

// Render
var option = {
    grid: {
        right: '35%',
        left: '75%',
        top: '15%',
        bottom: '15%'
    },
    xAxis: {
        type: 'category',
        data: [''],
        show: false
    },
    yAxis: {
        type: 'value',
        max: 100,
        show: false
    },
    title: {
        text: "Desglose de cargos",
        right: 60,
        // borderWidth: 0,
        borderColor: 'transparent',
        textStyle: {
            fontSize: 12,
        }
    },
    color: [
        '#E3E8DF',
        '#D4DAD1',
        '#CED5D0',
        '#777777',
    ],
    series: [
    {
        type: 'pie',
        radius: '50%',
        center: ['25%', '50%'],
        data: pie_data,
        label: {
            formatter: function(params){return toCommaNumber(params.value)+' €\n'+params.name},
            color: '#333',  // needed for wkhtmltopdf
        },
        startAngle: 20,  // TODO: pensar be aixo
        animation: false,
        silent: true,
        color: [
            '#CDFF80',
            '#0B2E34',
            '#FF632B',
            '#0C4C27',
            '#AFB5E8',
        ],
    },
    ].concat(stackBarSeries),
};

chartDesi.setOption(option);
