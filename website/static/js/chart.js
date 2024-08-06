function fetch_chart_data(symbol, entries, ctx) {
    console.log('Fetching chart data');
    $.ajax({
        url: '/api/chart_data',
        type: 'GET',
        data: {
            symbol: symbol,
            entries: entries
        },
        success: function(response) {
            response = $.parseJSON(response)
            console.log('Received chart data:', response['chart_data']);
            lineGraph = createLineGraph(
                ctx,
                response['dates'], // Labels
                response['price_data'], // Data
                response['symbol'], // Label # TODO Symbol needs to be passed by API as well
                'rgba(75, 192, 192, 1)', // Line color
                'rgba(75, 192, 192, 0.2)', // Fill color
                'Time', // X-axis title
                'Price in USD' // Y-axis title
            );
            return lineGraph;
        },
        error: function(xhr, status, error) {
            console.error('Error fetching chart data:', error);
        }
    })
}

function createLineGraph(ctx, labels, data, label, borderColor, backgroundColor, xAxisTitle, yAxisTitle) {
    console.log('CREATING CHART')
    console.log(data)
    return new Chart(ctx, {
      type: 'line',
      data: {
          labels: labels,
          datasets: [{
              label: label,
              data: data,
              borderColor: borderColor,
              backgroundColor: backgroundColor,
              fill: true,
              tension: 0.4
          }]
      },
      options: {
          responsive: true,
          maintainAspectRatio: false, // Allow chart to adjust to container size
          plugins: {
              legend: {
                  display: true,
                  position: 'top',
                  labels: {
                      color: 'white'
                  }
              },
              tooltip: {
                  enabled: true,
                  mode: 'index',
                  intersect: false,
                  backgroundColor: 'rgba(0, 0, 0, 0.2)',
                  titleColor: 'white',
                  bodyColor: 'white',
                  borderColor: borderColor,
                  borderWidth: 1
              },
              zoom: {
                  pan: {
                      enabled: true,
                      mode: 'x'
                  },
                  zoom: {
                      wheel: {
                          enabled: true
                      },
                      pinch: {
                          enabled: true
                      },
                      mode: 'xy'
                  }
              }
          },
          hover: {
              mode: 'nearest',
              intersect: true
          },
          scales: {
              x: {
                  display: true,
                  title: {
                      display: true,
                      text: xAxisTitle,
                      color: 'white'
                  },
                  ticks: {
                      color: 'white'
                  }
              },
              y: {
                  display: true,
                  title: {
                      display: true,
                      text: yAxisTitle,
                      color: 'white'
                  },
                  ticks: {
                      color: 'white'
                  }
              }
          },
          animation: {
              duration: 1000,
              easing: 'easeInOutBounce'
          }
      }
  });
}
