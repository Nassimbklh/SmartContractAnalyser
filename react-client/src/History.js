import React, { useEffect, useState, useContext } from "react";
import { AuthContext } from "./AuthContext";

// Décodage minimal du JWT pour obtenir le wallet
function getWalletFromToken(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.wallet;
  } catch {
    return null;
  }
}

function History() {
  const { token } = useContext(AuthContext);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");

  const wallet = getWalletFromToken(token);

  useEffect(() => {
    fetch("http://localhost:8000/history", {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
      .then(res => res.json())
      .then(data => setHistory(data))
      .catch(() => setError("Erreur lors du chargement de l'historique"));
  }, [token]);

  const handleDownload = (filename) => {
    fetch(`http://localhost:8000/report/${wallet}/${filename}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
      .then(res => {
        if (!res.ok) throw new Error("Erreur lors du téléchargement");
        return res.blob();
      })
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${filename}.md`;
        a.click();
        window.URL.revokeObjectURL(url);
      })
      .catch(err => console.error(err));
  };

  return (
    <div className="container mt-5">
      <h2>📚 Historique des analyses</h2>

      {error && <div className="alert alert-danger">{error}</div>}
      {history.length === 0 && <p>📭 Aucun rapport pour l’instant.</p>}

      <ul className="list-group mt-3">
        {history.map((item, index) => (
          <li key={index} className="list-group-item d-flex justify-content-between align-items-center">
            <span>
              {item.date} — <strong>{item.filename}</strong> — {' '}
              {item.status === "OK" ? (
                <span className="text-success">✅ OK</span>
              ) : item.status === "KO" ? (
                <span className="text-danger">❌ KO</span>
              ) : (
                <span className="text-secondary">⚠️ {item.status}</span>
              )}
              {item.attack && <span className="ms-2 text-warning">— {item.attack}</span>}
            </span>
            <button className="btn btn-outline-primary" onClick={() => handleDownload(item.filename)}>
              📥 Télécharger
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default History;
