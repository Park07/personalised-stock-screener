// src/component/CompanyLogo.jsx
import { useState } from 'react';

const CompanyLogo = ({ ticker, name, website }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError]   = useState(false);

  // Normalize a display name
  const rawName = name || ticker;

  // 1) If backend gave us a real site, use that...
  //    otherwise fall back to our old "guess from name" logic.
  const logoSrc = website
    ? `https://logo.clearbit.com/${new URL(website).hostname}` 
    : (() => {
        // strip common suffixes, punctuation, etc.
        const simplified = rawName
          .replace(/\b(Inc|Corp|Co|Ltd|LLC|Group|Holdings|Incorporated|Corporation|Company|Limited)\b\.?,?/gi, '')
          .replace(/\([^)]*\)/g, '')
          .trim()
          .split(' ')[0]
          .toLowerCase()
          .replace(/[^a-z0-9]/g, '');
        return `https://img.logo.dev/${simplified}.com?token=pk_JwL3WsZdS7metT_Z7bQGQw&size=80&format=png`;
      })();

  // 2) Fallback gradient–initials
  const getGradient = (t) => {
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

  const handleLoad  = () => setIsLoading(false);
  const handleError = () => {
    setHasError(true);
    setIsLoading(false);
  };

  // If loading & no error yet, show a pulse
  // If error, show gradient + initials
  if (hasError) {
    return (
      <div
        className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-bold bg-gradient-to-br ${getGradient(ticker)}`}
      >
        {ticker.slice(0, 2)}
      </div>
    );
  }

  return (
    <div className="w-12 h-12 relative">
      {isLoading && (
        <div className="absolute inset-0 rounded-full bg-gray-700 animate-pulse" />
      )}
      <img
        src={logoSrc}
        alt={`${rawName} logo`}
        className="w-12 h-12 rounded-full object-contain bg-white"
        onLoad={handleLoad}
        onError={handleError}
        style={{ display: isLoading ? 'none' : 'block' }}
      />
    </div>
  );
};

export default CompanyLogo;
