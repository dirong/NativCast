function stopNote() {
	chrome.notifications.clear('notif', function(id) { console.log("Last error:", chrome.runtime.lastError); });
}

function notif(title, msg) {
	var opt = {
		type: "basic",
		title: title,
		message: msg,
		iconUrl: "48.png"
	};

	chrome.notifications.create('notif', opt, function(id) { console.log("Last error:", chrome.runtime.lastError); });

	setTimeout(stopNote, 4000);		
}


function mkrequest(url, response) {
	try {
		var newURL = "http://"+localStorage.getItem('raspip')+":2020"+url;
		if (response == 1) {
			notif("NativCast", "Processing video. Please wait ~ 10 seconds.");
		}
		var req = new XMLHttpRequest();
		req.open('GET', newURL, true);
		req.onreadystatechange = function (aEvt) {
			if (req.readyState == 4) {
				if (req.status == 200) {
					if (response == 1) {
						if (req.responseText == "1") {
							notif("NativCast", "Video should now start playing.");	
						} else if (req.responseText == "2") {
							notif("NativCast", "Video has been added to queue.");	
						} else {
							notif("Error", "Please make sure the link is compatible");
						}
					}
				} else {
					chrome.notifications.clear('notif', function(id) { console.log("Last error:", chrome.runtime.lastError); });
					alert("Error during requesting from server ! Make sure the ip/port are corrects, and the server is running.");
				}
			}
		};
		req.send(null);
	} 
	catch(err) {
		alert("Error ! Make sure the ip/port are corrects, and the server is running.")
		return "wrong";
	}
}

function mkimgrequest(url, response) {
	try {
		var newURL = "http://"+localStorage.getItem('raspip')+":2020"+url;
		if (response == 1) {
			notif("NativCast", "Processing Image.");
		}
		var req = new XMLHttpRequest();
		req.open('GET', newURL, true);
		req.onreadystatechange = function (aEvt) {
			if (req.readyState == 4) {
				if (req.status == 200) {
					if (response == 1) {
						if (req.responseText == "1") {
							notif("NativCast", "Image should now displayed.");
						}
						else {
							notif("Error", "Please make sure the link is compatible");
						}
					}
				} else {
					chrome.notifications.clear('notif', function(id) { console.log("Last error:", chrome.runtime.lastError); });
					alert("Error during requesting from server ! Make sure the ip/port are corrects, and the server is running.");
				}
			}
		};
		req.send(null);
	} 
	catch(err) {
		alert("Error ! Make sure the ip/port are corrects, and the server is running.")
		return "wrong";
	}
}


chrome.contextMenus.onClicked.addListener(function(info) {
	if(info.menuItemId == "Castnow") {
		var url_encoded_url = encodeURIComponent(info.linkUrl);
		if (localStorage.cmFunction == "stream") {
			mkrequest("/stream?url="+url_encoded_url+"&slow="+localStorage.modeslow, 1);
		} else {
			mkrequest("/queue?url="+url_encoded_url+"&slow="+localStorage.modeslow, 0);
		}
	}
	else {
		mkimgrequest("/image?"+info.srcUrl, 1);
	}
});

chrome.runtime.onInstalled.addListener(function() {
	chrome.tabs.create({url: "../options.html"});
});

chrome.contextMenus.create({
	id: "Castnow",
	title: "Cast Video",
	contexts: ["link"]
});

chrome.contextMenus.create({
	id: "Castimagenow",
	title: "Cast Image",
	contexts: ["image"]
}, checkImageUrl
);

function checkImageUrl(info) {
	var str = "undefined";
	if(str.localeCompare(info.srcUrl) == 0) {
		chrome.contextMenus.remove("Castimagenow");
	}
}

