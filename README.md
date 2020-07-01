Currency parser
banks short names - MAIB, MICB, Victoria, Mobias, BNM

endpoints:

banks/get/"bank short name"/ - parse data from selected bank

banks/get/all/ - parse data from all (5) banks

banks/best/"currency abbr"/ - find best selling and buy prices, returns JSON with 2 lists


GET request data {'date': 'YYYY-MM-DD'} will return info for selected date