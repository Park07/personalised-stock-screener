import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ReactApexChart from 'react-apexcharts';

const CandleChartStock = ({ params }) => {
  const [series, setSeries] = useState([{ data: [] }]);
  const [options, setOptions] = useState({});

  useEffect(() => {

    // Make sure that the data set have roughly 1000 points
    const downsampleData = (data, maxPoints = 1000) => {
      if (data.length <= maxPoints) return data;
      
      const step = Math.ceil(data.length / maxPoints);
      const downsampled = [];
      
      for (let i = 0; i < data.length; i += step) {
        const chunk = data.slice(i, i + step);
        if (chunk.length === 0) continue;
        
        downsampled.push({
          x: chunk[0].x, 
          y: [
            Math.min(...chunk.map(d => d.y[0])), 
            Math.max(...chunk.map(d => d.y[1])), 
            Math.min(...chunk.map(d => d.y[2])), 
            chunk[chunk.length-1].y[3] 
          ]
        });
      }
      return downsampled;
    };

    axios.get('http://35.169.25.122/indicators_stocks', { params })
      .then((response) => {
        const data = JSON.parse(response.data);
        const rawData = data.stock_data[params.tickers];   

        const chartData = rawData.map(item => {
          const dateParts = item.timestamp.split(/[- :+]/);
          const [year, month, day, hour, minute] = dateParts.map(Number);
          const timestamp = new Date(Date.UTC(year, month - 1, day, hour, minute));
          const formattedTimestamp = timestamp.toLocaleString("en-GB", { 
            timeZoneName: "short",
            hour: "2-digit",
            minute: "2-digit",
            year: "2-digit",
            month: "2-digit",
            day: "2-digit"
          });
          return {
            x: formattedTimestamp,
            y: [
              item.open,
              item.high,
              item.low,
              item.close
            ]
          }
        });        
        
        const downsampledData  = downsampleData(chartData, 500);

        setOptions({
          chart: {
            type: 'candlestick',
            height: 350,
            zoom: { enabled: true },
          },
          title: { text: `${params.tickers} Candlestick Chart`, align: 'left' },
          xaxis: { type: 'category', tickAmount: 10, labels: { formatter: function(value) {return value;} }},
          yaxis: { tooltip: { enabled: true }, labels: { formatter: (val) => val.toFixed(2) }},        
        });
        setSeries([{ data: downsampledData }]);
      })
      .catch(error => console.error('Error fetching data:', error));
  }, [params]);

  return (
    <div id="chart">
      <ReactApexChart options={options} series={series} type="candlestick" height={350} />
    </div>
  );
};

export default CandleChartStock;