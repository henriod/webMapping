//Initialize leaflet map and provide default values
var map = L.map("map", { attributionControl: false }).setView(
    [51.505, -0.09],
    13
);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
}).addTo(map);

//Initialize leaflet-geoman draw controls
map.pm.addControls({
    position: "topleft",
    drawCircle: false,
});
//To run add function on page load
loadLocations();

//Request data from the database and add to map in this case points
function loadLocations() {
    $.ajax({
        url: "/api/locations/",
        async: true,
        type: "GET",
        dataType: "json",
        success: function (results) {
            // console.log(ConvertToCSV(results));
            features = [];
            results.forEach((element) => {
                var marker = L.marker([element.lat, element.lon]);
                features.push(marker);
            });
            L.featureGroup(features).addTo(map);
        },
        erro: function (xhr, resp, text) {
            console.log(xhr, resp, text);
        },
    });
}
//Perform post request when leaflet geoman draw action is completed
map.on("pm:create", ({ workingLayer }) => {
    self_drawn = map.pm.getGeomanDrawLayers(true);
    $.ajax({
        url: "/api/query/",
        async: true,
        type: "POST",
        dataType: "json",
        data: JSON.stringify(self_drawn.toGeoJSON().features[0].geometry),
        headers: {
            "Content-Type": "application/json",
        },
        success: function (results) {
            self_drawn.bindPopup(
                results.value.toString(),
                // add some popup css if you like
                {
                    maxHeight: 500,
                    minWidth: 180,
                    maxWidth: 220,
                }
            );
        },
        erro: function (xhr, resp, text) {
            console.log(xhr, resp, text);
        },
    });
});
// add point to database on map click
map.on("click", onMapClick);
function onMapClick(e) {
    var popLocation = e.latlng;
    var marker = L.marker([popLocation.lat, popLocation.lng]).addTo(map);
    //Reverse Geocode lat lon of any point
    var LocationName;
    $.ajax({
        url: "https://nominatim.openstreetmap.org/reverse?" + "lat=" + popLocation.lat + "&lon=" + popLocation.lng + "&format=geojson",
        type: "GET",
        dataType: "json",
        success: function (request) {
            LocationName = request.features[0].properties.display_name;
            return LocationName
        },
        erro: function (xhr, resp, text) {
            console.log(xhr, resp, text);
        },
    })
    //Get location from database using ajax request
    $.ajax({
        url: "/api/locations/",
        async: true,
        type: "GET",
        dataType: "json",
        success: function (results) {
            // console.log(ConvertToCSV(results));
            features = [];
            results.forEach((element, index) => {
                // Use OSRM to get direction from click location to various locations from database
                $.ajax({
                    url:
                        "http://router.project-osrm.org/route/v1/driving/" +
                        popLocation.lng +
                        "," +
                        popLocation.lat +
                        ";" +
                        element.lon +
                        "," +
                        element.lat +
                        "?geometries=geojson",
                    type: "GET",
                    dataType: "json",
                    success: function (results) {
                        //Get duration and distance to those points and populate the table with it
                        var table = document.getElementById("tablebody");
                        var row = table.insertRow(0);
                        var cell1 = row.insertCell(0);
                        var cell2 = row.insertCell(1);
                        var cell3 = row.insertCell(2);
                        var cell4 = row.insertCell(3);
                        cell1.innerHTML = LocationName;
                        cell2.innerHTML = element.value;
                        cell3.innerHTML = (results.routes[0].duration / 60).toFixed(2);
                        cell4.innerHTML = (results.routes[0].distance / 1000).toFixed(2);

                        //Build route geojson form the reponse of osrm route search from clicked location to saved location in database
                        features.push(results.routes[0].geometry);
                        L.geoJSON(features).addTo(map);
                    },
                    erro: function (xhr, resp, text) {
                        console.log(xhr, resp, text);
                    },
                });
            });
        },
        erro: function (xhr, resp, text) {
            console.log(xhr, resp, text);
        },
    });
    // To post the clicked point to the database
    // $.ajax({
    //     url: "/api/locations/",
    //     async: true,
    //     type: 'POST',
    //     dataType: 'json',
    //     data: JSON.stringify(mydata),
    //     headers: {
    //         'Content-Type': 'application/json'
    //     },
    //     success: function (results) {
    //         console.log(results);
    //     },
    //     erro: function (xhr, resp, text) {
    //         console.log(xhr, resp, text)
    //     }
    // })
}

// JSON to CSV Converter
function ConvertToCSV(objArray) {
    var array = typeof objArray != "object" ? JSON.parse(objArray) : objArray;
    var str = "";

    for (var i = 0; i < array.length; i++) {
        var line = "";
        for (var index in array[i]) {
            if (line != "") line += ",";

            line += array[i][index];
        }

        str += line + "\r\n";
    }

    return str;
}


