import React, { useEffect, useRef, useState } from 'react';

const SpiderChart = ({ scores }) => {
  const canvasRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  
  // Add a resize observer to handle responsive sizing
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const parent = canvas.parentElement;
    
    const updateDimensions = () => {
      const { width, height } = parent.getBoundingClientRect();
      setDimensions({ width, height });
      
      // Set canvas dimensions with device pixel ratio for sharper rendering
      const dpr = window.devicePixelRatio || 1;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
    };
    
    // Initial dimensions
    updateDimensions();
    
    // Setup resize observer
    const resizeObserver = new ResizeObserver(() => {
      updateDimensions();
    });
    
    resizeObserver.observe(parent);
    
    // Cleanup
    return () => {
      resizeObserver.disconnect();
    };
  }, [canvasRef]);
  
  // Draw the chart when scores or dimensions change
  useEffect(() => {
    if (!canvasRef.current || !scores || dimensions.width === 0 || dimensions.height === 0) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Scale for device pixel ratio
    const dpr = window.devicePixelRatio || 1;
    if (dpr > 1) {
      ctx.scale(dpr, dpr);
    }
    
    const centerX = dimensions.width / 2;
    const centerY = dimensions.height / 2;
    const radius = Math.min(centerX, centerY) * 0.8;
    
    // Clear canvas
    ctx.clearRect(0, 0, dimensions.width, dimensions.height);
    
    // Score categories and values (ensure they all exist before proceeding)
    const categories = [
      { key: 'overall_score', label: 'Overall' },
      { key: 'valuation_score', label: 'Valuation' },
      { key: 'growth_score', label: 'Growth' },
      { key: 'health_score', label: 'Health' }
    ];
    
    const validCategories = categories.filter(cat => 
      typeof scores[cat.key] === 'number' && !isNaN(scores[cat.key])
    );
    
    if (validCategories.length === 0) {
      // Draw placeholder text if no valid data
      ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
      ctx.font = '16px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('No score data available', centerX, centerY);
      return;
    }
    
    const angleStep = (2 * Math.PI) / validCategories.length;
    
    // Draw background circles
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.setLineDash([]);
    
    for (let r = 1; r <= 5; r++) {
      const circleRadius = (radius / 5) * r;
      ctx.beginPath();
      ctx.arc(centerX, centerY, circleRadius, 0, 2 * Math.PI);
      ctx.stroke();
    }
    
    // Draw axis lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    
    validCategories.forEach((_, i) => {
      const angle = i * angleStep - Math.PI / 2;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(
        centerX + radius * Math.cos(angle),
        centerY + radius * Math.sin(angle)
      );
      ctx.stroke();
    });
    
    // Draw labels
    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    validCategories.forEach((category, i) => {
      const angle = i * angleStep - Math.PI / 2;
      const labelX = centerX + (radius + 20) * Math.cos(angle);
      const labelY = centerY + (radius + 20) * Math.sin(angle);
      
      ctx.fillText(category.label, labelX, labelY);
    });
    
    // Draw score value labels on each axis
    ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.font = '10px sans-serif';
    
    for (let r = 1; r <= 5; r++) {
      ctx.fillText(
        r.toString(),
        centerX + 5,
        centerY - (radius / 5) * r + 10
      );
    }
    
    // Draw data points and connect them
    ctx.fillStyle = 'rgba(59, 130, 246, 0.6)';
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.8)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    validCategories.forEach((category, i) => {
      const angle = i * angleStep - Math.PI / 2;
      const value = scores[category.key] || 0;
      const valueRadius = (radius / 5) * Math.min(Math.max(value, 0), 5);
      
      const x = centerX + valueRadius * Math.cos(angle);
      const y = centerY + valueRadius * Math.sin(angle);
      
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    // Close the path back to the first point
    const firstCategory = validCategories[0];
    const firstAngle = -Math.PI / 2; // Start at top (first category)
    const firstValue = scores[firstCategory.key] || 0;
    const firstValueRadius = (radius / 5) * Math.min(Math.max(firstValue, 0), 5);
    
    ctx.lineTo(
      centerX + firstValueRadius * Math.cos(firstAngle),
      centerY + firstValueRadius * Math.sin(firstAngle)
    );
    
    ctx.closePath();
    ctx.globalAlpha = 0.5;
    ctx.fillStyle = 'rgba(59, 130, 246, 0.3)';
    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.8)';
    ctx.stroke();
    
    // Draw data points with values
    validCategories.forEach((category, i) => {
      const angle = i * angleStep - Math.PI / 2;
      const value = scores[category.key] || 0;
      const valueRadius = (radius / 5) * Math.min(Math.max(value, 0), 5);
      
      const x = centerX + valueRadius * Math.cos(angle);
      const y = centerY + valueRadius * Math.sin(angle);
      
      // Draw point
      ctx.beginPath();
      ctx.arc(x, y, 5, 0, 2 * Math.PI);
      ctx.fillStyle = 'rgba(59, 130, 246, 1)';
      ctx.fill();
      ctx.strokeStyle = 'white';
      ctx.lineWidth = 1;
      ctx.stroke();
      
      // Draw value text
      ctx.fillStyle = 'white';
      ctx.font = 'bold 12px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const textX = centerX + (valueRadius + 15) * Math.cos(angle);
      const textY = centerY + (valueRadius + 15) * Math.sin(angle);
      ctx.fillText(value.toFixed(1), textX, textY);
    });
    
  }, [scores, dimensions]);
  
  return (
    <div className="w-full h-full flex items-center justify-center">
      <canvas 
        ref={canvasRef} 
        className="w-full h-full"
        style={{ display: 'block' }}
      />
    </div>
  );
};

export default SpiderChart;