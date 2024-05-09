<%def name="graphic(costs)">
  <script>
    var chartDom = document.getElementById('grafic-costos');
    var myChart = echarts.init(chartDom, null, { renderer: 'svg' });
    var option;

    // ECharts v5.5.0
    option = {
      animation: false,
      tooltip: {
        trigger: 'item'
      },
      title: {
        text: 'DISTRIBUCIÓ\nDELS COSTOS',
        left: 'center',
        top: 'center',
        textStyle: {
          fontSize: 12,
        }
      },
      series: [
        {
          type: 'pie',
          color: [
            '#4d4d4d',
            '#80a82d',
            '#bec8a9',
            '#71805b',
          ],
          radius: ['50%', '70%'],
          center: ['50%', '50%'],
          padAngle: 0,
          startAngle: 0,
          endAngle: 360,
          label: {
            position: 'outside',
            formatter: '{b} {d}%',
            show: true,
            fontSize: 11,
          },
          percentPrecision: 0,
          data: [
            { value: ${costs['energia'].val}, name: ${_(u'Energia')} },
            { value: ${costs['potencia'].val}, name: ${_(u'Potencia')} },
            { value: ${costs['exces'].val}, name: ${_(u'Exces')} },
            { value: ${costs['reactiva'].val}, name: ${_(u'Reactiva')} },
          ]
        }
      ]
    };
    option && myChart.setOption(option);
  </script>
</%def>
