import React, { useEffect, useRef } from 'react';

const SpiderChart = ({ scores }) => {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    if (!canvasRef.current || !scores) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Set canvas to be responsive
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) * 0.8;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Score categories and values
    const categories = [
      { key: 'overall_score', label: 'Overall' },
      { key: 'valuation_score', label: 'Valuation' },
      { key: 'growth_score', label: 'Growth' },
      { key: 'health_score', label: 'Health' }
    ];
    
    const validCategories = categories.filter(cat => 
      scores[cat.key] !== null && scores[cat.key] !== undefined
    );
    
    if (validCategories.length === 0) return;
    
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
      const valueRadius = (radius / 5) * Math.min(value, 5);
      
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
    const firstValue = scores[firstCategory.key] || 0;
    const firstValueRadius = (radius / 5) * Math.min(firstValue, 5);
    
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
      const value = scores[category.key] || 0;
      const valueRadius = (radius / 5) * Math.min(value, 5);
      
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
      const textX = centerX + (valueRadius + 15) * Math.cos(angle);
      const textY = centerY + (valueRadius + 15) * Math.sin(angle);
      ctx.fillText(value.toFixed(1), textX, textY);
    });
    
  }, [scores, canvasRef]);
  
  return (
    <div className="w-full h-full flex items-center justify-center">
      <canvas ref={canvasRef} className="w-full h-full"></canvas>
    </div>
  );
};

export default SpiderChart;
