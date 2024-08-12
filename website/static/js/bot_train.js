// Function to set max attribute to current date and time considering user's time zone
function setMaxDate() {
    const now = new Date();
    const localDateTime = new Date(now.getTime() - (now.getTimezoneOffset() * 60000)).toISOString().slice(0, 16);
    document.getElementById('startTime').max = localDateTime;
    document.getElementById('endTime').max = localDateTime;
}

// Set max date when the page loads
window.onload = setMaxDate;

// Function to handle "Until now" checkbox and set current date and time to endTime field
document.getElementById('untilNow').addEventListener('change', function () {
    if (this.checked) {
        const now = new Date();
        const localDateTime = new Date(now.getTime() - (now.getTimezoneOffset() * 60000)).toISOString().slice(0, 16);
        document.getElementById('endTime').value = localDateTime;
    } else {
        document.getElementById('endTime').value = '';
    }
});

// Function to handle checkbox and data percentage input
document.getElementById('useAllData').addEventListener('change', function () {
    const dataPercentageInput = document.getElementById('dataPercentage');
    if (this.checked) {
        dataPercentageInput.value = 100;
        dataPercentageInput.disabled = true;
    } else {
        dataPercentageInput.disabled = false;
    }
});

document.getElementById('dataPercentage').addEventListener('input', function () {
    const useAllDataCheckbox = document.getElementById('useAllData');
    if (this.value != 100) {
        useAllDataCheckbox.checked = false;
    }
});
