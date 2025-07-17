import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, AuthContext } from "./contexts/AuthContext";
import Login from "./components/Login";
import Register from "./components/Register";
import Analyze from "./components/Analyze";
import EtherscanAnalyze from "./components/EtherscanAnalyze";
import Navbar from "./components/Navbar";
import History from "./components/History";
import Subscription from "./components/Subscription";
import Finetune from "./components/Finetune";
import BlockchainBackground from "./components/BlockchainBackground";

function ProtectedRoute({ children }) {
  const { token } = React.useContext(AuthContext);
  return token ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <BlockchainBackground /> {/* Animated blockchain background */}
        <Navbar /> {/* ⬅️ Affiché en haut */}
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/analyze" element={<ProtectedRoute><Analyze /></ProtectedRoute> } />
          <Route path="/analyse-etherscan" element={<ProtectedRoute><EtherscanAnalyze /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
          <Route path="/subscription" element={<ProtectedRoute><Subscription /></ProtectedRoute>} />
          <Route path="/finetune" element={<ProtectedRoute><Finetune /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
