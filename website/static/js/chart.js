function fetch_chart_data(symbol, entries, return_trades, user, bot_id, ctx) {
    $.ajax({
        url: '/api/chart_data',
        type: 'GET',
        data: {
            symbol: symbol,
            entries: entries,
            return_trades: return_trades,
            user: user,
            bot_id: bot_id
        },
        success: function(response) {
            response = $.parseJSON(response)
            if (return_trades == 'True'){
                lineGraph = createLineGraphWithTrades(
                    ctx,
                    response['dates'], // Labels
                    response['price_data'], // Data
                    response['symbol'], // Label 
                    response['short_trades_indexes'],
                    response['long_trades_indexes'],
                    'rgba(75, 192, 192, 1)', // Line color
                    'rgba(75, 192, 192, 0.2)', // Fill color
                    'Time', // X-axis title
                    'Price in USD' // Y-axis title
                );
            } else {
                lineGraph = createLineGraph(
                    ctx,
                    response['dates'], // Labels
                    response['price_data'], // Data
                    response['symbol'], // Label 
                    'rgba(75, 192, 192, 1)', // Line color
                    'rgba(75, 192, 192, 0.2)', // Fill color
                    'Time', // X-axis title
                    'Price in USD' // Y-axis title
                );
            }

            return lineGraph;
        },
        error: function(xhr, status, error) {
            console.error('Error fetching chart data:', error);
        }
    })
}

function createLineGraphWithTrades(ctx, labels, data, label, shortPositions, longPositions, borderColor, backgroundColor, xAxisTitle, yAxisTitle) {
    const positionInfo = new Array(data.length).fill('');
    longPositions.forEach(index => positionInfo[index] = 'Long Position');
    shortPositions.forEach(index => positionInfo[index] = 'Short Position');

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
                pointRadius: data.map((_, index) => {
                    if (longPositions.includes(index) || shortPositions.includes(index)) {
                        return 5;
                    }
                    return 0;
                }),
                pointBackgroundColor: data.map((_, index) => {
                    if (longPositions.includes(index)) {
                        return '#00FF00';
                    } else if (shortPositions.includes(index)) {
                        return '#FF0000';
                    }
                    return 'transparent';
                }),
                pointStyle: 'circle',
            }]
        },
        options: {
            responsive: true,
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
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.raw;
                            const position = positionInfo[context.dataIndex];
                            return `${label}: $${value} (${position})`;
                        }
                    }
                }
            }
        }
    });
}

function createLineGraph(ctx, labels, data, label, borderColor, backgroundColor, xAxisTitle, yAxisTitle) {
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
