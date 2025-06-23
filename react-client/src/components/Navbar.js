import React, { useContext } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../contexts/AuthContext";
import logo from "../img/logo.png";

function Navbar() {
  const { token, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-light bg-light shadow-sm">
      <div className="container">
        {/* 🔗 Le nom du site redirige vers /analyze */}
        <Link to="/analyze" className="navbar-brand d-flex align-items-center text-decoration-none">
          <img src={logo} alt="Logo" className="me-2" style={{ height: '30px' }} />
          <strong className="text-dark">SmartContractAnalyser</strong>
        </Link>

        {token ? (
          <div className="d-flex">
            <Link to="/history" className="btn btn-outline-secondary">
              Historique
            </Link>
            <button onClick={handleLogout} className="btn btn-outline-danger ms-2">
              Déconnexion
            </button>
          </div>
        ) : (
          <div className="d-flex">
            <Link to="/login" className="btn btn-outline-primary me-2">Connexion</Link>
            <Link to="/register" className="btn btn-outline-success">Inscription</Link>
          </div>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
