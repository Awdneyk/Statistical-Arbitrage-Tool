using System;
using System.IO;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.FullAccess)]
    public class PriceDataExtractorBot : Robot
    {
        [Parameter("Symbol A", DefaultValue = "GOOGL.US")]
        public string SymbolA { get; set; }

        [Parameter("Symbol B", DefaultValue = "AAPL.US")]
        public string SymbolB { get; set; }

        [Parameter("Timeframe", DefaultValue = "Minute")]
        public string Timeframe { get; set; }

        [Parameter("History Days", DefaultValue = 180)]
        public int HistoryDays { get; set; }

        private Symbol _symbolAData;
        private Symbol _symbolBData;
        private TimeFrame _timeFrame;
        private string _csvFilePath;
        private StreamWriter _csvWriter;

        protected override void OnStart()
        {
            try
            {
                _symbolAData = Symbols.GetSymbol(SymbolA);
                _symbolBData = Symbols.GetSymbol(SymbolB);

                if (_symbolAData == null)
                {
                    Print($"❌ Error: Symbol A '{SymbolA}' not found");
                    Stop();
                    return;
                }

                if (_symbolBData == null)
                {
                    Print($"❌ Error: Symbol B '{SymbolB}' not found");
                    Stop();
                    return;
                }

                _timeFrame = ParseTimeFrame(Timeframe);
                if (_timeFrame == null)
                {
                    Print($"❌ Error: Invalid timeframe '{Timeframe}'. Use: Minute, Hour, Daily, etc.");
                    Stop();
                    return;
                }

                _csvFilePath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "your_price_data.csv");

                CreateCsvFileWithHistoricalData();

                Print($"✅ Historical data export complete");
                Print($"📁 CSV file created at: {_csvFilePath}");
            }
            catch (Exception ex)
            {
                Print($"❌ OnStart Error: {ex.Message}");
                Stop();
            }
        }

        private TimeFrame ParseTimeFrame(string timeframe)
        {
            switch (timeframe.ToLower())
            {
                case "minute":
                case "m1":
                    return TimeFrame.Minute;
                case "minute5":
                case "m5":
                    return TimeFrame.Minute5;
                case "minute15":
                case "m15":
                    return TimeFrame.Minute15;
                case "minute30":
                case "m30":
                    return TimeFrame.Minute30;
                case "hour":
                case "h1":
                    return TimeFrame.Hour;
                case "hour4":
                case "h4":
                    return TimeFrame.Hour4;
                case "daily":
                case "d1":
                    return TimeFrame.Daily;
                case "weekly":
                case "w1":
                    return TimeFrame.Weekly;
                case "monthly":
                case "mn1":
                    return TimeFrame.Monthly;
                default:
                    return null;
            }
        }

        private void CreateCsvFileWithHistoricalData()
        {
            try
            {
                var fromDate = DateTime.Now.AddDays(-HistoryDays);
                var toDate = DateTime.Now;

                Print($"📅 Fetching historical data from {fromDate:yyyy-MM-dd} to {toDate:yyyy-MM-dd} ({HistoryDays} days)");
                Print($"⚠️ Note: GetBars() may only return recent cached data. For full historical data, ensure cTrader has loaded the required history.");

                // Use MarketData.GetBars to fetch bars, then filter by date range
                var barsA = MarketData.GetBars(_timeFrame, _symbolAData.Name);
                var barsB = MarketData.GetBars(_timeFrame, _symbolBData.Name);
                
                // Check if bars were retrieved successfully
                if (barsA == null || barsB == null)
                {
                    Print($"❌ Error: Unable to fetch bars for one or both symbols");
                    return;
                }

                Print($"📊 Total bars available: {SymbolA} = {barsA.Count} bars, {SymbolB} = {barsB.Count} bars");

                // Filter bars to get data within the specified date range
                var filteredBarsA = barsA.Where(bar => bar.OpenTime >= fromDate && bar.OpenTime <= toDate).ToArray();
                var filteredBarsB = barsB.Where(bar => bar.OpenTime >= fromDate && bar.OpenTime <= toDate).ToArray();

                Print($"📊 Filtered Data Retrieved: {SymbolA} = {filteredBarsA.Length} bars, {SymbolB} = {filteredBarsB.Length} bars");
                
                if (filteredBarsA.Length > 0)
                    Print($"📈 {SymbolA} date range: {filteredBarsA.First().OpenTime:yyyy-MM-dd} to {filteredBarsA.Last().OpenTime:yyyy-MM-dd}");
                if (filteredBarsB.Length > 0)
                    Print($"📈 {SymbolB} date range: {filteredBarsB.First().OpenTime:yyyy-MM-dd} to {filteredBarsB.Last().OpenTime:yyyy-MM-dd}");

                if (filteredBarsA == null || filteredBarsB == null || filteredBarsA.Length == 0 || filteredBarsB.Length == 0)
                {
                    Print($"❌ Error: Unable to fetch historical data for one or both symbols");
                    return;
                }

                using (var writer = new StreamWriter(_csvFilePath, false))
                {
                    writer.WriteLine("timestamp,AAPL_close,GOOGL_close");

                    var indexA = 0;
                    var indexB = 0;

                    while (indexA < filteredBarsA.Length && indexB < filteredBarsB.Length)
                    {
                        var barA = filteredBarsA[indexA];
                        var barB = filteredBarsB[indexB];

                        if (barA.OpenTime == barB.OpenTime)
                        {
                            var timestamp = barA.OpenTime.ToString("yyyy-MM-dd HH:mm:ss");
                            var aaplClose = SymbolA == "AAPL.US" ? barA.Close : barB.Close;
                            var googlClose = SymbolA == "GOOGL.US" ? barA.Close : barB.Close;
                            
                            writer.WriteLine($"{timestamp},{aaplClose},{googlClose}");
                            indexA++;
                            indexB++;
                        }
                        else if (barA.OpenTime < barB.OpenTime)
                        {
                            indexA++;
                        }
                        else
                        {
                            indexB++;
                        }
                    }
                }

                _csvWriter = new StreamWriter(_csvFilePath, true);

                Print($"📊 Historical data exported: {Math.Min(filteredBarsA.Length, filteredBarsB.Length)} aligned records");
            }
            catch (Exception ex)
            {
                Print($"❌ CreateCsvFileWithHistoricalData Error: {ex.Message}");
            }
        }

        protected override void OnBar()
        {
            try
            {
                if (_csvWriter == null)
                    return;

                var barsA = MarketData.GetBars(_timeFrame, _symbolAData.Name);
                var barsB = MarketData.GetBars(_timeFrame, _symbolBData.Name);

                if (barsA.Count == 0 || barsB.Count == 0)
                    return;

                var latestBarA = barsA.Last(1);
                var latestBarB = barsB.Last(1);

                if (latestBarA.OpenTime == latestBarB.OpenTime)
                {
                    var timestamp = latestBarA.OpenTime.ToString("yyyy-MM-dd HH:mm:ss");
                    var aaplClose = SymbolA == "AAPL.US" ? latestBarA.Close : latestBarB.Close;
                    var googlClose = SymbolA == "GOOGL.US" ? latestBarA.Close : latestBarB.Close;

                    _csvWriter.WriteLine($"{timestamp},{aaplClose},{googlClose}");
                    _csvWriter.Flush();

                    Print($"📈 New bar appended: {timestamp} | AAPL: {aaplClose} | GOOGL: {googlClose}");
                }
            }
            catch (Exception ex)
            {
                Print($"❌ OnBar Error: {ex.Message}");
            }
        }

        protected override void OnStop()
        {
            try
            {
                if (_csvWriter != null)
                {
                    _csvWriter.Flush();
                    _csvWriter.Close();
                    _csvWriter.Dispose();
                    _csvWriter = null;
                }

                Print($"🛑 Price Data Export Bot Stopped");
                Print($"📁 Final CSV file saved at: {_csvFilePath}");
            }
            catch (Exception ex)
            {
                Print($"❌ OnStop Error: {ex.Message}");
            }
        }
    }
}