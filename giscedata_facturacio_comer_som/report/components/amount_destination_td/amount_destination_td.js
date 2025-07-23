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

function getDashedLine(x1, y1, x2, y2) {
    return {
        type: 'line',
        shape: { x1: x1, y1: y1, x2: x2, y2: y2 },
        style: {
            stroke: '#333',
            lineWidth: 0.5,
            lineDash: "dashed",
            opacity: 1,
        },
        z: -1,
        silent: true,
        animation: false,
    };
}

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
    color: [
        '#E3E8DF',
        '#D4DAD1',
        '#CED5D0',
        '#777777',
    ],
    graphic: {
        elements: [
            getDashedLine(320, 100, 400, 100),
            getDashedLine(400, 100, 510, 30),
            getDashedLine(400, 100, 510, 170),
        ]
    },
    series: [
    {
        type: 'pie',
        radius: '50%',
        center: ['25%', '50%'],
        data: pie_data,
        label: {
            formatter: function(params){return toCommaNumber(params.value)+' €\n'+params.name},
            color: '#333',  // needed for wkhtmltopdf
            fontSize: 11,
            overflow: 'break',
        },
        startAngle: 15,
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
