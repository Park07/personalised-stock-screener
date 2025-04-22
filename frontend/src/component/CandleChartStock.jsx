import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ReactApexChart from 'react-apexcharts';

const CandleChartStock = ({ params }) => {
  const [chartData, setChartData] = useState({
    series: [],
    options: {}
  });

  const formatTimestamp = (timestampStr) => {
    const dateParts = timestampStr.split(/[- :+]/);
    const [year, month, day, hour, minute] = dateParts.map(Number);
    return new Date(Date.UTC(year, month - 1, day, hour, minute)).getTime();
  };

  const processIndicatorData = (rawData, indicatorKey) => { 
    return rawData.map(item => {
      const value = Number(item[indicatorKey]);
      return {
        x: formatTimestamp(item.timestamp),
        y: isNaN(value) ? null : Number(value.toFixed(2))
      };
    }).filter(item => !isNaN(item.y));
  };

  const processData = (rawData, valueExtractor) => {
    return rawData.map(item => ({
      x: formatTimestamp(item.timestamp),
      y: valueExtractor(item)
    }));
  };

  useEffect(() => {
    let limit = false;
    if (params.time_period === '1') {
      params.time_period = '3';
      limit = true;
    }

    axios.get('http://35.169.25.122/indicators_stocks', { params })
      .then((response) => {
        const data = JSON.parse(response.data);
        let rawData = data.stock_data[params.tickers];   
        if (limit) rawData = rawData.slice(0, 1440);

        const OHCLData = processData(rawData, item => [
          Number(item.open.toFixed(2)),
          Number(item.high.toFixed(2)),
          Number(item.low.toFixed(2)),
          Number(item.close.toFixed(2))
        ]);

        const smaData = processIndicatorData(rawData, 'SMA');
        const emaData = processIndicatorData(rawData, 'EMA');
        const vwapData = processIndicatorData(rawData, 'vwap');

        const baseOptions = {
          chart: { 
            height: 650, 
            foreColor: '#fff', 
            animations: { enabled: false }, 
            zoom: { enabled: false }, 
            toolbar: { show: true } 
          },
          xaxis: { 
            type: 'datetime', 
            tickAmount: 10,
            labels: {
              formatter: function(value) {
                const timestamp = new Date(Number(value));
                return timestamp.toLocaleString("en-GB", {
                  timeZoneName: "short",
                  hour: "2-digit",
                  minute: "2-digit",
                  year: "2-digit",
                  month: "2-digit",
                  day: "2-digit"
                });            
              }
            }          
          },
          stroke: { width: [1, 3, 3, 3] },
          yaxis: { 
            title: { text: 'Price (USD)' },
            labels: { formatter: (val) => val }
          },
          title: {
            text: `${params.tickers} Price Analysis`,
            align: 'left',
            style: {
              fontSize: '16px',
              color: '#fff'
            }
          },
          legend: {
            show: true,
            position: 'top',
            horizontalAlign: 'right',
            fontSize: '12px',
            markers: {
              width: 12,
              height: 12,
              strokeWidth: 0,
              strokeColor: '#fff',
              radius: 12,
            }
          },
          tooltip: {
            shared: true,
            intersect: false,
            x: {
              format: 'dd MMM yyyy HH:mm'
            }
          }
        };

        setChartData({
          series: [
            {
              name: 'OHLC',
              type: 'candlestick',
              data: OHCLData
            },
            {
              name: 'SMA',
              type: 'line',
              data: smaData,
              color: '#FF4560',
              stroke: { width: 2 }
            },
            {
              name: 'EMA',
              type: 'line',
              data: emaData,
              color: '#008FFB',
              stroke: { width: 2 }
            },
            {
              name: 'VWAP',
              type: 'line',
              data: vwapData,
              color: '#FEB019',
              stroke: { width: 2 }
            }
          ],
          options: baseOptions
        });
      })
      .catch(console.error);
  }, [params]);

  return (
    <div className="chart-container">
      <ReactApexChart 
        options={chartData.options} 
        series={chartData.series} 
        type="candlestick" 
        height={650} 
      />
    </div>
  );
};

export default CandleChartStock;