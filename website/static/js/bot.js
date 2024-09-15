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
            console.error('THIS IS THE END');
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
