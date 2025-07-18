import React, { useContext, useState, useRef, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../contexts/AuthContext";
import logo from "../img/logo.png";

function Navbar() {
  const { token, wallet, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Get initials for avatar
  const getInitials = () => {
    if (!wallet) return "U";
    return wallet.substring(0, 2);
  };

  // Truncate wallet address for display
  const truncateWallet = () => {
    if (!wallet) return "Utilisateur";
    if (wallet.length <= 10) return wallet;
    return `${wallet.substring(0, 6)}...${wallet.substring(wallet.length - 4)}`;
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-light bg-light shadow-sm">
      <div className="container d-flex justify-content-between align-items-center">
        {/* 🔗 Le nom du site redirige vers /analyze */}
        <Link to="/analyze" className="navbar-brand d-flex align-items-center text-decoration-none">
          <img src={logo} alt="Logo" className="me-2" style={{ height: '30px' }} />
          <strong className="text-dark">SmartContractAnalyser</strong>
        </Link>

        {token ? (
          <div className="position-relative" ref={dropdownRef}>
            <button 
              className="btn d-flex align-items-center" 
              onClick={() => setDropdownOpen(!dropdownOpen)}
              aria-expanded={dropdownOpen}
            >
              <div className="d-flex align-items-center">
                <div 
                  className="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center me-2" 
                  style={{ width: '35px', height: '35px', fontSize: '14px' }}
                >
                  {getInitials()}
                </div>
                <span className="d-none d-md-inline">{truncateWallet()}</span>
                <span className="ms-2">{dropdownOpen ? '▲' : '▼'}</span>
              </div>
            </button>

            {dropdownOpen && (
              <div 
                className="position-absolute end-0 mt-2 py-2 bg-white rounded shadow-lg" 
                style={{ 
                  minWidth: '200px', 
                  zIndex: 1000,
                  transition: 'opacity 0.2s ease-in-out, transform 0.2s ease-in-out',
                  opacity: 1,
                  transform: 'translateY(0)'
                }}
              >
                <div className="px-4 py-2 text-muted border-bottom">
                  {wallet}
                </div>
                <Link 
                  to="/history" 
                  className="dropdown-item py-2 px-4 d-flex align-items-center" 
                  onClick={() => setDropdownOpen(false)}
                >
                  <span className="me-2" role="img" aria-label="document">📄</span> Mon historique
                </Link>
                <Link 
                  to="/analyse-etherscan" 
                  className="dropdown-item py-2 px-4 d-flex align-items-center" 
                  onClick={() => setDropdownOpen(false)}
                >
                  <span className="me-2" role="img" aria-label="loupe">🔍</span> Analyse depuis Etherscan
                </Link>
                <Link 
                  to="/subscription" 
                  className="dropdown-item py-2 px-4 d-flex align-items-center" 
                  onClick={() => setDropdownOpen(false)}
                >
                  <span className="me-2" role="img" aria-label="étoile">⭐</span> Abonnements
                </Link>
                <Link 
                  to="/finetune" 
                  className="dropdown-item py-2 px-4 d-flex align-items-center" 
                  onClick={() => setDropdownOpen(false)}
                >
                  <span className="me-2" role="img" aria-label="cible">🎯</span> Finetune
                </Link>
                <Link 
                  to="/evaluation" 
                  className="dropdown-item py-2 px-4 d-flex align-items-center" 
                  onClick={() => setDropdownOpen(false)}
                >
                  <span className="me-2" role="img" aria-label="graphique">📊</span> Évaluation
                </Link>
                <button 
                  className="dropdown-item py-2 px-4 d-flex align-items-center" 
                  onClick={() => {
                    setDropdownOpen(false);
                    alert("La page de profil sera disponible prochainement!");
                  }}
                >
                  <span className="me-2" role="img" aria-label="développeur">🧑‍💻</span> Mon profil
                </button>
                <button 
                  onClick={() => {
                    setDropdownOpen(false);
                    handleLogout();
                  }} 
                  className="dropdown-item py-2 px-4 text-danger d-flex align-items-center"
                >
                  <span className="me-2" role="img" aria-label="porte">🚪</span> Se déconnecter
                </button>
              </div>
            )}
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
