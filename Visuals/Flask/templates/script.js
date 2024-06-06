document.addEventListener('DOMContentLoaded', function() {
    console.log('Document loaded, populating box select...');
    populateBoxSelect();
});

let myChart = null; // Global variable to hold the chart instance

function populateBoxSelect() {
    fetch('http://192.168.0.171:8888/user-boxes')
        .then(response => response.json())
        .then(data => {
            if (data.boxes) {
                const boxSelect = document.getElementById("box-select");
                data.boxes.forEach(box => {
                    const option = document.createElement("option");
                    option.value = box.id;
                    option.text = box.name;
                    boxSelect.add(option);
                });
                // Automatically populate month select for the first pit
                populateMonthSelect();
            } else {
                console.error("No boxes available");
            }
        })
        .catch(error => console.error("Error fetching boxes:", error));
}

function populateMonthSelect() {
    const boxId = document.getElementById("box-select").value;
    fetch(`http://192.168.0.171:8888/monthly-data?months_only=true&box_id=${boxId}`)
        .then(response => response.json())
        .then(data => {
            if (data.months) {
                const monthSelect = document.getElementById('month');
                monthSelect.innerHTML = ''; // Clear existing options
                const blankOption = document.createElement('option');
                blankOption.value = '';
                blankOption.text = 'Select a month';
                monthSelect.add(blankOption);
                data.months.forEach(month => {
                    const option = document.createElement('option');
                    option.value = month;
                    option.text = month;
                    monthSelect.add(option);
                });
            } else {
                console.error('No months available');
            }
        })
        .catch(error => console.error('Error fetching months:', error));
}

function fetchMonthlyData() {
    const month = document.getElementById('month').value;
    const boxId = document.getElementById("box-select").value;
    if (month === '') {
        console.log('No month selected.');
        return;
    }

    fetch(`/monthly-data?month=${month}&box_id=${boxId}`)
        .then(response => response.json())
        .then(data => {
            if (data.length) {
                const timestamps = data.map(entry => new Date(entry[0]));
                const percentages = data.map(entry => calculateFillPercentage(entry[2], entry[1]));
                renderChart(timestamps, percentages);
            } else {
                console.error('No data for the selected month:', month);
            }
        })
        .catch(error => console.error('Error fetching data:', error));
}

function calculateFillPercentage(depth, height) {
    const filledHeight = height - depth;
    return (filledHeight / height) * 100;
}

function renderChart(labels, data) {
    const ctx = document.getElementById('chart').getContext('2d');
    if (myChart) {
        myChart.destroy();
    }
    myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Fill Percentage',
                data: data,
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day'
                    },
                    adapters: {
                        date: {}
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}
