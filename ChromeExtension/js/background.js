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
		var newURL = "http://"+localStorage.getItem('nc_raspip')+":2020"+url;
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
    console.log(url);
    toDataURL(url, function(base64img) {
        try {
            var newURL = "http://"+localStorage.getItem('nc_raspip')+":2020/image";
            if (response == 1) {
                notif("NativCast", "Processing Image.");
            }
            var req = new XMLHttpRequest();
            req.open('POST', newURL, true);
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
            data = base64img.split(",");
            type = data[0].split(";");
            req.send("data="+encodeURIComponent(base64img));
        } 
        catch(err) {
            alert("Error ! Make sure the ip/port are corrects, and the server is running.")
            return "wrong";
        }
    });
}


chrome.contextMenus.onClicked.addListener(function(info) {
	if(info.menuItemId == "Castnow") {
		var url_encoded_url = encodeURIComponent(info.linkUrl);
		if (localStorage.nc_cmFunction == "stream") {
			mkrequest("/stream?url="+url_encoded_url+"&slow="+localStorage.nc_modeslow, 1);
		} else {
			mkrequest("/queue?url="+url_encoded_url+"&slow="+localStorage.nc_modeslow, 0);
		}
	}
	else {
		mkimgrequest(info.srcUrl, 1);
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
    try {
        if(str.localeCompare(info.srcUrl) == 0) {
            chrome.contextMenus.remove("Castimagenow");
        }
    }
    catch (err) {
    }
}

function toDataURL(url, callback) {
    if(url.includes("data:image")) {
        callback(url);
    }
    else {
        var xhr = new XMLHttpRequest();
        xhr.onload = function() {
            var reader = new FileReader();
            reader.onloadend = function() {
                callback(reader.result);
            }
            reader.readAsDataURL(xhr.response);
        };
        xhr.open('GET', url);
        xhr.responseType = 'blob';
        xhr.send();
    }
}