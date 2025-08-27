
document.addEventListener('DOMContentLoaded', () => {
    const map = L.map('map').setView([51.505, -0.09], 13);
    const waypoints = [];
    const waypointsDiv = document.getElementById('waypoints');
    const takeoffBtn = document.getElementById('takeoff-btn');

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    map.on('click', async (e) => {
        const { lat, lng } = e.latlng;
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`);
        const data = await response.json();
        const name = data.display_name || 'Unknown Location';

        const waypoint = {
            name: name,
            lat: lat,
            lon: lng
        };
        waypoints.push(waypoint);

        L.marker([lat, lng]).addTo(map)
            .bindPopup(`<b>${name}</b><br>Lat: ${lat.toFixed(4)}, Lon: ${lng.toFixed(4)}`)
            .openPopup();

        renderWaypoints();
    });

    function renderWaypoints() {
        waypointsDiv.innerHTML = '';
        waypoints.forEach((wp, index) => {
            const wpDiv = document.createElement('div');
            wpDiv.className = 'waypoint';
            const title = index === 0 ? 'START' : `Waypoint ${index}`;
            const waypointName = index === 0 ? 'Mission Start' : wp.name;

            wpDiv.innerHTML = `<h3>${title}</h3><p>${waypointName}</p><p>Lat: ${wp.lat.toFixed(4)}, Lon: ${wp.lon.toFixed(4)}</p>`;
            waypointsDiv.appendChild(wpDiv);
        });
    }

    takeoffBtn.addEventListener('click', async () => {
        if (waypoints.length < 2) {
            alert('Please select at least a starting point and a destination.');
            return;
        }

        try {
            const response = await fetch('/run_simulation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(waypoints)
            });

            if (response.ok) {
                alert('Simulation started successfully!');
            } else {
                alert('Failed to start simulation.');
            }
        } catch (error) {
            console.error('Error starting simulation:', error);
            alert('An error occurred while starting the simulation.');
        }
    });
});
