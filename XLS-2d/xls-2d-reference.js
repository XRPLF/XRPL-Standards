function xls2d(uri) {

	const cleaned_uri = uri.replace(/^(.*:.*)?\?/mg, "").replace(/\?/img, "&").replace(/^.*?:\/\//, '').replace(/^ripple:/img, "")

	function clean() {
		return cleaned_uri
	}

	function to() {
		//NB: this regex is case sensitive to assist in correctly matching XRP ledger addresses
		var match =  /(?:(?:^|&)(?:to|TO|tO|To)=|^)([rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz]{25,55})/mg.exec(cleaned_uri)
		return (match == null ? false : match[1])
	}

	function dt() {
		var match = /(?:^|&)dt=([0-9]+)|:([0-9]+)$/img.exec(cleaned_uri)
		if (match != null) return (match[1] ? match[1] : match[2])
		return false
	}

	function amount() {
		var match = /(?:^|&)am(?:oun)?t=([0-9\.]+)/img.exec(cleaned_uri)
		return (match == null ? false : match[1])
	}

	function currency() {
		var match = /(?:^|&)cur(?:rency)?=(?:([rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz]{25,55}):)?([A-Z]{3}|[A-Fa-f]{40})/img.exec(cleaned_uri)
		return (match == null ? false : { issuer: ( match[1] ? match[1] : false ), currency: match[2] } )
	}


	function invoiceid() {
		var match = /(?:^|&)inv(?:oice)?(?:id)?=([a-f]{64})/img.exec(cleaned_uri)
		return (match == null ? false : match[1])
	}


	return {
		uri: uri,
		clean: clean(),
		to: to(),
		dt: dt(),
		amount: amount(),
		currency: currency(),
		invoiceid: invoiceid()
	}
}

var examples = [
	"rPEPPER7kfTD9w2To4CQk6UCfuHM9c6GDY?dt=123",
	"rPEPPER7kfTD9w2To4CQk6UCfuHM9c6GDY:123",
	"https://ripple.com//send?to=rPEPPER7kfTD9w2To4CQk6UCfuHM9c6GDY&amount=30&dt=123",
	"https://sub.domain.site.edu.au//send?to=rPEPPER7kfTD9w2To4CQk6UCfuHM9c6GDY&amount=30&dt=123",
	"https://someapp.com/sendXrp?to=rRippleBlah&dt=4&invoiceid=abcdef",
	"deposit-xrp?to=blah",
	"?rPEPPER7kfTD9w2To4CQk6UCfuHM9c6GDY:123",
	"rAhDr1qUEG4gHXt6m6zyRE4oogDDWmYvcgotCqyyEpArk8",
	"to=rAhDr1qUEG4gHXt6m6zyRE4oogDDWmXFdzQdZdH9SJzcNJ",
	"to=rAhDr1qUEG4gHXt6m6zyRE4oogDDWmXFdzQdZdH9SJzcNJ&currency=rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B:USD",
	"to=rAhDr1qUEG4gHXt6m6zyRE4oogDDWmXFdzQdZdH9SJzcNJ&currency=USD",
	"to=rAhDr1qUEG4gHXt6m6zyRE4oogDDWmXFdzQdZdH9SJzcNJ&currency=rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B:USD&invid=DEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEF",
	"scheme://uri/folders?rPEPPER7kfTD9w2To4CQk6UCfuHM9c6GDY:123",
	"scheme://uri/folders?rPEPPER7kfTD9w2To4CQk6UCfuHM9c6GDY&amount=4:123", // this one a bit iffy
    "XVLhHMPHU98es4dbozjVtdWzVrDjtV8xvjGQTYPiAx6gwDC",
    "to=XVLhHMPHU98es4dbozjVtdWzVrDjtV8xvjGQTYPiAx6gwDC",
    "ripple:XVLhHMPHU98es4dbozjVtdWzVrDjtV1kAsixQTdMjbWi39u",
    "ripple:XVLhHMPHU98es4dbozjVtdWzVrDjtV1kAsixQTdMjbWi39u:58321",
    "ripple:XVLhHMPHU98es4dbozjVtdWzVrDjtV1kAsixQTdMjbWi39u:58321&currency=rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B:USD",
    "ripple:XVLhHMPHU98es4dbozjVtdWzVrDjtV1kAsixQTdMjbWi39u:58321&currency=XVLhHMPHU98es4dbozjVtdWzVrDjtV1kAsixQTdMjbWi39u:ABC",
    "xrpl://XVLhHMPHU98es4dbozjVtdWzVrDjtV1kAsixQTdMjbWi39u",
    "xrp://XVLhHMPHU98es4dbozjVtdWzVrDjtV1kAsixQTdMjbWi39u",
    "f3w54ygsdfgfserga"
]

for (var i in examples) console.log(xls2d(examples[i]));
