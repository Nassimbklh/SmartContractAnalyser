import React from 'react';
import './BlockchainBackground.css';

const BlockchainBackground = () => {
  return (
    <div className="blockchain-background">
      <div className="blockchain-animation">
        {/* Generate multiple blockchain elements */}
        {Array.from({ length: 20 }).map((_, index) => (
          <div 
            key={index} 
            className="blockchain-element"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${5 + Math.random() * 10}s`
            }}
          >
            <div className="block">
              <div className="hash">{generateRandomHash()}</div>
            </div>
          </div>
        ))}
        
        {/* Generate connection lines */}
        {Array.from({ length: 15 }).map((_, index) => (
          <div 
            key={`line-${index}`} 
            className="blockchain-connection"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              width: `${100 + Math.random() * 150}px`,
              transform: `rotate(${Math.random() * 360}deg)`,
              animationDelay: `${Math.random() * 5}s`
            }}
          />
        ))}
      </div>
    </div>
  );
};

// Helper function to generate random hash-like strings
const generateRandomHash = () => {
  const characters = '0123456789abcdef';
  let hash = '0x';
  for (let i = 0; i < 8; i++) {
    hash += characters.charAt(Math.floor(Math.random() * characters.length));
  }
  return hash;
};

export default BlockchainBackground;