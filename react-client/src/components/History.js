import React, { useEffect, useState, useContext } from "react";
import { AuthContext } from "../contexts/AuthContext";
import { contractAPI, feedbackAPI } from "../services/api";
import { getUserFromToken, downloadBlob, handleApiError } from "../utils/utils";

function History() {
  const { token } = useContext(AuthContext);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

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

  const handleFeedback = (reportId, status) => {
    if (submitting) return;

    setSubmitting(true);
    setError(""); // Clear any previous errors

    const feedbackData = {
      report_id: reportId,
      status: status // "OK" or "KO"
    };

    feedbackAPI.submitFeedback(feedbackData)
      .then(res => {
        // Update the history item with the new feedback
        setHistory(prevHistory => 
          prevHistory.map(item => 
            item.id === reportId 
              ? { 
                  ...item, 
                  feedback: { 
                    status: status, 
                    code_result: status === "OK" ? 1 : 0,
                    comment: null 
                  } 
                } 
              : item
          )
        );
      })
      .catch(error => {
        const errorMessage = handleApiError(error);

        // Check if the error is due to already submitted feedback
        if (errorMessage.includes("déjà donné votre avis") || errorMessage.includes("already submitted")) {
          // Refresh the history to get the latest feedback data
          contractAPI.getHistory()
            .then(res => {
              if (res.data && res.data.data) {
                setHistory(res.data.data);
              }
            })
            .catch(err => {
              setError(`Erreur lors du rafraîchissement de l'historique: ${handleApiError(err)}`);
            });
        } else {
          setError(`Erreur lors de l'envoi du feedback: ${errorMessage}`);
        }
      })
      .finally(() => {
        setSubmitting(false);
      });
  };

  return (
    <div className="container mt-5">
      <h2>📚 Historique des analyses</h2>

      {error && <div className="alert alert-danger">{error}</div>}
      {history.length === 0 && <p>📭 Aucun rapport pour l’instant.</p>}

      <ul className="list-group mt-3">
        {history.map((item, index) => (
          <li key={index} className="list-group-item">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <span>
                {item.date} — <strong>{item.filename}</strong> — {item.status}
              </span>
              <button
                className="btn btn-outline-primary"
                onClick={() => handleDownload(item.filename)}
              >
                📥 Télécharger
              </button>
            </div>

            {/* Feedback section */}
            <div className="mt-2">
              {item.feedback ? (
                <div className="alert alert-info">
                  <strong>
                    {item.feedback.status === "OK" ? "👍 OK" : "👎 KO"}
                  </strong>
                  {item.feedback.comment && (
                    <span> — {item.feedback.comment}</span>
                  )}
                  <div className="mt-1">✅ Feedback déjà envoyé</div>
                </div>
              ) : (
                <div className="d-flex gap-2">
                  <button
                    className="btn btn-sm btn-success"
                    onClick={() => handleFeedback(item.id, "OK")}
                    disabled={submitting}
                  >
                    👍 Correct
                  </button>
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => handleFeedback(item.id, "KO")}
                    disabled={submitting}
                  >
                    👎 Incorrect
                  </button>
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default History;
