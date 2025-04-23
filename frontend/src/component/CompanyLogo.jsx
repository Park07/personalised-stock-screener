import { useState } from 'react';

const CompanyLogo = ({ ticker, name }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  // If name is undefined, default to ticker
  const rawName = name || ticker;

  const getDomainFromName = (companyName) => {
    // strip suffixes/etc
    const simplified = companyName
      .replace(/\b(Inc|Corp|Co|Ltd|LLC|Group|Holdings|Incorporated|Corporation|Company|Limited)\b\.?,?/gi, '')
      .replace(/\([^)]*\)/g, '')
      .trim()
      .split(' ')[0]
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '');

    return `${simplified}.com`;
  };

  const getLogoUrl = () => {
    // now rawName is always defined
    const domain = getDomainFromName(rawName);
    return `https://img.logo.dev/${domain}?token=pk_JwL3WsZdS7metT_Z7bQGQw&size=80&format=png`;
  };

  // fallback gradient
  const getColorFromTicker = (t) => {
    let hash = 0;
    for (let i = 0; i < t.length; i++) {
      hash = t.charCodeAt(i) + ((hash << 5) - hash);
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

  const handleImageLoaded = () => setIsLoading(false);
  const handleImageError  = () => {
    setHasError(true);
    setIsLoading(false);
  };

  if (hasError) {
    // show ticker fallback
    const gradient = getColorFromTicker(ticker);
    return (
      <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-bold bg-gradient-to-br ${gradient}`}>
        {ticker.slice(0,2)}
      </div>
    );
  }

  return (
    <div className="w-12 h-12 relative">
      {isLoading && <div className="absolute inset-0 rounded-full bg-gray-700 animate-pulse"/>}
      <img
        src={getLogoUrl()}
        alt={`${rawName} logo`}
        className="w-12 h-12 rounded-full object-contain bg-white"
        onLoad={handleImageLoaded}
        onError={handleImageError}
        style={{ display: isLoading ? 'none' : 'block' }}
      />
    </div>
  );
};

export default CompanyLogo;
