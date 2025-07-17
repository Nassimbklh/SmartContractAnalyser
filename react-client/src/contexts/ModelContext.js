import React, { createContext, useState, useContext } from 'react';

// Create the context
export const ModelContext = createContext();

// Create a provider component
export const ModelProvider = ({ children }) => {
  const [modelType, setModelType] = useState('runpod'); // Default to 'runpod' (Qwen)

  // Function to toggle between 'runpod' (Qwen) and 'openai' (GPT)
  const toggleModel = () => {
    setModelType(prevModel => prevModel === 'runpod' ? 'openai' : 'runpod');
  };

  // Create a value object with the state and functions
  const value = {
    modelType,
    setModelType,
    toggleModel,
    isQwen: modelType === 'runpod',
    isGPT: modelType === 'openai'
  };

  // Return the provider with the value
  return (
    <ModelContext.Provider value={value}>
      {children}
    </ModelContext.Provider>
  );
};

// Custom hook for using the model context
export const useModel = () => {
  const context = useContext(ModelContext);
  if (context === undefined) {
    throw new Error('useModel must be used within a ModelProvider');
  }
  return context;
};