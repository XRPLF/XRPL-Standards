function xls2d(uri) {

	const cleaned_uri = uri.replace(/^(.*:.*)?\?/mg, "").replace(/\?/img, "&")

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
