//+------------------------------------------------------------------+
//|                    MT4 Account Monitor EA                       |
//|      Sends account metrics via HTTP WebRequest (JSON)           |
//+------------------------------------------------------------------+
#property strict
#include <stdlib.mqh>
#include <stderror.mqh>

// API URL
#define SERVER_URL "https://mt4-server.up.railway.app/api/mt4data"
#define TIMEOUT 5000
#define IC_MARKETS_BROKER "Raw Trading Ltd"
#define OP_BALANCE 6
#define OP_CREDIT 7

int OnInit()
{
   Print(" EA Initialized.");
   EventSetTimer(60);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   Print(" EA Deinitialized.");
}

//+------------------------------------------------------------------+
//| MAIN TIMER FUNCTION                                             |
//+------------------------------------------------------------------+
void OnTimer()
{
   Print(" Sending data...");
   SendAccountMetrics();
}

//+------------------------------------------------------------------+
double CalculateRealizedPL(datetime periodStart)
{
   double pl = 0.0;
   for (int i = OrdersHistoryTotal() - 1; i >= 0; i--)
   {
      if (OrderSelect(i, SELECT_BY_POS, MODE_HISTORY))
      {
         if ((OrderType() == OP_BUY || OrderType() == OP_SELL) && (OrderCloseTime() >= periodStart))
         {
            pl += OrderProfit() + OrderSwap() + OrderCommission();
         }
      }
   }
   return pl;
}

double CalculateTransactions(datetime periodStart, bool isDeposit, bool holdingFee = false)
{
   double total = 0.0;
   for (int i = OrdersHistoryTotal() - 1; i >= 0; i--)
   {
      if (OrderSelect(i, SELECT_BY_POS, MODE_HISTORY))
      {
         int type = OrderType();
         if (type == OP_BALANCE && OrderCloseTime() >= periodStart)
         {
            string comment = OrderComment();
            bool isHoldingFee = StringFind(comment, "Holding Fee") >= 0;

            if (holdingFee && isHoldingFee)
               total += OrderProfit();

            if (!holdingFee && !isHoldingFee)
            {
               if (isDeposit && OrderProfit() > 0) total += OrderProfit();
               if (!isDeposit && OrderProfit() < 0) total += OrderProfit();
            }
         }
      }
   }
   return total;
}

datetime GetStartOfWeek()
{
   int dayOfWeek = TimeDayOfWeek(TimeCurrent());
   int daysSinceMonday = (dayOfWeek == 0) ? 6 : dayOfWeek - 1;
   return TimeCurrent() - daysSinceMonday * 86400;
}

datetime GetStartOfMonth() { return StringToTime(StringFormat("%d.%02d.01 00:00", TimeYear(TimeCurrent()), TimeMonth(TimeCurrent()))); }
datetime GetStartOfYear() { return StringToTime(StringFormat("%d.01.01 00:00", TimeYear(TimeCurrent()))); }

