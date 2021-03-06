# coding=utf-8
#
# The MIT License (MIT)
#
# Copyright (c) 2016-2017 yutiansut/QUANTAXIS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import configparser
import csv
import datetime
import json
import os
import queue
import random
import re
import sys
import time
import threading
from threading import Thread, Timer
from functools import reduce, update_wrapper, wraps, lru_cache
from statistics import mean

import apscheduler
import numpy as np
import pandas as pd
import pymongo
from QUANTAXIS import (QA_Market, QA_Portfolio, QA_QAMarket_bid, QA_Risk,
                       __version__)
from QUANTAXIS.QAARP.QAAccount import QA_Account
from QUANTAXIS.QABacktest.QAAnalysis import QA_backtest_analysis_start
from QUANTAXIS.QAData import QA_DataStruct_Stock_day, QA_DataStruct_Stock_min
from QUANTAXIS.QAFetch.QAQuery import (QA_fetch_index_day, QA_fetch_index_min,
                                       QA_fetch_stock_day, QA_fetch_stock_info,
                                       QA_fetch_stocklist_day,
                                       QA_fetch_trade_date)
from QUANTAXIS.QAFetch.QAQuery_Advance import (QA_fetch_index_day_adv,
                                               QA_fetch_index_min_adv,
                                               QA_fetch_stock_day_adv,
                                               QA_fetch_stock_min_adv,
                                               QA_fetch_stock_block_adv,
                                               QA_fetch_stocklist_day_adv,
                                               QA_fetch_stocklist_min_adv)
from QUANTAXIS.QAMarket.QABid import QA_QAMarket_bid_list
from QUANTAXIS.QASU.save_backtest import (QA_SU_save_account_message,
                                          QA_SU_save_account_to_csv,
                                          QA_SU_save_backtest_message,
                                          QA_SU_save_pnl_to_csv)
from QUANTAXIS.QATask import QA_Queue
from QUANTAXIS.QAUtil import (QA_Setting, QA_util_get_real_date,
                              QA_util_log_expection, QA_util_log_info,
                              QA_util_make_min_index, QA_util_time_gap, QA_util_date_gap,
                              QA_util_to_json_from_pandas, trade_date_sse)
from tabulate import tabulate


"""
????????? ???????????????????????????????????????

@yutiansut
2017/09/19

"""


