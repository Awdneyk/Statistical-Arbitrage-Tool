using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;
using cAlgo.Indicators;

namespace cAlgo.Robots
{
    public class RollingWindow
    {
        private readonly Queue<double> _values;
        private readonly int _windowSize;
        private double _sum;

        public RollingWindow(int windowSize)
        {
            _windowSize = windowSize;
            _values = new Queue<double>();
            _sum = 0;
        }

        public void Add(double value)
        {
            _values.Enqueue(value);
            _sum += value;

            if (_values.Count > _windowSize)
            {
                _sum -= _values.Dequeue();
            }
        }

        public double Mean => _values.Count > 0 ? _sum / _values.Count : 0;

        public double StandardDeviation
        {
            get
            {
                if (_values.Count < 2) return 0;

                var mean = Mean;
                var sumSquaredDifferences = _values.Sum(x => Math.Pow(x - mean, 2));
                return Math.Sqrt(sumSquaredDifferences / (_values.Count - 1));
            }
        }

        public int Count => _values.Count;

        public bool IsFull => _values.Count >= _windowSize;
    }

    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class StatisticalArbitrageBot : Robot
    {
        [Parameter("Symbol A", DefaultValue = "EURUSD")]
        public string SymbolA { get; set; }

        [Parameter("Symbol B", DefaultValue = "USDCHF")]
        public string SymbolB { get; set; }

        [Parameter("Hedge Ratio", DefaultValue = 0.85)]
        public double HedgeRatio { get; set; }

        [Parameter("Rolling Window Size", DefaultValue = 50)]
        public int WindowSize { get; set; }

        [Parameter("Entry Threshold", DefaultValue = 2.0)]
        public double EntryThreshold { get; set; }

        [Parameter("Exit Threshold", DefaultValue = 0.5)]
        public double ExitThreshold { get; set; }

        [Parameter("Max Spread (pips)", DefaultValue = 2.0)]
        public double MaxSpreadPips { get; set; }

        [Parameter("Volume", DefaultValue = 10000)]
        public int Volume { get; set; }

        [Parameter("Label", DefaultValue = "StatArb")]
        public string Label { get; set; }

        private Symbol _symbolAData;
        private Symbol _symbolBData;
        private RollingWindow _spreadWindow;
        private bool _hasPosition;
        private TradeType _currentTradeType;
        private DateTime _lastLogTime;

        protected override void OnStart()
        {
            _symbolAData = Symbols.GetSymbol(SymbolA);
            _symbolBData = Symbols.GetSymbol(SymbolB);
            _spreadWindow = new RollingWindow(WindowSize);
            _hasPosition = false;
            _lastLogTime = DateTime.MinValue;

            Print($"Statistical Arbitrage Bot Started");
            Print($"Symbol A: {SymbolA}, Symbol B: {SymbolB}");
            Print($"Hedge Ratio: {HedgeRatio}, Window Size: {WindowSize}");
            Print($"Entry Threshold: {EntryThreshold}, Exit Threshold: {ExitThreshold}");
        }

        protected override void OnTick()
        {
            if (_symbolAData == null || _symbolBData == null)
                return;

            var midPriceA = (_symbolAData.Bid + _symbolAData.Ask) / 2;
            var midPriceB = (_symbolBData.Bid + _symbolBData.Ask) / 2;
            var spread = midPriceA - HedgeRatio * midPriceB;

            _spreadWindow.Add(spread);

            if (!_spreadWindow.IsFull)
                return;

            var mean = _spreadWindow.Mean;
            var stdDev = _spreadWindow.StandardDeviation;

            if (stdDev == 0)
                return;

            var zScore = (spread - mean) / stdDev;

            LogSignalData(spread, mean, stdDev, zScore);

            if (_hasPosition)
            {
                CheckExitConditions(zScore);
            }
            else
            {
                CheckEntryConditions(zScore);
            }
        }

        private void CheckEntryConditions(double zScore)
        {
            if (Math.Abs(zScore) < EntryThreshold)
                return;

            if (!IsSpreadAcceptable())
                return;

            if (zScore > EntryThreshold)
            {
                ExecutePairTrade(TradeType.Sell, TradeType.Buy);
                _currentTradeType = TradeType.Sell;
                Print($"ENTRY: Short {SymbolA}, Long {SymbolB} | Z-Score: {zScore:F4}");
            }
            else if (zScore < -EntryThreshold)
            {
                ExecutePairTrade(TradeType.Buy, TradeType.Sell);
                _currentTradeType = TradeType.Buy;
                Print($"ENTRY: Long {SymbolA}, Short {SymbolB} | Z-Score: {zScore:F4}");
            }
        }

        private void CheckExitConditions(double zScore)
        {
            if (Math.Abs(zScore) > ExitThreshold)
                return;

            CloseAllPositions();
            Print($"EXIT: All positions closed | Z-Score: {zScore:F4}");
        }

        private void ExecutePairTrade(TradeType tradeTypeA, TradeType tradeTypeB)
        {
            var volumeA = Volume;
            var volumeB = (int)(Volume * HedgeRatio);

            var resultA = ExecuteMarketOrder(tradeTypeA, _symbolAData.Name, volumeA, Label + "_A");
            var resultB = ExecuteMarketOrder(tradeTypeB, _symbolBData.Name, volumeB, Label + "_B");

            if (resultA.IsSuccessful && resultB.IsSuccessful)
            {
                _hasPosition = true;
                Print($"Pair trade executed successfully");
            }
            else
            {
                Print($"Trade execution failed - A: {resultA.Error}, B: {resultB.Error}");
                if (resultA.IsSuccessful)
                    resultA.Position.Close();
                if (resultB.IsSuccessful)
                    resultB.Position.Close();
            }
        }

        private void CloseAllPositions()
        {
            var positions = Positions.FindAll(Label + "_A").Concat(Positions.FindAll(Label + "_B"));
            
            foreach (var position in positions)
            {
                position.Close();
            }

            _hasPosition = false;
        }

        private bool IsSpreadAcceptable()
        {
            var spreadA = (_symbolAData.Ask - _symbolAData.Bid) / _symbolAData.PipSize;
            var spreadB = (_symbolBData.Ask - _symbolBData.Bid) / _symbolBData.PipSize;

            return spreadA <= MaxSpreadPips && spreadB <= MaxSpreadPips;
        }

        private void LogSignalData(double spread, double mean, double stdDev, double zScore)
        {
            if (DateTime.Now.Subtract(_lastLogTime).TotalSeconds >= 5)
            {
                Print($"Spread: {spread:F6} | Mean: {mean:F6} | StdDev: {stdDev:F6} | Z-Score: {zScore:F4} | HasPos: {_hasPosition}");
                _lastLogTime = DateTime.Now;
            }
        }

        protected override void OnStop()
        {
            CloseAllPositions();
            Print("Statistical Arbitrage Bot Stopped");
        }
    }
}