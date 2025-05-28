import React, { useEffect, useState, useContext } from "react";
import { AuthContext } from "./AuthContext";

function History() {
  const { token } = useContext(AuthContext);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");

  const BACKEND_URL = (window.env && window.env.REACT_APP_API_URL) || process.env.REACT_APP_API_URL || "http://localhost:4455";

  useEffect(() => {
    fetch(`${BACKEND_URL}/history`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
      .then(res => res.json())
      .then(data => setHistory(data))
      .catch(err => setError("Erreur lors du chargement de l'historique"));
  }, [token, BACKEND_URL]);

  const handleDownload = (filename) => {
    const wallet = JSON.parse(atob(token.split(".")[1])).wallet; // extrait le wallet du JWT
    fetch(`${BACKEND_URL}/report/${wallet}/${filename}`, {
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
      .catch(() => alert("Erreur lors du téléchargement"));
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
              {item.date} — <strong>{item.filename}</strong> — {item.status}
            </span>
            <button
              className="btn btn-outline-primary"
              onClick={() => handleDownload(item.filename)}
            >
              📥 Télécharger
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default History;