//+------------------------------------------------------------------+
void SendAccountMetrics()
{
   string broker = AccountCompany();
   double balance = AccountBalance();
   double equity = AccountEquity();
   double marginUsed = AccountMargin();
   double freeMargin = AccountFreeMargin();
   double marginPercent = (marginUsed > 0) ? (equity / marginUsed) * 100.0 : 0.0;
   double profitLoss = equity - balance;
   int openTrades = OrdersTotal();
   int openCharts = CountOpenCharts();
   int emptyCharts = CountEmptyCharts();
   int accountNumber = AccountNumber();
   bool autotrading = TerminalInfoInteger(TERMINAL_TRADE_ALLOWED);

   datetime weekStart = GetStartOfWeek();
   datetime monthStart = GetStartOfMonth();
   datetime yearStart = GetStartOfYear();

   double realizedPLDaily = CalculateRealizedPL(TimeCurrent() - 86400);
   double realizedPLWeekly = CalculateRealizedPL(weekStart);
   double realizedPLMonthly = CalculateRealizedPL(monthStart);
   double realizedPLYearly = CalculateRealizedPL(yearStart);
   double realizedPLAllTime = CalculateRealizedPL(0);  // Ensure this is always calculated

   double depositsAllTime = CalculateTransactions(0, true);
   double withdrawalsAllTime = CalculateTransactions(0, false);

   double holdingFeeDaily = (broker == IC_MARKETS_BROKER) ? CalculateTransactions(TimeCurrent() - 86400, false, true) : 0.0;
   double holdingFeeWeekly = (broker == IC_MARKETS_BROKER) ? CalculateTransactions(weekStart, false, true) : 0.0;
   double holdingFeeMonthly = (broker == IC_MARKETS_BROKER) ? CalculateTransactions(monthStart, false, true) : 0.0;
   double holdingFeeYearly = (broker == IC_MARKETS_BROKER) ? CalculateTransactions(yearStart, false, true) : 0.0;
   double holdingFeeAllTime = (broker == IC_MARKETS_BROKER) ? CalculateTransactions(0, false, true) : 0.0;

   string json = "{";
   json += "\"broker\":\"" + broker + "\",";
   json += "\"account_number\":" + IntegerToString(accountNumber) + ",";
   json += "\"balance\":" + DoubleToString(balance, 2) + ",";
   json += "\"equity\":" + DoubleToString(equity, 2) + ",";
   json += "\"margin_used\":" + DoubleToString(marginUsed, 2) + ",";
   json += "\"free_margin\":" + DoubleToString(freeMargin, 2) + ",";
   json += "\"margin_percent\":" + DoubleToString(marginPercent, 2) + ",";
   json += "\"profit_loss\":" + DoubleToString(profitLoss, 2) + ",";
   json += "\"realized_pl_daily\":" + DoubleToString(realizedPLDaily, 2) + ",";
   json += "\"realized_pl_weekly\":" + DoubleToString(realizedPLWeekly, 2) + ",";
   json += "\"realized_pl_monthly\":" + DoubleToString(realizedPLMonthly, 2) + ",";
   json += "\"realized_pl_yearly\":" + DoubleToString(realizedPLYearly, 2) + ",";
   json += "\"realized_pl_alltime\":" + DoubleToString(realizedPLAllTime, 2) + ",";
   json += "\"deposits_alltime\":" + DoubleToString(depositsAllTime, 2) + ",";
   json += "\"withdrawals_alltime\":" + DoubleToString(withdrawalsAllTime, 2) + ",";
   json += "\"holding_fee_daily\":" + DoubleToString(holdingFeeDaily, 2) + ",";
   json += "\"holding_fee_weekly\":" + DoubleToString(holdingFeeWeekly, 2) + ",";
   json += "\"holding_fee_monthly\":" + DoubleToString(holdingFeeMonthly, 2) + ",";
   json += "\"holding_fee_yearly\":" + DoubleToString(holdingFeeYearly, 2) + ",";
   json += "\"holding_fee_alltime\":" + DoubleToString(holdingFeeAllTime, 2) + ",";
   json += "\"open_charts\":" + IntegerToString(openCharts) + ",";
   json += "\"empty_charts\":" + IntegerToString(emptyCharts) + ",";
   json += "\"open_trades\":" + IntegerToString(openTrades) + ",";
   json += "\"autotrading\":" + (autotrading ? "true" : "false");
   json += "}";

   Print(" Sending JSON: ", json);
   Print(" JSON Length: ", StringLen(json));

   uchar httpRequest[];
   StringToCharArray(json, httpRequest, 0, StringLen(json), CP_UTF8);
   Print(" HTTP Request Array Length: ", ArraySize(httpRequest));

   string headers = "Content-Type: application/json\r\n";
   uchar httpResponse[];
   string responseHeaders;

   ResetLastError();
   int result = WebRequest("POST", SERVER_URL, headers, TIMEOUT, httpRequest, httpResponse, responseHeaders);

   if (result > 0)
   {
      string response = CharArrayToString(httpResponse);
      Print(" Data sent successfully. Response: ", response);
   }
   else
   {
      Print(" WebRequest failed with error: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
int CountOpenCharts()
{
   int count = 0;
   long chartID = ChartFirst();
   while (chartID >= 0)
   {
      count++;
      chartID = ChartNext(chartID);
   }
   return count;
}

int CountEmptyCharts()
{
   int empty = 0;
   long chartID = ChartFirst();
   while (chartID >= 0)
   {
      string sym = ChartSymbol(chartID);
      if (sym == "") empty++;
      chartID = ChartNext(chartID);
   }
   return empty;
}