class QA_Backtest():
    '??????????????????????????? ??????????????????????????? ????????????????????????__init__'
    backtest_type = 'day'
    account = QA_Account()
    market = QA_Market()
    bid = QA_QAMarket_bid()
    order = QA_QAMarket_bid_list()
    setting = QA_Setting()
    clients = setting.client
    user = setting.QA_setting_user_name
    market_data = []
    now = None
    today = None
    last_time = None
    strategy_stock_list = []
    trade_list = []
    start_real_id = 0
    end_real_id = 0
    temp = {}
    commission_fee_coeff = 0.0015
    strategy_start_date = ''
    strategy_start_time = ''
    strategy_end_date = ''
    strategy_end_time = ''
    benchmark_type = 'index'
    account_d_value = []
    account_d_key = []
    market_data_dict = {}
    backtest_print_log = True
    if_save_to_mongo = True
    if_save_to_csv = True

    topic_name=''
    topic_id =''


    def __init__(self):

        self.backtest_type = 'day'
        self.account = QA_Account()
        self.market = QA_Market()
        self.order = QA_QAMarket_bid_list()
        self.bid = QA_QAMarket_bid()
        self.setting = QA_Setting()
        self.clients = self.setting.client
        self.user = self.setting.QA_setting_user_name
        self.market_data = []
        self.now = None
        self.last_time=None
        self.strategy_start_date = ''
        self.strategy_start_time = ''
        self.strategy_end_date = ''
        self.strategy_end_time = ''
        self.today = None
        self.strategy_stock_list = []
        self.trade_list = []
        self.start_real_id = 0
        self.end_real_id = 0
        self.temp = {}
        self.commission_fee_coeff = 0.0015
        self.account_d_value = []
        self.account_d_key = []
        self.benchmark_type = 'index'
        self.market_data_dict = {}
        self.backtest_print_log = True  # ??????
        self.if_save_to_mongo = True
        self.if_save_to_csv = True

        self.topic_name=''
        self.topic_id =''

    def __QA_backtest_init(self):
        self.__init__(self)
        """?????????????????????????????????,???????????????????????????????????????????????????,????????????????????????????????????"""
        # ?????????????????????????????????
        self.strategy_start_date = str('2017-01-05')
        self.strategy_end_date = str('2017-07-01')
        # ??????????????????,?????????list??????,??????????????????????????????
        # gap????????????,?????????????????????????????????(?????????)
        self.strategy_gap = int(60)
        # ??????????????????????????????,???????????????,??????,????????????
        self.setting.QA_util_sql_mongo_ip = str('127.0.0.1')
        self.setting.QA_setting_user_name = str('admin')
        self.setting.QA_setting_user_password = str('admin')
        self.setting.QA_setting_init()
        # ???????????????
        self.strategy_name = str('example_min')
       # ?????????????????????,???????????????????????????,????????????????????????????????????id
        self.trade_list = trade_date_sse
        self.benchmark_code = '000300'
        """
        ????????????????????????????????????,???????????????????????????,??????????????????????????????,1???????????????,-1???????????????
        """

        self.strategy_stock_list = ['000001', '000002', '000004']
        self.account.init_assest = 1000000
        self.backtest_bid_model = 'market_price'
        self.commission_fee_coeff = 0.0015

    def __QA_backtest_prepare(self):
        """
        ????????????????????? ?????????,?????????????????????????????????????????????
        ?????????????????????
        @yutiansut
        2017/7/20
        """

        self.strategy_stock_list = np.unique(
            self.strategy_stock_list).tolist()  # ??????????????????
        if len(str(self.strategy_start_date)) == 10:
            self.strategy_start_time = str(
                self.strategy_start_date) + ' 15:00:00'
        elif len(str(self.strategy_start_date)) == 19:
            self.strategy_start_time = str(self.strategy_start_date)
            self.strategy_start_date = str(self.strategy_start_date)[0:10]
        else:
            self.__QA_backtest_log_info(self, 'Wrong start date format')

        if len(str(self.strategy_end_date)) == 10:
            self.strategy_end_time = str(self.strategy_end_date) + ' 15:00:00'
        elif len(str(self.strategy_end_date)) == 19:
            self.strategy_end_time = str(self.strategy_end_date)
            self.strategy_end_date = str(self.strategy_end_date)[0:10]
        else:
            self.__QA_backtest_log_info(self, 'Wrong end date format')
        # ????????????????????????
        self.market = QA_Market(self.commission_fee_coeff)
        self.setting.QA_setting_init()
        self.account.init()
        self.account_d_value.append(self.account.init_assest)
        self.start_real_date = QA_util_get_real_date(
            self.strategy_start_date, self.trade_list, 1)
        self.start_real_time = str(
            self.start_real_date) + ' ' + self.strategy_start_time.split(' ')[1]
        self.start_real_id = self.trade_list.index(self.start_real_date)
        self.end_real_date = QA_util_get_real_date(
            self.strategy_end_date, self.trade_list, -1)
        self.end_real_id = self.trade_list.index(self.end_real_date)
        self.end_real_time = str(self.end_real_date) + \
            ' ' + self.strategy_end_time.split(' ')[1]
        # ????????????????????????cookie
        self.account.account_cookie = str(random.random())
        # ?????????????????????????????????
        if self.benchmark_type in ['I', 'index']:
            self.benchmark_data = QA_fetch_index_day_adv(
                self.benchmark_code, self.trade_list[self.start_real_id - 1], self.end_real_date)
        elif self.benchmark_type in ['S', 'stock']:
            self.benchmark_data = QA_fetch_stock_day_adv(
                self.benchmark_code, self.trade_list[self.start_real_id - 1], self.end_real_date)
        if self.backtest_type in ['day', 'd', '0x00']:
            self.market_data = QA_fetch_stocklist_day_adv(
                self.strategy_stock_list, self.trade_list[self.start_real_id - int(
                    self.strategy_gap + 1)], self.trade_list[self.end_real_id]).to_qfq()

        elif self.backtest_type in ['1min', '5min', '15min', '30min', '60min']:
            self.market_data = QA_fetch_stocklist_min_adv(
                self.strategy_stock_list, QA_util_time_gap(
                    self.start_real_time, self.strategy_gap + 1, '<', self.backtest_type),
                QA_util_time_gap(self.end_real_time, 1, '>', self.backtest_type), self.backtest_type).to_qfq()

        elif self.backtest_type in ['index_day']:
            self.market_data = QA_fetch_index_day_adv(self.strategy_stock_list, self.trade_list[self.start_real_id - int(
                self.strategy_gap + 1)], self.end_real_date)

        elif self.backtest_type in ['index_1min', 'index_5min', 'index_15min', 'index_30min', 'index_60min']:
            self.market_data = QA_fetch_index_min_adv(
                self.strategy_stock_list, QA_util_time_gap(self.start_real_time, self.strategy_gap + 1, '<', self.backtest_type.split('_')[1]),  QA_util_time_gap(self.end_real_time, 1, '>', self.backtest_type.split('_')[1]), self.backtest_type.split('_')[1])
        self.market_data_dict = dict(
            zip(list(self.market_data.code), self.market_data.splits()))
        self.market_data_hashable = self.market_data.dicts

    def __QA_backtest_log_info(self, log):
        if self.backtest_print_log:
            return QA_util_log_info(log)
        else:
            pass

    def __QA_backtest_before_backtest(self, *args, **kwargs):
        """
        ????????????????????????????????????
        """
        self.__QA_backtest_log_info(
            self, 'QUANTAXIS Backtest Engine Initial Successfully')
        self.__QA_backtest_log_info(self, 'Basical Info: \n' + tabulate(
            [[str(__version__), str(self.strategy_name)]], headers=('Version', 'Strategy_name')))
        self.__QA_backtest_log_info(self, 'BACKTEST Cookie_ID is:  ' +
                                    str(self.account.account_cookie))
        self.__QA_backtest_log_info(self, 'Stock_List: \n' +
                                    tabulate([self.strategy_stock_list]))

        # ?????????????????????
        self.__messages = []

    def __QA_bid_amount(self, __strategy_amount, __amount):
        if __strategy_amount == 'mean':
            return float(float(self.account.message['body']['account']['cash'][-1]) /
                         len(self.strategy_stock_list)), 'price'
        elif __strategy_amount == 'half':
            return __amount * 0.5, 'amount'
        elif __strategy_amount == 'all':
            return __amount, 'amount'

    def __end_of_trading(self, *arg, **kwargs):
        # ????????????????????????,??????????????????(????????????????????????????????????)
        # ?????????????????????????????????
        if self.backtest_type in ['day']:
            self.now = str(self.end_real_date)
            self.today = str(self.end_real_date)
        elif self.backtest_type in ['1min', '5min', '15min', '30min', '60min']:
            self.now = str(self.end_real_date) + ' 15:00:00'
            self.today = str(self.end_real_date)
        elif self.backtest_type in ['index_day']:
            self.now = str(self.end_real_date)
            self.today = str(self.end_real_date)
        elif self.backtest_type in ['index_1min', 'index_5min', 'index_15min', 'index_30min', 'index_60min']:
            self.now = str(self.end_real_date) + ' 15:00:00'
            self.today = str(self.end_real_date)

        self.today = self.end_real_date
        self.QA_backtest_sell_all(self)
        self.__sell_from_order_queue(self)
        self.__sync_order_LM(self, 'daily_settle')  # ????????????

    def __sell_from_order_queue(self):

        # ??????bar???????????????,????????????
        __result = []
        self.order.__init__()
        if len(self.account.order_queue) >= 1:
            __bid_list = self.order.from_dataframe(self.account.order_queue.query(
                'status!=200').query('status!=500').query('status!=400'))

            for item in __bid_list:
                # ???????????????????????????????????????
                item.date = self.today
                item.datetime = self.now

                __bid, __market = self.__wrap_bid(self, item)
                __message = self.__QA_backtest_send_bid(
                    self, __bid, __market)
                if isinstance(__message, dict):
                    if __message['header']['status'] in ['200', 200]:
                        self.__sync_order_LM(
                            self, 'trade', __bid, __message['header']['order_id'], __message['header']['trade_id'], __message)
                    else:
                        self.__sync_order_LM(self, 'wait')
        else:
            self.__QA_backtest_log_info(self,
                                        'FROM BACKTEST: Order Queue is empty at %s!' % self.now)
            pass

    def __sync_order_LM(self, event_, order_=None, order_id_=None, trade_id_=None, market_message_=None):
        """
        ????????????: ?????????????????? Order-Lifecycle-Management
        status1xx ???????????????
        status3xx ???????????????  ??????????????????(????????????/????????????)
        status3xx ????????????(????????????)
        status2xx ??????????????????/???????????????
        status4xx ????????????
        status500 ????????????(????????????) ??????????????????    
        =======
        1. ????????????
        2. ????????????
        """
        if event_ is 'init_':

            self.account.cash_available = self.account.cash[-1]
            self.account.sell_available = pd.DataFrame(self.account.hold[1::], columns=self.account.hold[0]).set_index(
                'code', drop=False)['amount'].groupby('code').sum()

        elif event_ is 'create_order':

            if order_ is not None:
                if order_.towards is 1:
                    # ??????
                    if self.account.cash_available - order_.amount * order_.price > 0:
                        self.account.cash_available -= order_.amount * order_.price
                        order_.status = 300  # ??????????????????

                        self.account.order_queue = self.account.order_queue.append(
                            order_.to_df())
                    else:
                        self.__QA_backtest_log_info(self, 'FROM ENGINE: NOT ENOUGH MONEY:CASH  %s Order %s' % (
                            self.account.cash_available, order_.amount * order_.price))
                elif order_.towards is -1:

                    if self.QA_backtest_sell_available(self, order_.code) - order_.amount >= 0:
                        self.account.sell_available[order_.code] -= order_.amount
                        self.account.order_queue = self.account.order_queue.append(
                            order_.to_df())

            else:
                self.__QA_backtest_log_info(self, 'Order Event Warning:%s in %s' %
                                            (event_, str(self.now)))

        elif event_ in ['wait', 'live']:
            # ???????????? ??????????????????????????????
            pass
        elif event_ in ['cancel_order']:  # ????????????:????????????
            # try:
            assert isinstance(order_id_, str)
            self.account.order_queue.loc[self.account.order_queue['order_id']
                                         == order_id_, 'status'] = 400  # ????????????
            if order_.towards is 1:
                # ?????? ??????  ????????????
                self.account.cash_available += self.account.order_queue.query('order_id=="order_id_"')[
                    'amount'] * self.account.order_queue.query('order_id=="order_id_"')['price']

            elif order_.towards is -1:
                # ???????????? ??????????????????
                self.account.sell_available[order_.code] += self.account.order_queue.query(
                    'order_id=="order_id_"')['price']
        elif event_ in ['daily_settle']:  # ????????????/??????/??????????????????/??????????????????500 ????????????

            # ??????
            """
            ??????????????????
            - ??????????????????????????????
            - ???????????????/??????????????????
            """

            self.account.cash_available = self.account.cash[-1]
            self.account.sell_available = self.QA_backtest_hold(
                self)['amount'].groupby('code').sum()

            self.account.order_queue = pd.DataFrame()

            self.account_d_key.append(self.today)

            if len(self.account.hold) > 1:

                self.account_d_value.append(self.account.cash[-1] + sum([self.QA_backtest_get_market_data_bar(
                    self, self.account.hold[i][1], self.now, if_trade=False).close[0] * float(self.account.hold[i][3])
                    for i in range(1, len(self.account.hold))]))
            else:
                self.account_d_value.append(self.account.cash[-1])
        elif event_ in ['t_0']:
            """
            T+0????????????

            ??????t+0??????????????? /????????????
            """
            self.account.cash_available = self.account.cash[-1]
            self.account.sell_available = self.QA_backtest_hold(
                self)['amount'].groupby('code').sum()

        elif event_ in ['trade']:
            # try:
            assert isinstance(order_, QA_QAMarket_bid)
            assert isinstance(order_id_, str)
            assert isinstance(trade_id_, str)
            assert isinstance(market_message_, dict)
            if order_.towards is 1:
                # ??????
                # ????????????
                order_.trade_id = trade_id_
                order_.transact_time = self.now
                order_.amount -= market_message_['body']['bid']['amount']

                if order_.amount == 0:  # ????????????
                    # ??????(????????????)['???????????????????????????']
                    self.account.order_queue.loc[self.account.order_queue['order_id']
                                                 == order_id_, 'status'] = 200

                elif order_.amount > 0:
                    # ??????(????????????)
                    self.account.order_queue.loc[self.account.order_queue['order_id']
                                                 == order_id_, 'status'] = 203
                    self.account.order_queue.query('order_id=="order_id_"')[
                        'amount'] -= market_message_['body']['bid']['amount']
            elif order_.towards is -1:
                # self.account.sell_available[order_.code] -= market_message_[
                #    'body']['bid']['amount']
                # ????????????????????? ??????????????????/ ??????????????????(??????????????????)
                self.account.cash_available += market_message_['body']['bid']['amount'] * market_message_[
                    'body']['bid']['price'] - market_message_['body']['fee']['commission']
                order_.trade_id = trade_id_
                order_.transact_time = self.now
                order_.amount -= market_message_['body']['bid']['amount']
                if order_.amount == 0:
                    # ??????(????????????)
                    self.account.order_queue.loc[self.account.order_queue['order_id']
                                                 == order_id_, 'status'] = 200
                else:
                    # ??????(????????????)
                    self.account.order_queue.loc[self.account.order_queue['order_id']
                                                 == order_id_, 'status'] = 203
                    self.account.order_queue[self.account.order_queue['order_id'] ==
                                             order_id_]['amount'] -= market_message_['body']['bid']['amount']
        else:
            self.__QA_backtest_log_info(self,
                                        'EventEngine Warning: Unknown type of order event in  %s' % str(self.now))

    def __QA_backtest_send_bid(self, __bid, __market=None):
        __message = self.market.receive_bid(__bid, __market)
        if __bid.towards == 1:
            # ??????
            # ????????????????????????bar???open??????
            # ??????????????????,??????????????????????????????????????????
            if __message['header']['status'] == 200 and __message['body']['bid']['amount'] > 0:
                # ????????????????????? ???????????????????????????,????????????????????????0???????????????
                # ???????????????>0, ????????????????????????
                self.__QA_backtest_log_info(self, 'BUY %s Price %s Date %s Amount %s' % (
                    __bid.code, __bid.price, __bid.datetime, __bid.amount))
                self.__messages = self.account.QA_account_receive_deal(
                    __message)
                return __message
            else:

                return __message
        # ?????????????????????,????????????????????????????????????????????????????????????:`````````````                                `
        # ?????????????????????????????????????????????,???????????????????????????????????????????????????????????????????????????

        elif __bid.towards == -1:
            # ????????????????????? ?????????????????????
            # ?????????????????????????????????
            # ??????????????????
            if __message['header']['status'] == 200:
                self.__messages = self.account.QA_account_receive_deal(
                    __message)
                self.__QA_backtest_log_info(self, 'SELL %s Price %s Date %s  Amount %s' % (
                    __bid.code, __bid.price, __bid.datetime, __bid.amount))
                return __message
            else:
                # self.account.order_queue=self.account.order_queue.append(__bid.to_df())
                return __message

        else:
            return "Error: No buy/sell towards"

    def __wrap_bid(self, __bid, __order=None):
        __market_data_for_backtest = self.QA_backtest_find_bar(
            self, __bid.code, __bid.datetime)
        if __market_data_for_backtest is not None:

            if __market_data_for_backtest['open'] is not None and __order is not None:
                if __order['bid_model'] in ['limit', 'Limit', 'Limited', 'limited', 'l', 'L', 0, '0']:
                        # ??????????????????
                    __bid.price = __order['price']
                elif __order['bid_model'] in ['Market', 'market', 'MARKET', 'm', 'M', 1, '1']:
                    # 2017-09-18 ??????  ??????????????????bar???????????????
                    __bid.price = float(__market_data_for_backtest['open'])
                elif __order['bid_model'] in ['strict', 'Strict', 's', 'S', '2', 2]:
                    __bid.price = float(
                        __market_data_for_backtest['high']) if __bid.towards == 1 else float(__market_data_for_backtest['low'])
                elif __order['bid_model'] in ['close', 'close_price', 'c', 'C', '3', 3]:
                    __bid.price = float(__market_data_for_backtest['close'])

                __bid.price = float('%.2f' % __bid.price)
                return __bid, __market_data_for_backtest
            else:
                return __bid, __market_data_for_backtest

        else:
            self.__QA_backtest_log_info(self, 'BACKTEST ENGINE ERROR=== CODE %s TIME %s NO MARKET DATA!' % (
                __bid.code, __bid.datetime))
            return __bid, 500

    def __end_of_backtest(self, *arg, **kwargs):
        # ????????????
        # ??????account.detail??????????????????
        self.account.detail = detail = pd.DataFrame(self.account.detail, columns=['date', 'code', 'price', 'amounts', 'order_id',
                                                                                  'trade_id', 'sell_price', 'sell_order_id',
                                                                                  'sell_trade_id', 'sell_date', 'left_amount',
                                                                                  'commission'])

        def __mean(list_):
            if len(list_) > 0:
                return mean(list_)
            else:
                return 'No Data'

        self.account.detail['sell_average'] = self.account.detail['sell_price'].apply(
            lambda x: __mean(x))

        try:
            self.account.detail['pnl_persentage'] = self.account.detail['sell_average'] - \
                self.account.detail['price']

            self.account.detail['pnl'] = self.account.detail['pnl_persentage'] * (self.account.detail['amounts'] - self.account.detail['left_amount'])- self.account.detail['commission']
        except:
            pass
        self.account.detail = self.account.detail.drop(
            ['order_id', 'trade_id', 'sell_order_id', 'sell_trade_id'], axis=1)
        self.__QA_backtest_log_info(self, 'start analysis====\n' +
                                    str(self.strategy_stock_list))
        self.__QA_backtest_log_info(
            self, '=' * 10 + 'Trade History' + '=' * 10)
        self.__QA_backtest_log_info(self, '\n' + tabulate(self.account.history,
                                                          headers=('date', 'code', 'price', 'towards',
                                                                   'amounts', 'order_id', 'trade_id', 'commission')))
        self.__QA_backtest_log_info(self, '\n' + tabulate(self.account.detail,
                                                          headers=(self.account.detail.columns)))
        __exist_time = int(self.end_real_id) - int(self.start_real_id) + 1
        if len(self.__messages) > 1:
            performace = QA_backtest_analysis_start(
                self.setting.client, self.strategy_stock_list, self.account_d_value, self.account_d_key, self.__messages,
                self.trade_list[self.start_real_id:self.end_real_id + 1],
                self.benchmark_data.data)
            _backtest_mes = {
                'user': self.setting.QA_setting_user_name,
                'strategy': self.strategy_name,
                'stock_list': performace['code'],
                'start_time': self.strategy_start_date,
                'end_time': self.strategy_end_date,
                'account_cookie': self.account.account_cookie,
                'annualized_returns': performace['annualized_returns'],
                'benchmark_annualized_returns': performace['benchmark_annualized_returns'],
                'assets': performace['assets'],
                'benchmark_assets': performace['benchmark_assets'],
                'trade_date': performace['trade_date'],
                'total_date': performace['total_date'],
                'win_rate': performace['win_rate'],
                'alpha': performace['alpha'],
                'beta': performace['beta'],
                'sharpe': performace['sharpe'],
                'vol': performace['vol'],
                'benchmark_vol': performace['benchmark_vol'],
                'max_drop': performace['max_drop'],
                'exist': __exist_time,
                'time': datetime.datetime.now()
            }

            if self.if_save_to_mongo:
                QA_SU_save_backtest_message(_backtest_mes, self.setting.client)
                QA_SU_save_account_message(
                    self.__messages, self.setting.client)
            if self.if_save_to_csv:
                QA_SU_save_account_to_csv(self.__messages)

                self.account.detail.to_csv(
                    'backtest-pnl--' + str(self.account.account_cookie) + '.csv')

    def __check_state(self, bid_price, bid_amount):
        pass

    def QA_Backtest_before_init(self):
        return self.__QA_backtest_init()

    def QA_Backtest_after_init(self):
        return self.__QA_backtest_prepare()

    @lru_cache()
    def QA_backtest_find_bar(self, code, time):
        if isinstance(time, str):
            if len(time) == 10:
                try:
                    return self.market_data_hashable[(datetime.datetime.strptime(time, '%Y-%m-%d'), code)]
                except:
                    return None
            elif len(time) == 19:
                try:
                    return self.market_data_hashable[(datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S'), code)]
                except:
                    return None
        else:
            try:
                return self.market_data_hashable[(time, code)]
            except:
                return None

    @lru_cache()
    def QA_backtest_get_market_data(self, code, date, gap_=None, type_='lt'):
        '?????????????????????????????????????????? ???GAP?????????'
        gap_ = self.strategy_gap if gap_ is None else gap_
        try:
            return self.market_data_dict[code].select_time_with_gap(date, gap_, type_)
        except:
            return None

    @lru_cache()
    def QA_backtest_get_market_data_panel(self, date=None, type_='lt'):
        try:
            if date is not None:
                if type_ in ['lt']:
                    return self.market_data.select_time_with_gap(date, 1, type_)
            else:
                return self.market_data.select_time_with_gap(self.now, 1, type_)
        except Exception as e:
            raise e

    @lru_cache()
    def QA_backtest_get_market_data_bar(self, code, time, if_trade=True):
        '??????????????????????????????????????????'
        try:
            return self.market_data_dict[code].get_bar(code, time, if_trade)
        except:
            return None

    def QA_backtest_get_block(self, block_list):
        block_ = QA_fetch_stock_block_adv()
        _data = []

        try:
            for item in block_list:

                _data.extend(block_.get_block(item).code)
            return np.unique(_data).tolist()
        except Exception as e:
            raise e

    #@lru_cache()
    def QA_backtest_sell_available(self, __code):
        try:
            return self.account.sell_available[__code]
        except:
            return 0
   # @lru_cache()

    def QA_backtest_hold(self):
        return pd.DataFrame(self.account.hold[1::], columns=self.account.hold[0]).set_index('code', drop=False)

    def QA_backtest_hold_amount(self, __code):
        try:
            return pd.DataFrame(self.account.hold[1::], columns=self.account.hold[0]).set_index(
                'code', drop=False)['amount'].groupby('code').sum()[__code]
        except:
            return 0

    def QA_backtest_hold_price(self, __code):
        try:
            return self.QA_backtest_hold(self)['price'].groupby('code').mean()[__code]
        except:
            return None

    @lru_cache()
    def QA_backtest_get_OHLCV(self, __data):
        '???????????? OHLCV??????'
        return (__data.open, __data.high, __data.low, __data.close, __data.vol)

    def QA_backtest_send_order(self, __code, __amount, __towards, __order):
        """
        2017/8/4
        ????????????
        ????????????????????????????????????,????????????????????????????????????

        ??????
        =============
        ??????/??????
        ????????????
        ??????/????????????
        ????????????*
            0 ???????????? LIMIT ORDER
            1 ???????????? MARKET ORDER
            2 ????????????(?????????????????? ??????????????????) STRICT ORDER


        ??????
        =============
        1. ????????????bid???(????????????)
        2. ????????????/????????????
        3. ????????????(wrap)
        4. ?????????_send_bid??????
        """

        # ?????????100????????????
        # ??????bid

        __bid = QA_QAMarket_bid()  # init
        (__bid.order_id, __bid.user, __bid.strategy,
         __bid.code, __bid.date, __bid.datetime,
         __bid.sending_time,
         __bid.amount, __bid.towards) = (str(random.random()),
                                         self.setting.QA_setting_user_name, self.strategy_name,
                                         __code, self.running_date, str(
                                             self.now),
                                         self.running_date, __amount, __towards)

        # 2017-09-21 ??????: ????????????????????????????????????amount?????????????????????
        if self.backtest_type in ['day']:
            __bid.type = '0x01'
            __bid.amount = int(__bid.amount / 100) * 100
        elif self.backtest_type in ['1min', '5min', '15min', '30min', '60min']:
            __bid.type = '0x02'
            __bid.amount = int(__bid.amount / 100) * 100
        elif self.backtest_type in ['index_day']:
            __bid.type = '0x03'
            __bid.amount = int(__bid.amount)
        elif self.backtest_type in ['index_1min', 'index_5min', 'index_15min', 'index_30min', 'index_60min']:
            __bid.type = '0x04'
            __bid.amount = int(__bid.amount)
        # ????????????/????????????

        __bid, __market = self.__wrap_bid(self, __bid, __order)
        if __bid is not None and __market != 500:
            print('GET the Order Code %s Amount %s Price %s Towards %s Time %s' % (
                __bid.code, __bid.amount, __bid.price, __bid.towards, __bid.datetime))
            self.__sync_order_LM(self, 'create_order', order_=__bid)

    @lru_cache()
    def QA_backtest_check_order(self, order_id_):
        '??????????????????????????????'
        """
        ?????????????????????????????????????????????,??????????????????????????????????????????:
        ???????????? 2xx ?????????  4xx????????? 5xx?????????????????????(??????)

        ?????????????????????????????????,?????????????????????????????????:


        200 ????????????,????????????
        203 ????????????,???????????????
        300 ????????????????????????
        400 ?????????
        500 ???????????????/????????????
        """
        return self.account.order_queue[self.account.order_queue['order_id'] == order_id_]['status']

    @lru_cache()
    def QA_backtest_status(self):
        return vars(self)

    @lru_cache()
    def QA_backtest_sell_all(self):
        __hold_list = pd.DataFrame(self.account.hold[1::], columns=self.account.hold[0]).set_index(
            'code', drop=False)['amount'].groupby('code').sum()

        for item in self.strategy_stock_list:
            try:
                if __hold_list[item] > 0:
                    self.QA_backtest_send_order(
                        self, item, __hold_list[item], -1, {'bid_model': 'C'})

            except:
                pass

    @classmethod
    def load_strategy(_cls, func, *arg, **kwargs):
        '??????????????????'

        # ??????????????????????????????????????????`
        __messages = {}
        _cls.__init_cash_per_stock = int(
            float(_cls.account.init_assest) / len(_cls.strategy_stock_list))
        # ????????????????????????
        for i in range(int(_cls.start_real_id), int(_cls.end_real_id)):
            _cls.running_date = _cls.trade_list[i]
            _cls.__QA_backtest_log_info(
                _cls, '=================daily hold list====================')
            _cls.__QA_backtest_log_info(_cls, 'in the begining of ' +
                                        _cls.running_date)
            _cls.__QA_backtest_log_info(_cls,
                                        tabulate(_cls.account.message['body']['account']['hold']))

            if _cls.now is not None:
                _cls.last_time = _cls.now

            _cls.now = _cls.running_date
            _cls.today = _cls.running_date

            # ???????????????????????????
            _cls.__sync_order_LM(_cls, 'init_')  # ???????????????

            if _cls.backtest_type in ['day', 'd', 'index_day']:

                func(*arg, **kwargs)  # ????????????
                _cls.__sell_from_order_queue(_cls)
            elif _cls.backtest_type in ['1min', '5min', '15min', '30min', '60min', 'index_1min', 'index_5min', 'index_15min', 'index_30min', 'index_60min']:
                if _cls.backtest_type in ['1min', 'index_1min']:
                    type_ = '1min'
                elif _cls.backtest_type in ['5min', 'index_5min']:
                    type_ = '5min'
                elif _cls.backtest_type in ['15min', 'index_15min']:
                    type_ = '15min'
                elif _cls.backtest_type in ['30min', 'index_30min']:
                    type_ = '30min'
                elif _cls.backtest_type in ['60min', 'index_60min']:
                    type_ = '60min'
                daily_min = QA_util_make_min_index(
                    _cls.today, type_)  # ???????????????index
                for min_index in daily_min:
                    _cls.now = min_index

                    _cls.__QA_backtest_log_info(_cls,
                                                '=================Min hold list====================')
                    _cls.__QA_backtest_log_info(
                        _cls, 'in the begining of %s' % str(min_index))
                    _cls.__QA_backtest_log_info(_cls,
                                                tabulate(_cls.account.message['body']['account']['hold']))
                    func(*arg, **kwargs)  # ????????????

                    _cls.__sell_from_order_queue(_cls)
                    if _cls.backtest_type in ['index_1min', 'index_5min', 'index_15min']:
                        _cls.__sync_order_LM(_cls, 't_0')
            _cls.__sync_order_LM(_cls, 'daily_settle')  # ????????????

        # ????????????
        _cls.__end_of_trading(_cls)

    @classmethod
    def backtest_init(_cls, func, *arg, **kwargs):
        def __init_backtest(_cls, *arg, **kwargs):
            _cls.__QA_backtest_init(_cls)
            func(*arg, **kwargs)
            _cls.__QA_backtest_prepare(_cls)
        return __init_backtest(_cls)

    @classmethod
    def before_backtest(_cls, func, *arg, **kwargs):
        def __before_backtest(_cls, *arg, **kwargs):
            func(*arg, **kwargs)
            _cls.__QA_backtest_before_backtest(_cls)
        return __before_backtest(_cls)

    @classmethod
    def end_backtest(_cls, func, *arg, **kwargs):
        _cls.__end_of_backtest(_cls, func, *arg, **kwargs)
        return func(*arg, **kwargs)

    # ???????????????????????????
    @classmethod
    def trade_event(_cls, func, *arg, **kwargs):
        return func(*arg, **kwargs)


if __name__ == '__main__':

    pass
