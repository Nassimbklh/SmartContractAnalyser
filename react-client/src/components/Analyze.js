import React, { useState, useContext } from "react";
import { AuthContext } from "../contexts/AuthContext";
import { contractAPI, feedbackAPI } from "../services/api";
import { downloadBlob, handleApiError } from "../utils/utils";

function Analyze() {
  const [code, setCode] = useState("");
  const [file, setFile] = useState(null);
  const [reportContent, setReportContent] = useState("");
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [reportId, setReportId] = useState(null);
  const [feedbackStatus, setFeedbackStatus] = useState("");
  const [feedbackComment, setFeedbackComment] = useState("");
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [feedbackError, setFeedbackError] = useState("");
  const { token } = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setReportContent("");
    setDownloadUrl(null);
    setReportId(null);
    setFeedbackStatus("");
    setFeedbackComment("");
    setFeedbackSubmitted(false);
    setFeedbackError("");
    setLoading(true);

    if (file && code.trim()) {
      setError("❗️ Choisissez soit un fichier, soit du code, pas les deux");
      setLoading(false);
      return;
    }

    if (!file && !code.trim()) {
      setError("❗️ Fournissez un fichier ou du code à analyser");
      setLoading(false);
      return;
    }

    const formData = new FormData();
    if (file) formData.append("file", file);
    if (code.trim()) formData.append("code", code);

    try {
      const res = await contractAPI.analyze(formData);

      // res.data is already a string when responseType is 'text'
      const text = res.data;
      setReportContent(text);

      // Get the latest report ID from history
      try {
        const historyRes = await contractAPI.getHistory();
        if (historyRes.data && historyRes.data.data && historyRes.data.data.length > 0) {
          // Use the ID of the most recent report (first in the list)
          const latestReport = historyRes.data.data[0];
          setReportId(latestReport.id);
        }
      } catch (historyError) {
        console.error("Failed to fetch report ID from history:", historyError);
        setFeedbackError("Impossible de récupérer l'ID du rapport. Le feedback pourrait ne pas fonctionner correctement.");
      }

      const blobUrl = window.URL.createObjectURL(new Blob([text], { type: "text/plain" }));
      setDownloadUrl(blobUrl);
    } catch (error) {
      console.error(error);
      setError(`❌ Erreur lors de l'analyse: ${handleApiError(error)}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedbackSubmit = async (e) => {
    e.preventDefault();
    setFeedbackError("");
    setFeedbackLoading(true);

    if (!feedbackStatus) {
      setFeedbackError("Veuillez sélectionner une option (valide ou invalide)");
      setFeedbackLoading(false);
      return;
    }

    if (!reportId) {
      setFeedbackError("Impossible d'envoyer le feedback: ID du rapport manquant");
      setFeedbackLoading(false);
      return;
    }

    try {
      await feedbackAPI.submitFeedback({
        report_id: reportId,
        status: feedbackStatus,
        comment: feedbackComment
      });

      setFeedbackSubmitted(true);
    } catch (error) {
      console.error(error);
      const errorMessage = handleApiError(error);

      // Check if the error is due to already submitted feedback
      if (errorMessage.includes("déjà donné votre avis") || errorMessage.includes("already submitted")) {
        setFeedbackError("Vous avez déjà donné votre avis sur ce rapport.");
        setFeedbackSubmitted(true); // Treat as submitted to disable the form
      } else {
        setFeedbackError(`Erreur lors de l'envoi du feedback: ${errorMessage}`);
      }
    } finally {
      setFeedbackLoading(false);
    }
  };

  return (
    <div className="container mt-5">
      <h2>🔍 Analyse de Smart Contract Solidity</h2>

      <form onSubmit={handleSubmit}>
        <label className="form-label mt-3">💻 Coller le code :</label>
        <textarea
          className="form-control"
          placeholder={`// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\ncontract Example {\n    uint256 public value;\n    function setValue(uint256 _value) public {\n        value = _value;\n    }\n}`}
          rows="10"
          value={code}
          onChange={(e) => {
            setCode(e.target.value);
            setFile(null); // reset fichier si code saisi
          }}
        ></textarea>

        <div className="text-center my-3">— ou —</div>

        <label className="form-label">📁 Fichier .sol :</label>
        <input
          type="file"
          accept=".sol"
          className="form-control"
          onChange={(e) => {
            setFile(e.target.files[0]);
            setCode(""); // vide le code si fichier choisi
          }}
        />

        <button type="submit" className="btn btn-primary mt-3" disabled={loading}>
          🚀 Lancer l'analyse
        </button>
      </form>

      {/* 🌀 Spinner pendant chargement */}
      {loading && (
        <div className="d-flex justify-content-center mt-3">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Chargement...</span>
          </div>
        </div>
      )}

      {/* ❌ Message d’erreur */}
      {error && <div className="alert alert-danger mt-3">{error}</div>}

      {/* ✅ Résultat */}
      {reportContent && (
        <div className="mt-4 mb-4 flex flex-column">
          <h4 className="mb-2">📝 Résultat de l’analyse :</h4>
          <pre className="bg-light p-3 rounded border max-h-96 overflow-auto">
            {reportContent}
          </pre>

          {downloadUrl && (
            <div className="d-flex justify-content-center mt-3">
              <a
                href={downloadUrl}
                download="rapport.txt"
                className="btn btn-success"
              >
                📥 Télécharger le rapport
              </a>
            </div>
          )}

          {/* 🔄 Feedback */}
          {reportId && !feedbackSubmitted ? (
            <div className="mt-4 p-4 border rounded bg-light">
              <h4 className="mb-3">💬 Votre avis sur ce rapport :</h4>

              <form onSubmit={handleFeedbackSubmit}>
                <div className="mb-3">
                  <div className="d-flex gap-3">
                    <button
                      type="button"
                      className={`btn ${feedbackStatus === "OK" ? "btn-success" : "btn-outline-success"}`}
                      onClick={() => setFeedbackStatus("OK")}
                    >
                      👍 Résultat valide
                    </button>
                    <button
                      type="button"
                      className={`btn ${feedbackStatus === "KO" ? "btn-danger" : "btn-outline-danger"}`}
                      onClick={() => setFeedbackStatus("KO")}
                    >
                      👎 Résultat invalide
                    </button>
                  </div>
                </div>

                <div className="mb-3">
                  <label htmlFor="feedbackComment" className="form-label">Laissez un commentaire (optionnel) :</label>
                  <textarea
                    id="feedbackComment"
                    className="form-control"
                    rows="3"
                    value={feedbackComment}
                    onChange={(e) => setFeedbackComment(e.target.value)}
                  ></textarea>
                </div>

                {feedbackError && (
                  <div className="alert alert-danger">{feedbackError}</div>
                )}

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={feedbackLoading}
                >
                  {feedbackLoading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Envoi en cours...
                    </>
                  ) : (
                    "Envoyer mon avis"
                  )}
                </button>
              </form>
            </div>
          ) : reportId && feedbackSubmitted ? (
            <div className="mt-4 p-4 border rounded bg-light">
              <div className="alert alert-success mb-0">
                <h5 className="alert-heading">✅ Merci pour votre retour !</h5>
                <p className="mb-0">Votre avis a bien été pris en compte.</p>
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

export default Analyze;
