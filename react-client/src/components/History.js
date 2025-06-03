import React, { useEffect, useState, useContext } from "react";
import { AuthContext } from "../contexts/AuthContext";
import { contractAPI } from "../services/api";
import { getUserFromToken, downloadBlob, handleApiError } from "../utils/utils";

function History() {
  const { token } = useContext(AuthContext);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;

    contractAPI.getHistory()
      .then(res => {
        if (res.data && res.data.data) {
          setHistory(res.data.data);
        } else {
          setHistory([]);
        }
      })
      .catch(err => {
        setError(`Erreur lors du chargement de l'historique: ${handleApiError(err)}`);
      });
  }, [token]);

  const handleDownload = (filename) => {
    const userData = getUserFromToken(token);
    if (!userData || !userData.wallet) {
      alert("Erreur: Impossible d'extraire les informations utilisateur du token");
      return;
    }

    contractAPI.getReport(userData.wallet, filename)
      .then(res => {
        downloadBlob(res.data, `${filename}.md`);
      })
      .catch(error => {
        alert(`Erreur lors du téléchargement: ${handleApiError(error)}`);
      });
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
