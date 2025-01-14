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
                    response['short_trade_entry_prices'],
                    response['long_trade_entry_prices'],
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

function fetch_money_development_chart_data(user, bot_id, ctx){
    $.ajax({
        url: '/api/get_money_development_data/' + user + '/' + bot_id,
        type: 'GET',
        data: {
            user: user,
            bot_id: bot_id
        },
        success: function(response) {
            response = $.parseJSON(response);
            console.log(response);
            console.log('RESPONSE DATES: ' + response['dates']);
            console.log('RESPONSE MONEY: ' + response['money']);
            lineGraph = createLineGraph(
                ctx,
                response['dates'], // Labels
                response['money'], // Data
                'money', // Label 
                'rgba(75, 192, 192, 1)', // Line color
                'rgba(75, 192, 192, 0.2)', // Fill color
                'Time', // X-axis title
                'Money in BTC' // Y-axis title
            );

            return lineGraph;
        },
        error: function(xhr, status, error) {
            console.error('Error fetching money development chart data:', error);
        }
    });

}

function createLineGraphWithTrades(ctx, labels, data, label, shortPositions, longPositions, shortPrices, longPrices, borderColor, backgroundColor, xAxisTitle, yAxisTitle) {
    const positionInfo = new Array(data.length).fill('');
    const priceInfo = new Array(data.length).fill('');
    
    // Populate positionInfo and priceInfo arrays
    longPositions.forEach((index, i) => {
        positionInfo[index] = 'Long Position';
        priceInfo[index] = longPrices[i]; // Match the price for the long position
    });
    
    shortPositions.forEach((index, i) => {
        positionInfo[index] = 'Short Position';
        priceInfo[index] = shortPrices[i]; // Match the price for the short position
    });
    
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
                            const value = priceInfo[context.dataIndex];
                            const position = positionInfo[context.dataIndex];
                            return `${label}: $${value} (${position})`;
                        }
                    }
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: 'white'
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

function createHistogramChart(user, bot_id){
    const ctx = document.getElementById('trades-histogram').getContext('2d');
    let data;

    $.ajax({
        url: '/api/data_for_trades_histogram/' + user + '/' + bot_id + '/10',
        type: 'GET',
        data: {
            user: user,
            bot_id: bot_id,
            bins: '11'
        },
        success: function(response) {
            data = $.parseJSON(response);
            let bins = data['bins'];
            let counts = data['counts'];

            chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: bins,
                    datasets: [{
                        label: 'Trade Returns Distribution',
                        data: counts,
                        backgroundColor: '#4BC0C0',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 0
                    }]
                },
                options: {
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                color: 'white'
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Trade Returns',
                                color: 'white'
                            },
                            ticks: {
                                color: 'white'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Frequency',
                                color: 'white'
                            },
                            ticks: {
                                color: 'white'
                            }
                        }
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error('Error fetching trade histogram data:', error);
        }
    });
}