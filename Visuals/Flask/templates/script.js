window.onload = function() {
    fetchData();
};

function fetchData() {
    fetch('http://192.168.0.171:8888/water-level')
        .then(response => response.json())
        .then(data => {
            if (data.hasOwnProperty('percent')) {
                const countElement = document.getElementById('count');
                const waterElement = document.getElementById('water');
                countElement.innerText = data.percent;
                waterElement.style.transform = 'translate(0,' + (100 - data.percent) + '%)';
            } else {
                console.error('Invalid data format:', data);
            }
        })
        .catch(error => console.error('Error fetching data:', error));
}

function loadData() {
    fetchData(); // Reload data when button is pressed
}
