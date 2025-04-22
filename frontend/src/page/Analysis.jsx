
import { useState } from "react";
import AuthButton from "../component/AuthButton";
import Carousel from "../component/Carousel";

const Analysis = () => {
  const [inputValue, setInputValue] = useState(""); 
  const [ticker, setTicker] = useState("");

  const handleSearch = () => {
    setTicker(inputValue.trim());

  };

  return (
    <div className="h-screen bg-background flex flex-col items-center gap-8 p-6">

      {/* Page Title */}
      <h1 className="text-3xl md:text-4xl font-semibold text-gray-100 border-b-2 border-blue-500 pb-1 inline-block">
        Analysis
      </h1>

      {/* Enhanced Ticker Input */}
      <div className="w-full max-w-2xl flex gap-4 bg-nav p-4 rounded-lg shadow-lg">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Enter ticker (e.g., AAPL)"
          className="flex-grow bg-transparent outline-none text-white placeholder-gray-400 text-lg"
        />
        <AuthButton type="submit" className="px-6 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 transition duration-300" onClick={handleSearch}>
          Search
        </AuthButton>
      </div>

      {/* Display Carousel or Default Info */}
      {ticker ? (
        <div className="w-full flex-1 flex justify-center">
          <Carousel ticker={ticker} />
        </div>
      ) : (
        <div className="w-full max-w-3xl text-center flex-1 flex flex-col justify-center items-center gap-4">
          <p className="text-xl text-gray-300">Start by entering a ticker to see detailed analysis.</p>
          <div className="bg-nav text-gray-300 rounded-lg p-4 shadow-lg">
            Example tickers: <span className="font-bold">AAPL, NVDA, AMZN, GOOG</span>
          </div>
        </div>
      )}
      {/* Risk Tolerance */}
      {/* <div className="w-full max-w-3xl">
        <span className="text-white font-bold block mb-2">Risk Tolerance</span>
        <div className="flex gap-4">
          {["Conservative", "Moderate", "Aggressive"].map((label) => (
            <AuthButton key={label} type="button" className="w-full">
              {label}
            </AuthButton>
          ))}
        </div>
      </div> */}

      {/* Investment Goal */}
      {/* <div className="w-full max-w-3xl">
        <span className="text-white font-bold block mb-2">Investment Goal</span>
        <div className="flex gap-4">
          {["Income", "Balanced", "Growth"].map((label) => (
            <AuthButton key={label} type="button" className="w-full">
              {label}
            </AuthButton>
          ))}
        </div>
      </div> */}

      {/* Footer/Other Stuff */}
      {/* <div className="w-full text-center mt-8">
        <h2 className="text-3xl text-white">Other stuff</h2>
      </div> */}
    </div>
  );
};

export default Analysis;
