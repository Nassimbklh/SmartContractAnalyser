import React, { createContext, useState } from "react";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [wallet, setWallet] = useState(localStorage.getItem("wallet"));

  const login = (newToken, walletAddress) => {
    localStorage.setItem("token", newToken);
    setToken(newToken);

    if (walletAddress) {
      localStorage.setItem("wallet", walletAddress);
      setWallet(walletAddress);
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("wallet");
    setToken(null);
    setWallet(null);
  };

  return (
    <AuthContext.Provider value={{ token, wallet, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
