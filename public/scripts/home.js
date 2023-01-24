window.onload = () => {
	google.charts.load("current", {"packages": ["corechart"]});
	google.charts.setOnLoadCallback(() => {
		let data_temperature = new google.visualization.DataTable();
		let data_humidity = new google.visualization.DataTable();

		data_temperature.addColumn("string", "time_stamp");
		data_temperature.addColumn("number", "temperature");
		
		data_humidity.addColumn("string", "time_stamp");
		data_humidity.addColumn("number", "humdity");

		let options = {
			'width': window.innerWidth,
			'height': 300
		};

		fetch("/data", {
			method: "GET",
			headers: {
				"Content-Type": "application/json"
			}
		})
		.then(res => res.json())
		.then(res => {
			let d1 = [], d2 = [];
			for (let i = 0; i < res.length; i++) {
				let day = res[i][0][0], hour = res[i][0][1], min = res[i][0][2];
				min += 30;
				if (min >= 60) { hour += 1; min -= 60; }
				hour += 5;
				if (hour >= 24) { day += 1; hour -= 24; }
				
				d1.push([`${hour}:${min}`, res[i][1]]);
				d2.push([`${hour}:${min}`, res[i][2]]);
			}
			data_temperature.addRows(d1);
			data_humidity.addRows(d2);

			let c1 = new google.visualization.LineChart(document.querySelector("#chart-temperature"));
			let c2 = new google.visualization.LineChart(document.querySelector("#chart-humidity"));
			c1.draw(data_temperature, options);
			c2.draw(data_humidity, options);
		});
	});
};