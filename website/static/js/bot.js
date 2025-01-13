function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');

    const sidebarDots = document.getElementById('sidebar_dots');
    sidebarDots.classList.toggle('rotate-90');
}

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function checkTrainingStatus(user, bot_id) {
    const url = '/api/bot_training_status/' + user + '/' + bot_id;
    const trainingStatusValue = document.getElementById('training-status-value');
    const loadingAnimation = document.getElementById('loading-animation');

    // Function to check the training status
    function fetchStatus() {
        $.ajax({
            url: url,
            method: 'GET',
            success: function(data) {
                data = $.parseJSON(data);
                console.log(data); // For debugging purposes
                if (data['training'] === "True") {
                    trainingStatusValue.textContent = 'True';
                    loadingAnimation.style.visibility = 'visible';
                } else {
                    trainingStatusValue.textContent = 'False';
                    loadingAnimation.style.visibility = 'hidden';
                    checkLastTrained(user, bot_id)
                    clearInterval(intervalId); // Stop the interval
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('There was a problem with the fetch operation:', textStatus, errorThrown);
            }
        });
    }

    // Set the interval to call fetchStatus every second
    const intervalId = setInterval(fetchStatus, 1000);
}

function checkLastTrained(user, bot_id){
    const lastTrainedValue = document.getElementById('lastTrained').textContent;
    console.log("LastTrainedValue" + lastTrainedValue);
    if (lastTrainedValue.toLowerCase().includes('None'.toLowerCase())) {
        console.log("LastTrainedValue includes None --> set to hidden")
        document.getElementById('training-metrics-section').style.display = 'none';
    } else {
        console.log("LastTrainedValue does not include None --> set to visible")
        document.getElementById('training-metrics-section').style.display = 'initial';
        getErrorMetrics(user, bot_id)
    }
}

function getErrorMetrics(user, bot_id) {
    const url = '/api/bot_training_error_metrics/' + user + '/' + bot_id;

    $.get(url, function(data) {
        data = JSON.parse(data);
        console.log(data["confusion_matrix"])
        const confusionMatrix = JSON.parse(data["confusion_matrix"]);
        const accuracy = data["accuracy"];
        const balancedAccuracy = data["balanced_accuracy"];
        const precision = data["precision"];
        const recall = data["recall"];

        $('#confusion-matrix').html(`
            <table>
                <tr>
                    <th></th>
                    <th>Predicted Decreasing</th>
                    <th>Predicted Increasing</th>
                </tr>
                <tr>
                    <th>Actual Decreasing</th>
                    <td>${confusionMatrix[0][0]}</td>
                    <td>${confusionMatrix[0][1]}</td>
                </tr>
                <tr>
                    <th>Actual Increasing</th>
                    <td>${confusionMatrix[1][0]}</td>
                    <td>${confusionMatrix[1][1]}</td>
                </tr>
            </table>
        `);

        $('#accuracy').text(`Accuracy: ${accuracy}`);
        $('#balanced-accuracy').text(`Balanced Accuracy: ${balancedAccuracy}`);
        $('#precision').text(`Precision: ${precision}`);
        $('#recall').text(`Recall: ${recall}`);
    });
}

function checkBotRunning(user, bot_id){
    const button = document.getElementById('startStopBot');
    var bot_running;
    const url = '/api/bot_is_running/' + user + '/' + bot_id;
    $.ajax({
        url: url,
        type: 'GET',
        data: {
            user: user,
            bot_id: bot_id
        },
        success: function(response) {
            response = $.parseJSON(response);
            bot_running = response['running'];

            if (bot_running === 'True') {
                button.textContent = 'Stop Bot';
                button.style.backgroundColor = '#DC3545';
            } else {
                button.textContent = 'Start Bot';
                button.style.backgroundColor = '#4BC0C0';
            }
        },
        error: function(xhr, status, error) {
            console.error('Error checking if bot is running:', error);
        }
    })
}

function toggleBot(user, bot_id) {
    const button = document.getElementById('startStopBot');

    if (button.textContent === 'Start Bot') {
        button.textContent = 'Stop Bot';
        button.style.backgroundColor = '#DC3545';
        var action = 'True';
    } else {
        button.textContent = 'Start Bot';
        button.style.backgroundColor = '#4BC0C0';
        var action = 'False';
    }

    const url = '/start_stop_bot/' + user + '/' + bot_id + '/' + action;
    $.ajax({
        url: url,
        type: 'GET',
        data: {
            user: user,
            bot_id: bot_id,
            action: action
        },
        success: function(response) {

        },
        error: function(xhr, status, error) {
            console.error('Error starting / stopping bot:', error);
            console.error(url);
        }
    })
}

function initialilzeTrailingStopLoss(user, bot_id){
    var trailingStopLossElement = document.getElementById('trailingStopLoss');

    $.ajax({
        url: '/get_trailing/' + user + '/' +bot_id,
        type: 'GET',
        data: {
            user: user,
            bot_id: bot_id
        } ,
        success: function(response) {
            response = $.parseJSON(response);
            if(response['stop_loss_trailing'] == true){
                trailingStopLossElement.checked = true;
            }else{
                trailingStopLossElement.checked = false;
            }
        },
        error: function(xhr, status, error) {
            console.error('Error getting the status for the stop loss trailing checkbox: ', error);
        }
    });
}

function updateTrailingStopLoss(user, bot_id){
    var trailingStopLossElement = document.getElementById('trailingStopLoss');

    var changeTrailingStopLossTo;
    if(trailingStopLossElement.checked){
        changeTrailingStopLossTo = "true";
    }else{
        changeTrailingStopLossTo = "false";
    }
    
    $.ajax({
        url: '/set_stop_loss_trailing/' + user + '/' + bot_id + '/' + changeTrailingStopLossTo,
        type: 'POST',
        data: {
            user: user,
            bot_id: bot_id,
            trailing: changeTrailingStopLossTo
        } ,
        success: function(response) {
            console.log(response);
        },
        error: function(xhr, status, error) {
            console.error('Error setting the status for the stop loss trailing checkbox: ', error);
        }
    });
}

function updateStopLossPrice(user, bot_id, symbol, first) {
    var stopLossInput; // = document.getElementById('stopLossInput').value;
    var stopLossPriceElementShort = document.getElementById('stopLossPriceShort');
    var stopLossPriceElementLong = document.getElementById('stopLossPriceLong');
    var currentPrice;

    const url = '/api/last_price';
    $.ajax({
        url: url,
        type: 'GET',
        data: {
            symbol: symbol
        },
        success: function(response) {
            response = $.parseJSON(response);
            currentPrice = parseFloat(response['last_price']);
            if(first){
                $.ajax({
                    url: '/get_stop_loss/' + user + '/' + bot_id,
                    type: 'GET',
                    data: {
                        user: user,
                        bot_id: bot_id
                    },
                    success: function(response) {
                        response = $.parseJSON(response);
                        document.getElementById('stopLossInput').value = parseFloat(response['stop_loss'] * 100);
                        stopLossInput = document.getElementById('stopLossInput').value;
                        const stopLossPercentage = parseFloat(stopLossInput);
                        const stopLossPriceShort = currentPrice + (currentPrice * stopLossPercentage / 100);
                        const stopLossPriceLong = currentPrice - (currentPrice * stopLossPercentage / 100);
                        stopLossPriceElementShort.textContent = `Price short trades: ${stopLossPriceShort.toFixed(2)}`;
                        stopLossPriceElementLong.textContent = `Price long trades: ${stopLossPriceLong.toFixed(2)}`;
                        console.log('On load stop loss: ' + parseFloat(response['stop_loss'] * 100));
                    },
                    error: function(xhr, status, error) {
                        console.error('Error looking up stop loss value:', error);
                    }
                });
                return;
            }

            stopLossInput = document.getElementById('stopLossInput').value;
            if (stopLossInput) {
                const stopLossPercentage = parseFloat(stopLossInput);
                const stopLossPriceShort = currentPrice + (currentPrice * stopLossPercentage / 100);
                const stopLossPriceLong = currentPrice - (currentPrice * stopLossPercentage / 100);
                stopLossPriceElementShort.textContent = `Price short trades: ${stopLossPriceShort.toFixed(2)}`;
                stopLossPriceElementLong.textContent = `Price long trades: ${stopLossPriceLong.toFixed(2)}`;

                // Update the stop loss value within the database
                const update_stop_loss_url = '/set_stop_loss/' + user + '/' + bot_id + '/' + stopLossPercentage / 100;
                $.ajax({
                    url: update_stop_loss_url,
                    type: 'POST',
                    data: {
                        user: user,
                        bot_id: bot_id,
                        stop_loss: stopLossPercentage / 100
                    },
                    success: function(response) {
                        console.log('Stop loss value updated successfully:', response);
                    },
                    error: function(xhr, status, error) {
                        console.error('Error updating stop loss value:', error);
                        console.error(update_stop_loss_url);
                    }
                })
            } else {
                stopLossPriceElementShort.textContent = 'Price short trades: --';
                stopLossPriceElementLong.textContent = 'Price long trades: --';
            }
        },
        error: function(xhr, status, error) {
            console.error('Error getting last price:', error);
        }
    })
}

function updateTakeProfitPrice(user, bot_id, symbol, first) {
    var takeProfitInput; // = document.getElementById('takeProfitInput').value;
    var takeProfitPriceElementShort = document.getElementById('takeProfitPriceShort');
    var takeProfitPriceElementLong = document.getElementById('takeProfitPriceLong');
    var currentPrice;

    const url = '/api/last_price';
    $.ajax({
        url: url,
        type: 'GET',
        data: {
            symbol: symbol
        },
        success: function(response) {
            response = $.parseJSON(response);
            currentPrice = parseFloat(response['last_price']);
            if(first){
                $.ajax({
                    url: '/get_take_profit/' + user + '/' + bot_id,
                    type: 'GET',
                    data: {
                        user: user,
                        bot_id: bot_id
                    },
                    success: function(response) {
                        response = $.parseJSON(response);
                        document.getElementById('takeProfitInput').value = parseFloat(response['take_profit'] * 100);
                        takeProfitInput = document.getElementById('takeProfitInput').value;
                        const takeProfitPercentage = parseFloat(takeProfitInput);
                        const takeProfitPriceShort = currentPrice + (currentPrice * takeProfitPercentage / 100);
                        const takeProfitPriceLong = currentPrice - (currentPrice * takeProfitPercentage / 100);
                        takeProfitPriceElementShort.textContent = `Price short trades: ${takeProfitPriceShort.toFixed(2)}`;
                        takeProfitPriceElementLong.textContent = `Price long trades: ${takeProfitPriceLong.toFixed(2)}`;
                        console.log('On load stop loss: ' + parseFloat(response['take_profit'] * 100));
                    },
                    error: function(xhr, status, error) {
                        console.error('Error looking up stop loss value:', error);
                    }
                });
                return;
            }

            takeProfitInput = document.getElementById('takeProfitInput').value;
            if (takeProfitInput) {
                const takeProfitPercentage = parseFloat(takeProfitInput);
                const takeProfitPriceShort = currentPrice + (currentPrice * takeProfitPercentage / 100);
                const takeProfitPriceLong = currentPrice - (currentPrice * takeProfitPercentage / 100);
                takeProfitPriceElementShort.textContent = `Price short trades: ${takeProfitPriceShort.toFixed(2)}`;
                takeProfitPriceElementLong.textContent = `Price long trades: ${takeProfitPriceLong.toFixed(2)}`;

                // Update the stop loss value within the database
                const update_take_profit_url = '/set_take_profit/' + user + '/' + bot_id + '/' + takeProfitPercentage / 100;
                $.ajax({
                    url: update_take_profit_url,
                    type: 'POST',
                    data: {
                        user: user,
                        bot_id: bot_id,
                        take_profit: takeProfitPercentage / 100
                    },
                    success: function(response) {
                        console.log('Stop loss value updated successfully:', response);
                    },
                    error: function(xhr, status, error) {
                        console.error('Error updating stop loss value:', error);
                        console.error(update_take_profit_url);
                    }
                })
            } else {
                takeProfitPriceElementShort.textContent = 'Price short trades: --';
                takeProfitPriceElementLong.textContent = 'Price long trades: --';
            }
        },
        error: function(xhr, status, error) {
            console.error('Error getting last price:', error);
            console.error(url);
        }
    })
}