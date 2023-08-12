import numpy as np
from AlgorithmImports import *


class MultidimensionalTransdimensionalSplitter(QCAlgorithm):

    def Initialize(self):
        self.SetCash(100000)

        self.SetStartDate(2017, 1, 1)
        self.SetEndDate(2023, 1, 1)

        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        self.lookback = 20 # days to look back to breakout point
        
        self.ceiling, self.floor = 30, 10 # limits in days

        self.ininitialStopRisk = 0.98
        self.trailingStopRisk = 0.95
        
        # When the method "EveryMarketOpen" is called
        self.Schedule.On(self.DateRules.EveryDay(self.symbol),\
            self.TimeRules.AfterMarketOpen(self.symbol, 20),\
            Action(self.EveryMarketOpen))

    # Plot Info
    def OnData(self, data: Slice):
        self.Plot("Data Chart", self.symbol, self.Securities[self.symbol].Close)

    # Method that makes trading
    def EveryMarketOpen(self):
        self.highestPrice = 0
        # Brings info for past 30 days
        close = self.History(self.symbol,\
             31, Resolution.Daily)["close"]
        todayvol = np.std(close[1:31])
        yesterdayvol = np.std(close[0:30])
        deltavol = (todayvol - yesterdayvol) / todayvol
        self.lookback = round(self.lookback * (1 + deltavol))

        if self.lookback > self.ceiling:
            self.lookback = self.ceiling
        elif self.lookback < self.floor:
            self.lookback = self.floor
        
        self.high = self.History(self.symbol, self.lookback,\
            Resolution.Daily)["high"]

        if not self.Securities[self.symbol].Invested and \
            self.Securities[self.symbol].Close >= max(self.high[:-1]):
            self.SetHoldings(self.symbol, 1)
            self.breakoutlvl = max(self.high[:-1])
            self.highestPrice = self.breakoutlvl
        
        # Trading stop loss (If I've invested)
        if self.Securities[self.symbol].Invested:
            if not self.Transactions.GetOpenOrders(self.symbol):
                self.stopMarketTicket = self.StopMarketOrder(self.symbol,\
                     -self.Porfolio[self.symbol].Quantity,\
                         self.ininitialStopRisk * self.breakoutlvl) # "-" is equal to sell order

        if self.Securities[self.symbol].Close > self.highestPrice and\
            self.ininitialStopRisk * self.breakoutlvl < self.Securities[self.symbol].Close * self.trailingStopRisk:
            self.highestPrice = self.Securities[self.symbol].Close
            updateFields = UpdateOrderFields()
            updateFields.StopPrice = self.Securities[self.symbol].Close * self.trailingStopRisk
            self.stopMarketTicket.Update(updateFields)
        
            # Check new order price
            self.Debug(updateFields.StopPrice)
        
        self.Plot("Data Chart", "Stop Price", self.stopMarketTicket.Get(OrderField.StopPrice))