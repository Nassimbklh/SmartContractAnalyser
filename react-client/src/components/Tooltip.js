import React, { useState } from 'react';
import './Tooltip.css';

const Tooltip = ({ text, children }) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="tooltip-container">
      {children}
      <span 
        className="tooltip-icon" 
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onClick={() => setIsVisible(!isVisible)}
      >
        ℹ️
      </span>
      {isVisible && (
        <div className="tooltip-content">
          {text}
        </div>
      )}
    </div>
  );
};

export default Tooltip;