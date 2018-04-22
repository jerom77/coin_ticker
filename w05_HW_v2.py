# -*- coding: utf-8 -*-
"""
Created on Mon Apr 23 00:19:46 2018

@author: tykil
"""

import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
import pykorbit

form_class = uic.loadUiType("mywin_v2.ui")[0]
currency_list = ["BTC", "ETH", "BCH", "ETC"]

class Worker(QThread):
    worker_finished = pyqtSignal(list)

    def run(self):
        # 금액 조회
        prices = []
        for currency in currency_list:
            price = pykorbit.get_current_price(currency.lower() + "_krw")
            prices.append(price)

        # 일이 끝나면 시그널 emit
        self.worker_finished.emit(prices)


class Worker2(QThread):
    worker2_finished = pyqtSignal(list)

    def run(self):
        # 최근 5일 조회
        ma5_list = []
        for currency in currency_list:
            df = pykorbit.get_daily_ohlc(currency, period=5)
            ma5 = df['close'].rolling(window=5).mean()[-1]
            ma5_list.append(ma5)

        # 일이 끝나면 시그널 emit
        self.worker2_finished.emit(ma5_list)
        

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.loop_count = 0
        self.err_count = 0
        
        self.cur_prices = []
#        for currency in currency_list:
#            price = pykorbit.get_current_price(currency.lower() + "_krw")
#            self.cur_prices.append(price)
            
        self.last_ma5_list = []
        for currency in currency_list:
            df = pykorbit.get_daily_ohlc(currency, period=5)
            ma5 = df['close'].rolling(window=5).mean()[-1]
            self.last_ma5_list.append(ma5)

        # Worker 객체 - 현재가 조회
        self.worker = Worker()
        self.worker.worker_finished.connect(self.update_price)
        
        # Worker2 객체 - MA5 
        self.worker2 = Worker2()
        self.worker2.worker2_finished.connect(self.update_ma5)

        # 타이머 객체 생성 for 현재가 조회
        timer = QTimer(self)
        timer.start(2500)
        timer.timeout.connect(self.check_state)
        
        # 타이머 객체 생성 for ma5
        timer2 = QTimer(self)
        timer2.start(5000)
        timer2.timeout.connect(self.check_state2)

        # Table Widget
        self.tableWidget.setRowCount(4)
        for row, currency in enumerate(currency_list):
            item = QTableWidgetItem(currency)
            self.tableWidget.setItem(row, 0, item)

    def check_state(self):
        # 타이머의 시간이 되면 일정시간마다 일꾼 객체 일시키기
        self.worker.start()
        
    def check_state2(self):
        # 타이머의 시간이 되면 일정시간마다 일꾼 객체 일시키기
        self.worker2.start()
        
    def update_window(self):
        if len(self.cur_prices) == 0 or len(self.last_ma5_list) == 0:
            return
        
        for i, currency in enumerate(currency_list):
            if self.cur_prices[i] is None:
                # print('%s 현재가 조회 이상 (None)' % currency)
                self.err_count += 1
                print('Error Count : %d' % self.err_count)
                return
            else:
                price = self.cur_prices[i]
                ma5 = self.last_ma5_list[i]
                
                item = QTableWidgetItem(format(price, ',.0f'))
                self.tableWidget.setItem(i, 1, item)
                
                item = QTableWidgetItem(format(ma5, ',.0f'))
                self.tableWidget.setItem(i, 2, item)
                
                if price > ma5:
                    market_pos = '상승장'
                else:
                    market_pos = '하락장'
                    
                item = QTableWidgetItem(market_pos)
                self.tableWidget.setItem(i, 3, item)
                
                disparity = round((price/ma5) * 100, 2)
                item = QTableWidgetItem(str(disparity))
                self.tableWidget.setItem(i, 4, item)
                
                
        self.loop_count += 1
        print('loop Count : %d' % self.loop_count)
            

    @pyqtSlot(list)
    def update_price(self, prices):
        self.cur_prices = prices
        self.update_window()


    @pyqtSlot(list)
    def update_ma5(self, ma5_list):
        self.last_ma5_list = ma5_list
        self.update_window()



app = QApplication(sys.argv)
win = MyWindow()
win.show()
sys.exit(app.exec_())