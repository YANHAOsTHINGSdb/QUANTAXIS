#!/usr/bin/env python
# -*- coding: utf-8 -*-

import msvcrt
import sys
import configparser
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import TradeX

TradeX.OpenTdx()


class QA_Stock():

    def set_config(self, configs):
        try:

            self.sHost = configs['host']
            self.nPort = configs['port']
            self.sVersion = configs['version']
            self.sBranchID = configs['branchID']
            self.sAccountNo = configs['accountNo']
            self.sTradeAccountNo = configs['tradeAccountNo']
            self.sPassword = int(configs['password'])
            self.sTxPassword = int(configs['txPassword'])

            print(self.sAccountNo)
        except:
            return ('error with read setting files')

    def get_config(self):
        config = configparser.ConfigParser()
        try:
            config.read(
                str(os.path.dirname(os.path.realpath(__file__))) + '\setting.ini')
            self.sHost = config['trade-mock']['host']
            self.nPort = config['trade-mock']['port']
            self.sVersion = config['trade-mock']['version']
            self.sBranchID = config['trade-mock']['branchID']
            self.sAccountNo = config['trade-mock']['accountNo']
            self.sTradeAccountNo = config['trade-mock']['tradeAccountNo']
            self.sPassword = int(config['trade-mock']['password'])
            self.sTxPassword = int(config['trade-mock']['txPassword'])
            config_setting = {
                "host": config['trade-mock']['host'],
                "port": config['trade-mock']['port'],
                "version": config['trade-mock']['version'],
                "branchID": config['trade-mock']['branchID'],
                "accountNo": config['trade-mock']['accountNo'],
                "tradeAccountNo": config['trade-mock']['tradeAccountNo'],
                "password": int(config['trade-mock']['password']),
                "txPassword": int(config['trade-mock']['txPassword'])
            }
            return config_setting

        except:
            return ('error with read setting files')

    def QA_trade_stock_login(self):
        try:
            TradeX.OpenTdx()
            client = TradeX.Logon(str(self.sHost), int(self.nPort), str(self.sVersion), int(self.sBranchID),
                                  str(self.sAccountNo), str(
                                      self.sTradeAccountNo),
                                  str(self.sPassword), str(self.sTxPassword))
            return client
        except TradeX.error as e:
            return ("error: " + e.message)

    def QA_trade_stock_login_with_config(self, config):
        try:
            TradeX.OpenTdx()
            client = TradeX.Logon(str(config[0]), int(config[1]), str(config[2]), int(self.sBranchID),
                                  str(self.sAccountNo), str(
                                      self.sTradeAccountNo),
                                  str(self.sPassword), str(self.sTxPassword))
            return client
        except TradeX.error as e:
            return ("error: " + e.message)

        """
        nCategory
        0 ??????
        1 ??????
        2 ????????????
        3 ????????????
        4 ?????????
        5 ????????????
        6 ????????????
        7 ????????????
        8 ????????????
        9
        10
        11
        12 ?????????????????????
        13 ????????????????????????
        14 ????????????
        15 ???????????? 
        """

    def QA_trade_stock_get_cash(self, _client):
        # ??????
        self.nCategory = 0

        _errinfo, self.result = _client.QueryData(self.nCategory)
        if _errinfo != "":
            return (_errinfo)
        else:
            accounts = self.result.split('\n')[1].split('\t')
            account = {}
            account['account_id'] = accounts[0]
            account['available'] = accounts[3]
            account['freeze'] = accounts[4]
            account['on_way'] = accounts[5]
            account['withdraw'] = accounts[6]
            return account

    def QA_trade_stock_get_stock(self, client):
        # ??????
        self.nCategory = 1

        _errinfo, self.result = client.QueryData(self.nCategory)
        if _errinfo != "":
            return (_errinfo)
        else:
            stocks = self.result.split('\n')
            stock = []
            for i in range(1, len(stocks)):
                temp = {}
                temp['code'] = stocks[i].split('\t')[0]
                temp['name'] = stocks[i].split('\t')[1]
                temp['number'] = stocks[i].split('\t')[2]
                temp['hold'] = stocks[i].split('\t')[3]
                temp['sell_available'] = stocks[i].split('\t')[4]
                temp['price_now'] = stocks[i].split('\t')[5]
                temp['value_now'] = stocks[i].split('\t')[6]
                temp['price_buy'] = stocks[i].split('\t')[7]
                temp['pnl_float'] = stocks[i].split('\t')[8]
                temp['pnl_ratio'] = stocks[i].split('\t')[9]
                temp['account_type'] = stocks[i].split('\t')[10]
                temp['account_id'] = stocks[i].split('\t')[11]
                temp['shareholder'] = stocks[i].split('\t')[12]
                temp['exchange'] = stocks[i].split('\t')[13]
                temp['trade_mark'] = stocks[i].split('\t')[14]
                temp['insure_mark'] = stocks[i].split('\t')[15]
                temp['buy_today'] = stocks[i].split('\t')[16]
                temp['sell_today'] = stocks[i].split('\t')[17]
                temp['position_buy'] = stocks[i].split('\t')[18]
                temp['position_sell'] = stocks[i].split('\t')[19]
                temp['price_yesterday'] = stocks[i].split('\t')[20]
                temp['margin'] = stocks[i].split('\t')[21]
                stock.append(temp)
            return stock

    def QA_trade_stock_get_orders(self, client):
        # ????????????
        self.nCategory = 2

        _errinfo, self.result = client.QueryData(self.nCategory)
        if _errinfo != "":
            return (_errinfo)
        else:

            return self.result

    def QA_trade_stock_get_deals(self, client):
        # ????????????
        self.nCategory = 2

        _errinfo, self.result = client.QueryData(self.nCategory)
        if _errinfo != "":
            return (_errinfo)
        else:
            print(self.result)
            return self.result

    def QA_trade_stock_get_holder(self, client):
        # ????????????
        self.nCategory = 5

        _errinfo, self.result = client.QueryData(self.nCategory)
        if _errinfo != "":
            print(_errinfo)
        else:
            # print(self.result.split('\n')[1].split('\t')[0])
            # print(self.result.split('\n')[2].split('\t')[0])

            return [self.result.split('\n')[1].split('\t')[0], self.result.split('\n')[2].split('\t')[0]]

            """
            nCategory - ?????????????????????
                0 ??????
                1 ??????
                2 ????????????
                3 ????????????
                4 ????????????
                5 ????????????
                6 ????????????
            nOrderType - ??????????????????
                0 ??????????????? ??????????????????/ ??????????????????
                1 ????????????(????????????????????????)
                2 ????????????(????????????????????????)
                3 ????????????(??????????????????????????????)
                4 ????????????(????????????????????????/ ????????????????????????)
                5 ????????????(???????????????????????????)
                6 ????????????(???????????????????????????)
            sAccount - ????????????
            sStockCode - ????????????
            sPrice - ??????
            sVolume - ?????????????????????
            ????????????
            _errinfo - ???????????????????????????????????????
            result - ?????????????????????


            nCategory = 0
            nOrderType = 4
            sInvestorAccount = "p001001001005793"
            sStockCode = "601988"
            sPrice = 0
            sVolume = 100
            """

    def QA_trade_stock_post_order(self, client, order):

        if len(order) == 6:

            _errinfo, self.result = client.SendOrder(
                order[0], order[1], order[2], order[3], order[4], order[5])
            if _errinfo != "":
                print(_errinfo)
            else:
                print(self.result)

    def QA_trade_stock_post_orders(self, orderLists):

        orderLists = [{
            "nCategory": 0,
            "nOrderType": 4,
            "sInvestorAccount": "p001001001005793",
            "sStockCode": "601988",
            "sPrice": 0,
            "sVolume": 100
        }, {
            "nCategory": 0,
            "nOrderType": 4,
            "sInvestorAccount": "p001001001005793",
            "sStockCode": "601988",
            "sPrice": 0,
            "sVolume": 100
        }]
        pass

    def QA_trade_stock_delete_order(self, client, order_list):
        """
        ?????????
        nMarket - ????????????0:?????????1:??????
        Orderid - ????????????????????????
        ????????????
        _errinfo - ???????????????????????????????????????
        result - ?????????????????????

        """

        _errinfo, result = client.CancelOrder(
            int(order_list[0]), str(order_list[1]))
        if _errinfo != "":
            print(_errinfo)
        else:
            print(result)
            return (result)


    def QA_trade_stock_get_quote(self, client, stock):
        _errinfo, self.result = client.GetQuote(str(stock),)
        if _errinfo != "":
            print(_errinfo)
        else:
            #print (self.result)
            return self.result

    def QA_trade_stock_get_quotes(self, client, stock_list):
        res = client.GetQuotes(tuple(stock_list))
        for elem in res:
            _errinfo, result = elem
            if _errinfo != "":
                print(_errinfo)
            else:
                print(result)

    def QA_trade_stock_get_stockbars(self, client):
        pass


        #GetSecurityBars(nCategory, nMarket, sStockCode, nStart, nCount)
if __name__ == "__main__":
    st = QA_Stock()
    st.get_config()
    client = st.QA_trade_stock_login()
    st.QA_trade_stock_get_cash(client)
    st.QA_trade_stock_get_stock(client)
    st.QA_trade_stock_get_orders(client)
    holder = st.QA_trade_stock_get_holder(client)
    st.QA_trade_stock_get_quotes(client, ['000001', '601988'])
    #st.QA_trade_stock_delete_order(client,[0,'2 '])
    #st.QA_trade_stock_post_order(client,[0, 4, holder[0], "601988", 0, 100])
