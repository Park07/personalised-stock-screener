import React, { useEffect, useRef } from 'react';

const SpiderChart = ({ scores }) => {
  const canvasRef = useRef(null);
  
  // Add debug logging
  useEffect(() => {
    console.log("SpiderChart received scores:", scores);
    
    // Check if scores are valid
    const isValid = scores && 
                   typeof scores === 'object' && 
                   Object.keys(scores).length > 0 &&
                   Object.values(scores).some(val => typeof val === 'number');
    
    console.log("Are scores valid for rendering?", isValid);
    
    if (!isValid) {
      console.warn("Invalid scores provided to SpiderChart:", scores);
    }
  }, [scores]);
  
  useEffect(() => {
    if (!canvasRef.current || !scores) {
      console.log("SpiderChart: Missing canvas ref or scores, skipping render");
      return;
    }
    
    // Check if any score is NaN or null
    const hasNaN = Object.values(scores).some(val => 
      val === null || val === undefined || isNaN(val)
    );
    
    if (hasNaN) {
      console.warn("SpiderChart: Some scores are NaN or null:", scores);
    }
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Get parent dimensions
    const parent = canvas.parentElement;
    const { width, height } = parent.getBoundingClientRect();
    
    console.log("SpiderChart: Parent dimensions:", width, height);
    
    // Set canvas size to match parent
    canvas.width = width;
    canvas.height = height;
    
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(centerX, centerY) * 0.8;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Score categories and values
    const categories = [
      { key: 'overall_score', label: 'Overall' },
      { key: 'valuation_score', label: 'Valuation' },
      { key: 'growth_score', label: 'Growth' },
      { key: 'health_score', label: 'Health' }
    ];
    
    // Filter for valid categories (non-null, defined values)
    const validCategories = categories.filter(cat => 
      scores[cat.key] !== null && 
      scores[cat.key] !== undefined && 
      !isNaN(scores[cat.key])
    );
    
    console.log("SpiderChart: Valid categories:", validCategories.length);
    
    if (validCategories.length === 0) {
      // Draw text indicating no data
      ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
      ctx.font = '14px sans-serif';
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
      
      // Ensure score is a valid number between 0 and 5
      let value = scores[category.key];
      if (value === null || value === undefined || isNaN(value)) {
        value = 0;
      }
      value = Math.max(0, Math.min(5, value)); // Clamp between 0 and 5
      
      const valueRadius = (radius / 5) * value;
      
      const x = centerX + valueRadius * Math.cos(angle);
      const y = centerY + valueRadius * Math.sin(angle);
      
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    // Close the path
    const firstCategory = validCategories[0];
    const firstAngle = -Math.PI / 2; // Start at top (first category)
    
    // Ensure first value is valid
    let firstValue = scores[firstCategory.key];
    if (firstValue === null || firstValue === undefined || isNaN(firstValue)) {
      firstValue = 0;
    }
    firstValue = Math.max(0, Math.min(5, firstValue)); // Clamp between 0 and 5
    
    const firstValueRadius = (radius / 5) * firstValue;
    
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
    
    // Draw data points
    validCategories.forEach((category, i) => {
      const angle = i * angleStep - Math.PI / 2;
      
      // Ensure score is a valid number between 0 and 5
      let value = scores[category.key];
      if (value === null || value === undefined || isNaN(value)) {
        value = 0;
      }
      value = Math.max(0, Math.min(5, value)); // Clamp between 0 and 5
      
      const valueRadius = (radius / 5) * value;
      
      const x = centerX + valueRadius * Math.cos(angle);
      const y = centerY + valueRadius * Math.sin(angle);
      
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
      
      // Position the text with a slight offset from the point
      const textX = centerX + (valueRadius + 15) * Math.cos(angle);
      const textY = centerY + (valueRadius + 15) * Math.sin(angle);
      
      // Display the value with fixed precision
      ctx.fillText(value.toFixed(1), textX, textY);
    });
    
  }, [scores, canvasRef]);
  
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