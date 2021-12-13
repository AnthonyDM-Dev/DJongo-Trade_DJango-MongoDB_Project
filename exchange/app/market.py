import requests

#importing BTC value from CoinMarketCap API
class Bot_CMC:

    def __init__(self):
        # API Parameters
        self.url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        self.params = {
            'start': '1',
            'limit': '1',
            'convert': 'USD'
        }
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': '<YOUR API KEY>'
        }

    def get_data(self):
        # Gathering data
        r = requests.get(url=self.url, headers=self.headers, params=self.params).json()
        price = round(r['data'][0]['quote']['USD']['price'], 8)
        return price
