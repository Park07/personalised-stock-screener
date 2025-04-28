import TextInput from "../component/TextInput"
import SelectInput from "../component/SelectInput";
import AuthContainer from "../component/AuthContainer"
import AuthButton from "../component/AuthButton"
import CandleChart from "../component/CandleChart"
import { useState, useEffect } from "react"
import axios from "axios"

const Crypto = function () {
  const [tickers, setTickers] = useState('');
  const [indicators, setIndicators] = useState('SMA,EMA');
  const [timePeriod, setTimePeriod] = useState('');
  const [resolution, setResolution] = useState('');
  const [aggregator, setAggregator] = useState('');
  const [errorMessage, setErrorMessage] = useState(''); 
  const [fetchData, setFetchData] = useState(false); // State to control chart fetching
  const [recommendations, setRecommendations] = useState(''); // State to store API response
  const [shouldFetch, setShouldFetch] = useState(false);  // Added state to trigger fetch on form submit
  const [submittedParams, setSubmittedParams] = useState(null);
  const [indicatorResolution, setIndicatorResolution] = useState(null);

  const updateGraph = (newTimePeriod, newResolution, newAggregator) => {
    if (!submittedParams) return;
  
    const newParams = {
      ...submittedParams,
      time_period: newTimePeriod,
      resolution: newResolution.trim(),
      agg: newAggregator
    };
    // const config = {
    //   url: 'http://35.169.25.122/indicators_crypto',
    //   params: newParams
    // };
    // console.log('Complete URL:', axios.getUri(config));
    setSubmittedParams(newParams);
  };

  const updateParams = (event) => {
    event.preventDefault();
  
    const normalizedTicker = tickers.trim().toUpperCase();
    const newParams = {
      tickers: normalizedTicker,
      indicators: indicators.replace(/\s+/g, ''),
      time_period: timePeriod,
      resolution: resolution.trim(),
      agg: aggregator,
    };
  
    setSubmittedParams(newParams);
    setFetchData(true);
    setShouldFetch(true); // Set to true when user submits the form
    axios.get(`http://35.169.25.122/get_analysis_v2`, {
      params: {
        tickers: tickers,
        resolution: indicatorResolution
      }
    })
    .then((response) => {
      const tickerData = response.data[normalizedTicker];

      if (tickerData) {
        setRecommendations(tickerData);  // Store the relevant recommendation data
      } else {
        setRecommendations(null);  // Handle case where ticker is not found
        setErrorMessage("Ticker for analysis not found.");
      }
    })
    .catch((error) => {
      setErrorMessage(error.message);  // Handle error and set error message
    });
  };

  return (
    <div className="p-4 flex flex-col bg-background min-h-screen">
      <div className="w-full mb-8 text-center">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-100 mb-2 inline-block border-b-2 border-blue-500 pb-1">Crypto</h1>    
      </div>
      <div className="flex flex-col sm:flex-row gap-20 justify-center">
        {/* Left Column: Form */}
        <div className="flex flex-col w-full sm:w-1/2 max-w-md">
          <AuthContainer>
            <h2 className="text-2xl font-semibold text-center text-gray-200">Select Crypto</h2>
            <form onSubmit={updateParams} className="space-y-4">
              <div>
                <label htmlFor="ticker" className="block text-sm font-medium text-gray-400">
                  <span className="inline-flex items-center gap-1">
                    Tickers
                    <span className="group relative cursor-pointer text-gray-400 hover:text-white">
                      <span>ⓘ</span>
                      <span className="absolute left-6 top-1/2 -translate-y-1/2 hidden group-hover:block bg-gray-800 text-white text-xs rounded px-2 py-1 z-10 whitespace-nowrap">
                        Valid Crypto: BTC/USD<br />
                        {/* <span className="pl-[70px]">MSFT, TSLA</span> */}
                      </span>
                    </span>
                  </span>
                </label>                
                <TextInput
                  type="tickers"
                  id="tickers"
                  value={tickers}
                  onChange={(e) => setTickers(e.target.value)}
                  placeholder="Enter ticker eg: BTC/USD"
                />
              </div>
              <div>
                <label htmlFor="timePeriod" className="block text-sm font-medium text-gray-400">Graph Time Period</label>
                <SelectInput
                  id="timePeriod"
                  value={timePeriod && resolution && aggregator ? `${timePeriod},${resolution},${aggregator}` : ""}
                  onChange={(e) => {
                    const [selectedTime, selectedResolution, selectedAggregator] = e.target.value.split(",");
                    setTimePeriod(selectedTime);
                    setResolution(selectedResolution);
                    setAggregator(selectedAggregator);
                  }}                  
                  placeholder="Please choose a time period"
                  options={[
                    { label: "24 hours", value: "1,min,2" },
                    { label: "7 Days", value: "7,min,8" },
                    { label: "30 Days", value: "30,hour,1" },
                    { label: "3 Months", value: "90,hour,3" },
                    { label: "6 Months", value: "180,hour,5" },
                    { label: "1 Year", value: "365,day,1"}
                  ]}
                />
              </div>
              <div>
                <label htmlFor="indicatorTimePeriod" className="block text-sm font-medium text-gray-400">Analysis Time Period</label>
                <SelectInput
                  id="indicatorTimePeriod"
                  value={indicatorResolution ? `${indicatorResolution}` : ""}
                  onChange={(selectedOption) => {
                    setIndicatorResolution(selectedOption.target.value);
                  }}
                  placeholder="Please choose a time period"
                  options={[
                    { label: "Now", value: "min" },
                    { label: "Couple Days", value: "hour" },
                    { label: "Couple Months", value: "day" },
                  ]}
                />
              </div>
              <AuthButton type="submit">
                Submit
              </AuthButton>
            </form>
            {errorMessage && (
              <p className="text-red-500 text-sm mt-4">{errorMessage}</p> 
            )}
          </AuthContainer>
        </div>

        {/* Right Column: Analysis */}
        <div className="flex flex-col w-full sm:w-1/2 max-w-md">
          <div className="w-full p-8 space-y-4 bg-nav rounded-lg shadow-md h-full">
            <p className="text-3xl text-gray-300 break-words whitespace-normal overflow-hidden">Crypto Analysis:</p>
            {recommendations && (
            <div className="mt-4 text-gray-200">
              <p><strong>Last Updated:</strong> {recommendations.time_stamp}</p>
              <div className="space-y-4 mt-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="font-medium text-green-400">Buy</span>
                    <span className="text-gray-300">{recommendations.buy}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2.5">
                    <div 
                      className="bg-green-500 h-2.5 rounded-full" 
                      style={{ width: `${recommendations.buy}%` }}
                    ></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="font-medium text-red-400">Sell</span>
                    <span className="text-gray-300">{recommendations.sell}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2.5">
                    <div 
                      className="bg-red-500 h-2.5 rounded-full" 
                      style={{ width: `${recommendations.sell}%` }}
                    ></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="font-medium text-amber-400">Hold</span>
                    <span className="text-gray-300">{recommendations.hold}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2.5">
                    <div 
                      className="bg-amber-500 h-2.5 rounded-full" 
                      style={{ width: `${recommendations.hold}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
            )}
            {!recommendations && (
              <div className="mt-4 text-gray-200">
                <p>Please select your Crypto first to see analysis</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Graph Spanning Both Columns */}
      <div className="w-full px-36 pt-8">
        {fetchData && submittedParams && shouldFetch ? (
          <>
            <div className="flex gap-4 mb-4 justify-center">
              <button
                onClick={() => updateGraph('1', 'min', '2')}
                className="bg-blue-500 hover:bg-blue-600 text-white py-1 px-4 rounded-lg"
              >
                24 hours
              </button>
              <button
                onClick={() => updateGraph('7', 'min', '8')}
                className="bg-blue-500 hover:bg-blue-600 text-white py-1 px-4 rounded-lg"
              >
                7 Days
              </button>
              <button
                onClick={() => updateGraph('30', 'hour', '1')}
                className="bg-blue-500 hover:bg-blue-600 text-white py-1 px-4 rounded-lg"
              >
                30 Days
              </button>
              <button
                onClick={() => updateGraph('90', 'hour', '3')}
                className="bg-blue-500 hover:bg-blue-600 text-white py-1 px-4 rounded-lg"
              >
                3 Months
              </button>
              <button
                onClick={() => updateGraph('180', 'hour', '5')}
                className="bg-blue-500 hover:bg-blue-600 text-white py-1 px-4 rounded-lg"
              >
                6 Months
              </button>
              <button
                onClick={() => updateGraph('365', 'day', '1')}
                className="bg-blue-500 hover:bg-blue-600 text-white py-1 px-4 rounded-lg"
              >
                1 Year
              </button>
            </div>
            <CandleChart params={submittedParams} />
          </>
        ) : (
          <div className="w-full h-[400px] bg-nav rounded-lg shadow-md flex items-center justify-center">
          <p className="text-gray-300 text-lg">
            Enter a ticker and select a time period to generate the chart.
          </p>
          </div>
        )}
      </div>

    </div>
  );
};

export default Crypto;
