import { useState, useEffect } from 'react';

const CompanyLogo = ({ ticker, name }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  
  // Extract domain from company name (simplified)
  const getDomainFromName = (companyName) => {
    // Remove common suffixes and punctuation
    const simplifiedName = companyName
      .replace(/\b(Inc|Corp|Co|Ltd|LLC|Group|Holdings|Incorporated|Corporation|Company|Limited)\b\.?,?/gi, '')
      .replace(/\([^)]*\)/g, '') // Remove anything in parentheses
      .trim()
      .split(' ')[0] // Take first word
      .toLowerCase()
      .replace(/[^a-z0-9]/g, ''); // Remove non-alphanumeric
      
    return `${simplifiedName}.com`;
  };
  
  const getLogoUrl = () => {
    // Try to get domain from name as fallback
    const domain = getDomainFromName(name);
    
    // Use logo.dev with your public key
    return `https://img.logo.dev/${domain}?token=pk_JwL3WsZdS7metT_Z7bQGQw&size=80&format=png`;
  };
  
  // Create a consistent color from ticker symbol for the fallback
  const getColorFromTicker = (ticker) => {
    let hash = 0;
    for (let i = 0; i < ticker.length; i++) {
      hash = ticker.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    const colors = [
      'from-blue-500 to-blue-700',
      'from-green-500 to-green-700',
      'from-purple-500 to-purple-700',
      'from-red-500 to-red-700',
      'from-yellow-500 to-amber-700',
      'from-indigo-500 to-indigo-700',
      'from-pink-500 to-pink-700',
      'from-teal-500 to-teal-700'
    ];
    
    return colors[Math.abs(hash) % colors.length];
  };
  
  // Handle image load complete
  const handleImageLoaded = () => {
    setIsLoading(false);
  };
  
  // Handle image load error
  const handleImageError = () => {
    setHasError(true);
    setIsLoading(false);
  };
  
  if (hasError || !ticker) {
    const colorClass = getColorFromTicker(ticker || 'XX');
    return (
      <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-bold bg-gradient-to-br ${colorClass}`}>
        {ticker ? ticker.substring(0, 2) : 'XX'}
      </div>
    );
  }
  
  return (
    <div className="w-12 h-12 relative">
      {isLoading && (
        <div className="absolute inset-0 rounded-full bg-gray-700 animate-pulse"></div>
      )}
      <img
        src={getLogoUrl()}
        alt={`${name} logo`}
        className="w-12 h-12 rounded-full object-contain bg-white"
        onLoad={handleImageLoaded}
        onError={handleImageError}
        style={{ display: isLoading ? 'none' : 'block' }}
      />
    </div>
  );
};

export default CompanyLogo;