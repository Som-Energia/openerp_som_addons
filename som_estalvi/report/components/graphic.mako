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
          // adjust the start and end angle
          startAngle: 0,
          endAngle: 360,
          label: {
              show: true,
              fontSize: 12,
            },
          data: [
            { value: 3137.65, name: "Energia" },
            { value: 765.14, name: "Potencia" },
            { value: 41.45, name: "Exces" },
            { value: 81.19, name: "Reactiva" },
          ]
        }
      ]
    };
    option && myChart.setOption(option);
  </script>
</%def>
