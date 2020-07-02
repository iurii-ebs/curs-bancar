Currency parser
banks short names - MAIB, MICB, Victoria, Mobias, BNM

endpoints:

api/banks/get/"bank short name"/ - parse data from selected bank

api/banks/get/all/ - parse data from all (5) banks

api/banks/best/"currency abbr"/ - find best selling and buy prices, returns JSON with 2 lists

api/user/register/        Register new user 
aip/user/token/           Get Authorization Bearer Token


GET request data {'date': 'YYYY-MM-DD'} will return info for selected date

