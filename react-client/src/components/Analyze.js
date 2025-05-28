import React, { useState, useContext } from "react";
import { AuthContext } from "../contexts/AuthContext";
import { contractAPI } from "../services/api";
import { downloadBlob, handleApiError } from "../utils/utils";

function Analyze() {
  const [code, setCode] = useState("");
  const [file, setFile] = useState(null);
  const [reportContent, setReportContent] = useState("");
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { token } = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setReportContent("");
    setDownloadUrl(null);
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

      const text = await res.data.text();
      setReportContent(text);

      const blobUrl = window.URL.createObjectURL(new Blob([text], { type: "text/plain" }));
      setDownloadUrl(blobUrl);
    } catch (error) {
      console.error(error);
      setError(`❌ Erreur lors de l'analyse: ${handleApiError(error)}`);
    } finally {
      setLoading(false);
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
        <div className="mt-4">
          <h4 className="mb-2">📝 Résultat de l’analyse :</h4>
          <pre className="bg-light p-3 rounded border max-h-96 overflow-auto">
            {reportContent}
          </pre>

          {downloadUrl && (
            <a
              href={downloadUrl}
              download="rapport.txt"
              className="btn btn-success mt-3"
            >
              📥 Télécharger le rapport
            </a>
          )}
        </div>
      )}
    </div>
  );
}

export default Analyze;
