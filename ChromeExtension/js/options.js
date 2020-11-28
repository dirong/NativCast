function saveSettings() {
	localStorage.nc_raspip = document.getElementById("raspip").value;
	localStorage.nc_cmd = document.getElementById("cmd").value;
	localStorage.nc_user = document.getElementById("user").value;

	var radios = document.getElementsByName('cmFunction');
	for (var i = 0, length = radios.length; i < length; i++) {
	    if (radios[i].checked) {
		localStorage.nc_cmFunction = radios[i].value;
		break;
	    }
	}

	var radios = document.getElementsByName('mode_slow');
	for (var i = 0, length = radios.length; i < length; i++) {
	    if (radios[i].checked) {
		localStorage.nc_modeslow = radios[i].value;
		break;
	    }
	}

	alert("Settings were successfully saved !");
}

document.addEventListener("DOMContentLoaded", function() {
	if (localStorage.nc_raspip != undefined) {
		document.getElementById("raspip").value = localStorage.nc_raspip;
	} else {
		document.getElementById("raspip").value = "raspberrypi.local";
		localStorage.nc_raspip = 'raspberrypi.local';
	}

	if (localStorage.nc_cmFunction == undefined) {
		localStorage.nc_cmFunction = "stream";
		document.getElementById("cmFstream").checked = true;
	} else {
		if (localStorage.nc_cmFunction == "stream") {
			document.getElementById("cmFstream").checked = true;
		} else {
			document.getElementById("cmFqueue").checked = true;
		}
	}

	if (localStorage.nc_modeslow == undefined) {
		localStorage.nc_modeslow = "False";
		document.getElementById("high_qual").checked = true;
	} else {
		if (localStorage.nc_modeslow == "False") {
			document.getElementById("high_qual").checked = true;
		} else {
			document.getElementById("bad_qual").checked = true;
		}
	}

	var el = document.getElementById("saveButton");
	el.addEventListener("click", saveSettings, false);
});
