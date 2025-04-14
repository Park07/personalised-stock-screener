import TextInput from "../component/TextInput"
import AuthContainer from "../component/AuthContainer"
import AuthButton from "../component/AuthButton"
import CandleChartStock from "../component/CandleChartStock"
import { useState, useEffect } from "react"
import axios from "axios"

const Stocks = function () {
  const [tickers, setTickers] = useState('');
  const [indicators, setIndicators] = useState('SMA,EMA');
  const [timePeriod, setTimePeriod] = useState('');
  const [resolution, setResolution] = useState('');
  const [errorMessage, setErrorMessage] = useState(''); 
  const [fetchData, setFetchData] = useState(false); // State to control chart fetching
  const [recommendations, setRecommendations] = useState(''); // State to store API response

  const params = {
    tickers: tickers.trim(),
    indicators: indicators.replace(/\s+/g, ''),
    time_period: timePeriod,
    resolution: resolution.trim(),
  };

  // Trigger API call when form is submitted
  const updateParams = (event) => {
    event.preventDefault();
    console.log("Tickers:", tickers, " Indicators:", indicators, " Time Period:", timePeriod, " Resolution:", resolution);
    setFetchData(true);

    // Make the API call on form submit
    axios.get('http://35.169.25.122/advice_v1')
      .then((response) => {
        console.log(response);
        setRecommendations(response.data);  // Store the response in recommendations state
      })
      .catch((error) => {
        setErrorMessage(error.message);  // Handle error and set error message
      });
  };

  return (
    <div className="p-4 flex flex-col bg-background min-h-screen">
      <div className="p-4">
        <h1 className="text-3xl md:text-4xl font-semibold text-gray-100 mb-5 md:text-left">Stocks</h1>
      </div>
      <div className="flex flex-wrap">
        {/* Left Column: Form */}
        <div className="flex flex-col w-full sm:w-1/2 p-4">
          <AuthContainer>
            <h2 className="text-2xl font-semibold text-center text-gray-200">Select Stock</h2>
            <form onSubmit={updateParams} className="space-y-4">
              <div>
                <label htmlFor="ticker" className="block text-sm font-medium text-gray-400">Tickers</label>
                <TextInput
                  type="tickers"
                  id="tickers"
                  value={tickers}
                  onChange={(e) => setTickers(e.target.value)}
                  placeholder="Enter ticker eg: AAPL"
                />
              </div>
              <div>
                <label htmlFor="indicators" className="block text-sm font-medium text-gray-400">Indicators</label>
                <TextInput
                  type="indicators"
                  id="indicators"
                  value={indicators}
                  onChange={(e) => setIndicators(e.target.value)}
                  placeholder="Enter indicators eg: SMA"
                />
              </div>
              <div>
                <label htmlFor="timePeriod" className="block text-sm font-medium text-gray-400">Time Period</label>
                <TextInput
                  type="timePeriod"
                  id="timePeriod"
                  value={timePeriod}
                  onChange={(e) => setTimePeriod(e.target.value)}
                  placeholder="Enter time period eg: 7"
                />
              </div>
              <div>
                <label htmlFor="resolution" className="block text-sm font-medium text-gray-400">Resolution</label>
                <TextInput
                  type="resolution"
                  id="resolution"
                  value={resolution}
                  onChange={(e) => setResolution(e.target.value)}
                  placeholder="Enter resolution eg: min"
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

        {/* Right Column: Recommendations */}
        <div className="flex flex-col w-full sm:w-1/2 p-4">
          <p className="text-3xl text-gray-300 break-words whitespace-normal overflow-hidden">Recommendation:</p>
          {(
            <div className="mt-4 text-gray-200">
              <p>Recommendations are currently only available for Crypto. <br></br>Sorry for the inconvinience :(</p>  {/* Display the recommendations from the API response */}
            </div>
          )}
        </div>
      </div>

      {/* Graph Spanning Both Columns */}
      <div className="w-full px-36 pt-8">
        {fetchData && <CandleChartStock params={params} />}
      </div>
    </div>
  );
};

export default Stocks;
