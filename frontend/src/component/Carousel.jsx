import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Carousel = ({ ticker }) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [valuationData, setValuationData] = useState(null);
    const [error, setError] = useState(null);
    const [peChartUrl, setPeChartUrl] = useState(null);
    const [performanceChartUrl, setPerformanceChartUrl] = useState(null);
    const [cashFlowChartUrl, setCashFlowChartUrl] = useState(null);
    const [enhancedValuationChartUrl, setEnhancedValuationChartUrl] = useState(null);

    const handleNext = () => {
      if (currentIndex < boxes.length - 2) {
        setCurrentIndex(currentIndex + 1);
      }
    };
  
    const handlePrev = () => {
      if (currentIndex > 0) {
        setCurrentIndex(currentIndex - 1);
      }
    };

    useEffect(() => {
      if (!ticker) return;
    
      // PE CHART
      // axios.get("http://35.169.25.122/fundamentals/pe_chart", {
      //   params: {
      //     ticker: ticker,
      //     format: "png",
      //     theme: "dark",
      //     type: "plotly"
      //   },
      //   responseType: "blob"
      // })
      // .then(response => {
      //   console.log(response)
      //   const url = URL.createObjectURL(response.data);
      //   setPeChartUrl(url);
      // })
      // .catch(error => {
      //   console.error("Failed to load PE chart:", error);
      //   setError("Could not load PE chart.");
      // });

      // PERFOMRANCE CHART
      const fetchChart = (url, params, setChartUrl, chartName) => {
        axios.get(url, { params, responseType: "blob" })
        .then(response => setChartUrl(URL.createObjectURL(response.data)))
        .catch(err => {
          console.error(`Failed to load ${chartName}:`, err);
          setError(`Could not load ${chartName}.`);
        });
      };

      fetchChart("http://35.169.25.122/fundamentals/pe_chart", {
        ticker, format: "png", theme: "dark", type: "plotly"
      }, setPeChartUrl, "PE chart");

      fetchChart("http://35.169.25.122/fundamentals_historical/generate_yearly_performance_chart", {
        ticker, quarters: 4, dark_theme: true, format: "png"
      }, setPerformanceChartUrl, "performance chart");

      fetchChart("http://35.169.25.122/fundamentals_historical/free_cash_flow_chart", {
        ticker, years: 4, theme: "dark", format: "png"
      }, setCashFlowChartUrl, "cash flow chart");

      fetchChart("http://35.169.25.122/fundamentals/enhanced_valuation_chart", {
        ticker, theme: "dark", format: "png"
      }, setEnhancedValuationChartUrl, "valuation chart");

    }, [ticker]);

  
    const boxes = [performanceChartUrl, cashFlowChartUrl, enhancedValuationChartUrl].map((url, idx) => (
      <div key={idx} className="flex-shrink-0 p-4 bg-gray-800 rounded-md flex items-center justify-center">
        {url ? (
          <img src={url} alt={`Chart ${idx}`} className="w-full h-auto object-contain max-h-[600px] max-w-[950px]" />
        ) : (
          <p className="text-white">Loading...</p>
        )}
      </div>
    ));

    
    return (
      <div className="relative flex items-center justify-center gap-4">
        {currentIndex > 0 && (
          <button onClick={handlePrev} className="absolute left-0 z-10 bg-gray-800 text-white p-2 rounded-full">&#10094;</button>
        )}

        <div className="flex gap-6 overflow-hidden justify-center">
          {boxes.slice(currentIndex, currentIndex + 2)}
        </div>

        {currentIndex < boxes.length - 2 && (
          <button onClick={handleNext} className="absolute right-0 z-10 bg-gray-800 text-white p-2 rounded-full">&#10095;</button>
        )}
      </div>
    );

  };
  
export default Carousel;
