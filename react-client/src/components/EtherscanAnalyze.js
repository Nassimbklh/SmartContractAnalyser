import React, { useState } from "react";
import axios from "axios";
import { contractAPI } from "../services/api";
import { downloadBlob } from "../utils/utils";

// 👉 Ta clé API Etherscan (évite de la laisser en dur pour la prod)
const ETHERSCAN_API_KEY = "ZSA2GA64UDTRKI8EBSMIB435HH3Q8N6XQA";

function EtherscanAnalyze() {
  const [address, setAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState("");
  const [sourceCode, setSourceCode] = useState("");
  const [downloadUrl, setDownloadUrl] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setReport("");
    setSourceCode("");
    setDownloadUrl(null);
    setLoading(true);

    if (!address.trim()) {
      setError("Veuillez entrer une adresse.");
      setLoading(false);
      return;
    }

    try {
      const res = await axios.get(`https://api.etherscan.io/api`, {
        params: {
          module: "contract",
          action: "getsourcecode",
          address,
          apikey: ETHERSCAN_API_KEY
        }
      });

      const contract = res.data.result?.[0];
      if (!contract || contract.ABI === "Contract source code not verified") {
        setError("Ce contrat n’est pas vérifié sur Etherscan.");
        return;
      }

      const source = contract.SourceCode;
      if (!source) {
        setError("Aucun code source trouvé.");
        return;
      }

      setSourceCode(source); // Affiche le code

      const formData = new FormData();
      formData.append("code", source);

      const result = await contractAPI.analyze(formData);
      setReport(result.data);

      const blob = new Blob([result.data], { type: "text/plain" });
      setDownloadUrl(URL.createObjectURL(blob));
    } catch (err) {
      console.error(err);
      setError("Erreur pendant l’analyse. Vérifiez l’adresse.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (downloadUrl) {
      downloadBlob(downloadUrl, `etherscan-analysis-${address}.md`);
    }
  };

  return (
    <div className="container mt-4">
      <h5 className="mb-3">Analyse de contrat via Etherscan</h5>

      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <input
            type="text"
            placeholder="Adresse du contrat (ex: 0x...)"
            className="form-control"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
          />
        </div>
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? "Analyse en cours..." : "Analyser"}
        </button>
      </form>

      {error && <div className="alert alert-danger mt-3">{error}</div>}

      {sourceCode && (
        <div className="card mt-4">
          <div className="card-header">Code source du contrat</div>
          <div className="card-body">
            <pre style={{ whiteSpace: "pre-wrap", fontSize: "13px" }}>
              {sourceCode}
            </pre>
          </div>
        </div>
      )}

      {report && (
        <div className="card mt-4">
          <div className="card-header d-flex justify-content-between align-items-center">
            <span>Résultats de l’analyse</span>
            <button className="btn btn-sm btn-outline-secondary" onClick={handleDownload}>
              Télécharger
            </button>
          </div>
          <div className="card-body">
            <pre style={{ whiteSpace: "pre-wrap" }}>{report}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default EtherscanAnalyze;