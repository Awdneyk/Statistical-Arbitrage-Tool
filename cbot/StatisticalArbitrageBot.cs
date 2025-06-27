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

        [Parameter("Risk Percent", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 10.0)]
        public double RiskPercent { get; set; }

        [Parameter("Min Volatility", DefaultValue = 0.0001, MinValue = 0.00001)]
        public double MinVolatility { get; set; }

        [Parameter("Vol Scaling Factor", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 5.0)]
        public double VolScalingFactor { get; set; }

        [Parameter("Max Volume (0 = unlimited)", DefaultValue = 0, MinValue = 0)]
        public int MaxVolume { get; set; }

        [Parameter("Label", DefaultValue = "StatArb")]
        public string Label { get; set; }

        [Parameter("Max Trade Duration (minutes)", DefaultValue = 30)]
        public int MaxTradeDurationMinutes { get; set; }

        private Symbol _symbolAData;
        private Symbol _symbolBData;
        private RollingWindow _spreadWindow;
        private bool _hasPosition;
        private TradeType _currentTradeType;
        private DateTime _lastLogTime;
        private DateTime _positionEntryTime;
        private bool _stopLossSet;

        protected override void OnStart()
        {
            _symbolAData = Symbols.GetSymbol(SymbolA);
            _symbolBData = Symbols.GetSymbol(SymbolB);
            _spreadWindow = new RollingWindow(WindowSize);
            _hasPosition = false;
            _lastLogTime = DateTime.MinValue;

            Print($"🚀 Statistical Arbitrage Bot Started");
            Print($"📊 Symbol A: {SymbolA}, Symbol B: {SymbolB}");
            Print($"📈 Hedge Ratio: {HedgeRatio}, Window Size: {WindowSize}");
            Print($"🎯 Entry Threshold: {EntryThreshold}, Exit Threshold: {ExitThreshold}");
            Print($"💰 Risk Percent: {RiskPercent}%, Vol Scaling: {VolScalingFactor}");
            Print($"📏 Max Volume: {(MaxVolume > 0 ? MaxVolume.ToString() : "Unlimited")}");
            Print($"⏰ Max Trade Duration: {MaxTradeDurationMinutes} minutes");
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
                CheckTimeBasedExit();
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

            // Get the current standard deviation from the spread window
            double currentStdDev = _spreadWindow.StandardDeviation;

            if (zScore > EntryThreshold)
            {
                ExecutePairTrade(TradeType.Sell, TradeType.Buy, currentStdDev);
                _currentTradeType = TradeType.Sell;
                Print($"📉 ENTRY: Short {SymbolA}, Long {SymbolB} | Z-Score: {zScore:F4}");
            }
            else if (zScore < -EntryThreshold)
            {
                ExecutePairTrade(TradeType.Buy, TradeType.Sell, currentStdDev);
                _currentTradeType = TradeType.Buy;
                Print($"📈 ENTRY: Long {SymbolA}, Short {SymbolB} | Z-Score: {zScore:F4}");
            }
        }

        private void CheckExitConditions(double zScore)
        {
            if (Math.Abs(zScore) > ExitThreshold)
                return;

            // Use _currentTradeType to provide more specific exit information
            string tradeDirection = _currentTradeType == TradeType.Buy ? "LONG" : "SHORT";
            CloseAllPositions();
            Print($"🔄 EXIT: {tradeDirection} positions closed | Z-Score: {zScore:F4}");
        }

        private void CheckTimeBasedExit()
        {
            if (!_hasPosition)
                return;

            var timeSinceEntry = DateTime.Now.Subtract(_positionEntryTime);
            if (timeSinceEntry.TotalMinutes < MaxTradeDurationMinutes)
                return;

            // Calculate current net profit
            var positionsA = Positions.FindAll(Label + "_A");
            var positionsB = Positions.FindAll(Label + "_B");
            double totalPnl = positionsA.Sum(p => p.NetProfit) + positionsB.Sum(p => p.NetProfit);

            string tradeDirection = _currentTradeType == TradeType.Buy ? "LONG" : "SHORT";

            if (totalPnl >= 0)
            {
                // Profit: Set stop loss at current market price (if not already set)
                if (!_stopLossSet)
                {
                    SetStopLossAtCurrentPrice(positionsA, positionsB);
                    _stopLossSet = true;
                    Print($"⏰ TIME-BASED STOP LOSS: {tradeDirection} positions | Duration: {timeSinceEntry.TotalMinutes:F1}min | PnL: ${totalPnl:F2}");
                }
            }
            else
            {
                // Loss: Immediately close positions
                CloseAllPositions();
                Print($"⏰ TIME-BASED EXIT: {tradeDirection} positions closed | Duration: {timeSinceEntry.TotalMinutes:F1}min | PnL: ${totalPnl:F2}");
            }
        }

        private void SetStopLossAtCurrentPrice(Position[] positionsA, Position[] positionsB)
        {
            try
            {
                foreach (var position in positionsA)
                {
                    double stopLossPrice = position.TradeType == TradeType.Buy ? _symbolAData.Bid : _symbolAData.Ask;
                    position.ModifyStopLossPrice(stopLossPrice);
                }

                foreach (var position in positionsB)
                {
                    double stopLossPrice = position.TradeType == TradeType.Buy ? _symbolBData.Bid : _symbolBData.Ask;
                    position.ModifyStopLossPrice(stopLossPrice);
                }
            }
            catch (Exception ex)
            {
                Print($"❌ Stop Loss Set Error: {ex.Message}");
            }
        }

        private void ExecutePairTrade(TradeType tradeTypeA, TradeType tradeTypeB, double stdDev)
        {
            try
            {
                // 📌 1. Calculate percentage-of-equity-based capital
                double capital = Account.Equity * RiskPercent / 100.0;
                Print($"💰 Capital allocated: ${capital:F2} ({RiskPercent}% of ${Account.Equity:F2})");

                // 📌 2. Calculate volumes with margin awareness and volatility scaling
                var volumes = CalculateVolumes(capital, stdDev, tradeTypeA);

                if (volumes.VolumeA == 0 || volumes.VolumeB == 0)
                {
                    Print($"⚠️ Trade skipped: Insufficient volume calculation");
                    return;
                }

                // 📌 3. Margin check before execution
                double marginA = _symbolAData.GetEstimatedMargin(tradeTypeA, volumes.VolumeA);
                double marginB = _symbolBData.GetEstimatedMargin(tradeTypeB, volumes.VolumeB);
                double totalMargin = marginA + marginB;

                if (totalMargin > Account.FreeMargin)
                {
                    Print($"❌ Trade skipped: Insufficient margin. Required: ${totalMargin:F2}, Available: ${Account.FreeMargin:F2}");
                    return;
                }

                // 📌 4. Log trade details
                Print($"🎯 Executing {tradeTypeA} {SymbolA} / {tradeTypeB} {SymbolB}:");
                Print($"   💵 Capital: ${capital:F2}");
                Print($"   📊 Volatility (StdDev): {stdDev:F6}");
                Print($"   📏 Volume A ({SymbolA}): {volumes.VolumeA}");
                Print($"   📏 Volume B ({SymbolB}): {volumes.VolumeB}");
                Print($"   💳 Total Margin: ${totalMargin:F2}");

                // Execute trades
                var resultA = ExecuteMarketOrder(tradeTypeA, _symbolAData.Name, volumes.VolumeA, Label + "_A");
                var resultB = ExecuteMarketOrder(tradeTypeB, _symbolBData.Name, volumes.VolumeB, Label + "_B");

                if (resultA.IsSuccessful && resultB.IsSuccessful)
                {
                    _hasPosition = true;
                    _positionEntryTime = DateTime.Now;
                    _stopLossSet = false;
                    Print($"✅ Pair trade executed successfully");
                    Print($"   📈 {SymbolA}: {tradeTypeA} {volumes.VolumeA} @ {(tradeTypeA == TradeType.Buy ? _symbolAData.Ask : _symbolAData.Bid):F5}");
                    Print($"   📉 {SymbolB}: {tradeTypeB} {volumes.VolumeB} @ {(tradeTypeB == TradeType.Buy ? _symbolBData.Ask : _symbolBData.Bid):F5}");
                    Print($"   ⏰ Entry Time: {_positionEntryTime:HH:mm:ss}");
                }
                else
                {
                    Print($"❌ Trade execution failed:");
                    if (!resultA.IsSuccessful)
                        Print($"   Symbol A Error: {resultA.Error}");
                    if (!resultB.IsSuccessful)
                        Print($"   Symbol B Error: {resultB.Error}");

                    // Close any successful position if the other failed
                    if (resultA.IsSuccessful)
                        resultA.Position.Close();
                    if (resultB.IsSuccessful)
                        resultB.Position.Close();
                }
            }
            catch (Exception ex)
            {
                Print($"❌ ExecutePairTrade Error: {ex.Message}");
            }
        }

        private (long VolumeA, long VolumeB) CalculateVolumes(double capital, double stdDev, TradeType tradeTypeA)
        {
            try
            {
                // 📌 2. Estimate margin per unit for both symbols
                // Convert VolumeInUnitsMin to long explicitly to avoid type conversion issues
                long minVolumeA = (long)_symbolAData.VolumeInUnitsMin;
                long minVolumeB = (long)_symbolBData.VolumeInUnitsMin;

                double marginPerUnitA = _symbolAData.GetEstimatedMargin(tradeTypeA, minVolumeA) / minVolumeA;
                double marginPerUnitB = _symbolBData.GetEstimatedMargin(tradeTypeA == TradeType.Buy ? TradeType.Sell : TradeType.Buy, minVolumeB) / minVolumeB;

                // 📌 3. Volatility-based scaling
                double volAdjustment = (1.0 / Math.Max(stdDev, MinVolatility)) * VolScalingFactor;

                // Calculate base volumes considering both symbols' margin requirements and hedge ratio
                double totalMarginPerUnit = marginPerUnitA + (marginPerUnitB * HedgeRatio);
                
                // Validate margin calculation to avoid division by zero
                if (totalMarginPerUnit <= 0)
                {
                    Print($"⚠️ Invalid margin calculation: {totalMarginPerUnit:F6}");
                    return (Volume, (long)(Volume * HedgeRatio));
                }
                
                double baseVolume = capital / totalMarginPerUnit;

                // Apply volatility adjustment with bounds checking
                double adjustedVolume = baseVolume * volAdjustment;

                // Apply max volume cap if specified
                if (MaxVolume > 0)
                {
                    adjustedVolume = Math.Min(adjustedVolume, (double)MaxVolume);
                }

                // Convert to valid volumes for each symbol with explicit casting
                long volumeA = (long)_symbolAData.NormalizeVolumeInUnits(adjustedVolume, RoundingMode.Down);
                long volumeB = (long)_symbolBData.NormalizeVolumeInUnits(adjustedVolume * HedgeRatio, RoundingMode.Down);

                // Ensure minimum volumes
                volumeA = Math.Max(volumeA, minVolumeA);
                volumeB = Math.Max(volumeB, minVolumeB);

                // Fallback to original logic if calculation fails
                if (volumeA == 0 || volumeB == 0)
                {
                    volumeA = Volume;
                    volumeB = (long)(Volume * HedgeRatio);
                    Print($"⚠️ Using fallback volumes: A={volumeA}, B={volumeB}");
                }

                Print($"📊 Volume Calculation:");
                Print($"   💰 Base Volume: {baseVolume:F2}");
                Print($"   📈 Vol Adjustment: {volAdjustment:F4}");
                Print($"   🎯 Final Volume A: {volumeA}");
                Print($"   🎯 Final Volume B: {volumeB}");

                return (volumeA, volumeB);
            }
            catch (Exception ex)
            {
                Print($"❌ Volume Calculation Error: {ex.Message}");
                // Return fallback volumes
                return (Volume, (long)(Volume * HedgeRatio));
            }
        }

        private void CloseAllPositions()
        {
            var positionsA = Positions.FindAll(Label + "_A");
            var positionsB = Positions.FindAll(Label + "_B");
            var allPositions = positionsA.Concat(positionsB);

            double totalPnlA = positionsA.Sum(p => p.NetProfit);
            double totalPnlB = positionsB.Sum(p => p.NetProfit);
            double totalPnl = totalPnlA + totalPnlB;

            foreach (var position in allPositions)
            {
                position.Close();
            }

            if (allPositions.Any())
            {
                Print($"💰 Position PnL Summary:");
                Print($"   📈 {SymbolA} PnL: ${totalPnlA:F2}");
                Print($"   📉 {SymbolB} PnL: ${totalPnlB:F2}");
                Print($"   💰 Total PnL: ${totalPnl:F2}");
            }

            _hasPosition = false;
            _stopLossSet = false;
            // Reset trade type when positions are closed
            _currentTradeType = TradeType.Buy; // Default value, will be set on next entry
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
                Print($"📊 Spread: {spread:F6} | Mean: {mean:F6} | StdDev: {stdDev:F6} | Z-Score: {zScore:F4} | HasPos: {_hasPosition} | Equity: ${Account.Equity:F2}");
                _lastLogTime = DateTime.Now;
            }
        }

        protected override void OnStop()
        {
            if (_hasPosition)
            {
                Print("🛑 Bot stopping - closing open positions");
                CloseAllPositions();
            }
            Print("🏁 Statistical Arbitrage Bot Stopped");
        }
    }
}