function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');

    const sidebarDots = document.getElementById('sidebar_dots');
    sidebarDots.classList.toggle('rotate-90');
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
                    clearInterval(intervalId); // Stop the interval
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('There was a problem with the fetch operation:', textStatus, errorThrown);
            }
        });
    }

    // Set the interval to call fetchStatus every second
    const intervalId = setInterval(fetchStatus, 1000); // TODO Change interval to 1000ms
}
