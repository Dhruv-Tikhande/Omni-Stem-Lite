import React, { createContext, useContext, useState, useCallback } from 'react';

const AccessibilityContext = createContext();

export const AccessibilityProvider = ({ children }) => {
  const [announcement, setAnnouncement] = useState('');

  const announce = useCallback((message) => {
    // If the message is the same, we need to temporarily clear it so the screen reader
    // registers it as a new update and re-reads it.
    setAnnouncement('');
    setTimeout(() => {
      setAnnouncement(message);
    }, 50);
  }, []);

  return (
    <AccessibilityContext.Provider value={{ announce }}>
      {children}
      {/* Visually hidden assertive live region for screen readers */}
      <div 
        className="sr-only" 
        aria-live="assertive" 
        aria-atomic="true"
        style={{ position: 'absolute', width: '1px', height: '1px', padding: '0', margin: '-1px', overflow: 'hidden', clip: 'rect(0, 0, 0, 0)', whiteSpace: 'nowrap', borderWidth: '0' }}
      >
        {announcement}
      </div>
    </AccessibilityContext.Provider>
  );
};

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
};
