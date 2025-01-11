from config import ALLOCATIONS
from logger_config import logger
from config import API_KEY, API_SECRET, API_DOMAIN
from api_kraken import KrakenAPI

# Portfolio balances
class Portfolio:
    def __init__(self, allocations: dict, total_btc: float):
        self.allocations = allocations
        self.total_btc = total_btc
        self.portfolio = {
            'HODL': total_btc * allocations['HODL'],
            'YIELD': total_btc * allocations['YIELD'],
            'TRADING': total_btc * allocations['TRADING'],
        }

    def rebalance(self):
        self.total_btc = sum(self.portfolio.values())
        self.portfolio['HODL'] = self.total_btc * self.allocations['HODL']
        self.portfolio['YIELD'] = self.total_btc * self.allocations['YIELD']
        self.portfolio['TRADING'] = self.total_btc * self.allocations['TRADING']
        logger.info(f"Portfolio rebalanced: {self.portfolio}")

    

# Initialize Portfolio
kraken_api = KrakenAPI(API_KEY, API_SECRET, API_DOMAIN)
total_btc = kraken_api.get_total_btc_balance()
logger.info(f"Your total BTC balance is: {total_btc}")
portfolio = Portfolio(ALLOCATIONS, total_btc)

def rebalance_portfolio():
    portfolio.rebalance()