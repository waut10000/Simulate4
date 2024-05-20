document.addEventListener('DOMContentLoaded', function() {
    console.log('Document loaded, populating month select...');
    populateMonthSelect();
});

let myChart = null; // Global variable to hold the chart instance

function populateMonthSelect() {
    fetch('http://192.168.0.171:8888/monthly-data?months_only=true')
        .then(response => response.json())
        .then(data => {
            if (data.months) {
                const monthSelect = document.getElementById('month');
                // Add a blank option
                const blankOption = document.createElement('option');
                blankOption.value = '';
                blankOption.text = 'Select a month';
                monthSelect.add(blankOption);

                // Populate the rest of the options
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
    if (month === '') {
        // Do nothing if no month is selected
        console.log('No month selected.');
        return;
    }

    fetch(`http://192.168.0.171:8888/monthly-data?month=${month}`)
        .then(response => response.json())
        .then(data => {
            console.log('Monthly data received:', data);  // Log the received data
            if (data.length) {
                const timestamps = data.map(entry => new Date(entry[0]));
                const percentages = data.map(entry => calculateFillPercentage(entry[2], entry[1]));
                console.log('Timestamps:', timestamps);    // Log timestamps
                console.log('Percentages:', percentages);  // Log percentages
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
    console.log('Rendering chart with labels:', labels);  // Log labels
    console.log('Rendering chart with data:', data);      // Log data

    const ctx = document.getElementById('chart').getContext('2d');

    // If a chart instance exists, destroy it before creating a new one
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
                        date: {} // Removed the locale reference
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
