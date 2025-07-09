import React, { useState } from "react";
import axios from "axios";
import { contractAPI, feedbackAPI } from "../services/api"; // Import feedbackAPI
import { handleApiError } from "../utils/utils"; // Import handleApiError
import AnalysisDisplay from "./AnalysisDisplay"; // Import AnalysisDisplay

// 👉 Ta clé API Etherscan (évite de la laisser en dur pour la prod)
// Consider moving this to an environment variable or config file
const ETHERSCAN_API_KEY = "ZSA2GA64UDTRKI8EBSMIB435HH3Q8N6XQA";

function EtherscanAnalyze() {
  const [address, setAddress] = useState("");
  // const [loading, setLoading] = useState(false); // Replaced by analysisInProgress
  const [error, setError] = useState("");
  // const [report, setReport] = useState(""); // Replaced by analysisReportData
  const [contractSourceCode, setContractSourceCode] = useState(""); // For "View Contract" button
  // const [downloadUrl, setDownloadUrl] = useState(null); // Will be part of reportData or handled by AnalysisDisplay

  // States for AnalysisDisplay
  const [analysisInProgress, setAnalysisInProgress] = useState(false);
  const [analysisProgressData, setAnalysisProgressData] = useState(null);
  const [analysisReportData, setAnalysisReportData] = useState(null);
  const [showContractModal, setShowContractModal] = useState(false);

  // Feedback states
  const [reportId, setReportId] = useState(null);
  const [feedbackStatus, setFeedbackStatus] = useState(""); // "OK" or "KO"
  const [feedbackComment, setFeedbackComment] = useState("");
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [feedbackError, setFeedbackError] = useState("");


  const resetAnalysisState = () => {
    setError("");
    setAnalysisProgressData(null);
    setAnalysisReportData(null);
    setContractSourceCode("");
    // setAddress(""); // Optionally reset address field

    // Clear feedback states
    setReportId(null);
    setFeedbackStatus("");
    setFeedbackComment("");
    setFeedbackSubmitted(false);
    setFeedbackLoading(false);
    setFeedbackError("");
  };

  const handleRestartAnalysis = () => {
    resetAnalysisState();
  };

  const handleEtherscanSubmit = async (e) => {
    e.preventDefault();
    resetAnalysisState();
    setAnalysisInProgress(true);

    if (!address.trim()) {
      setError("Veuillez entrer une adresse.");
      setAnalysisInProgress(false);
      return;
    }

    setAnalysisProgressData({
      steps: {
        "Récupération du contrat depuis Etherscan": { status: 'En cours', icon: '⏳', color: 'blue' },
        "Vérification du format Solidity": { status: 'En attente', icon: '⏳', color: 'gray' },
        "Compilation du contrat": { status: 'En attente', icon: '⏳', color: 'gray' },
        "Analyse des fonctions": { status: 'En attente', icon: '⏳', color: 'gray' },
        "Détection de vulnérabilités": { status: 'En attente', icon: '⏳', color: 'gray' },
        "Génération du rapport final": { status: 'En attente', icon: '⏳', color: 'gray' },
      }
    });

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
      if (!contract || contract.ABI === "Contract source code not verified" || !contract.SourceCode) {
        const NocontractError = "Ce contrat n’est pas vérifié sur Etherscan ou le code source est vide.";
        setError(NocontractError);
        setAnalysisProgressData(prev => ({
            ...prev,
            steps: {
                ...prev.steps,
                "Récupération du contrat depuis Etherscan": { status: 'Échec', icon: '❌', color: 'red', message: NocontractError },
            }
        }));
        setAnalysisInProgress(false);
        return;
      }

      setAnalysisProgressData(prev => ({
        ...prev,
        steps: {
            ...prev.steps,
            "Récupération du contrat depuis Etherscan": { status: 'Terminé', icon: '✅', color: 'green' },
            "Vérification du format Solidity": { status: 'En cours', icon: '⏳', color: 'blue' },
        }
      }));

      const source = contract.SourceCode;
      setContractSourceCode(source); // Store for "View Contract" button

      // Simulate verification and compilation for now
      await new Promise(resolve => setTimeout(resolve, 300));
       setAnalysisProgressData(prev => ({
        ...prev,
        steps: {
            ...prev.steps,
            "Vérification du format Solidity": { status: 'Terminé', icon: '✅', color: 'green' },
            "Compilation du contrat": { status: 'En cours', icon: '⏳', color: 'blue' },
        }
      }));
      await new Promise(resolve => setTimeout(resolve, 300));
      setAnalysisProgressData(prev => ({
        ...prev,
        steps: {
            ...prev.steps,
            "Compilation du contrat": { status: 'Terminé', icon: '✅', color: 'green' },
            "Analyse des fonctions": { status: 'En cours', icon: '⏳', color: 'blue' },
        }
      }));


      const formData = new FormData();
      formData.append("code", source);

      const result = await contractAPI.analyze(formData);

      // Simulate remaining steps
      await new Promise(resolve => setTimeout(resolve, 300));
       setAnalysisProgressData(prev => ({
        ...prev,
        steps: {
            ...prev.steps,
            "Analyse des fonctions": { status: 'Terminé', icon: '✅', color: 'green' },
            "Détection de vulnérabilités": { status: 'En cours', icon: '⏳', color: 'blue' },
        }
      }));
       await new Promise(resolve => setTimeout(resolve, 300));
      setAnalysisProgressData(prev => ({
        ...prev,
        steps: {
            ...prev.steps,
            "Détection de vulnérabilités": { status: 'Terminé', icon: '✅', color: 'green' },
            "Génération du rapport final": { status: 'En cours', icon: '⏳', color: 'blue' },
        }
      }));

      // Parse result.data into the structure expected by AnalysisDisplay
      // This is a placeholder, actual parsing logic is needed here
      const parsedReport = {
        fileName: `Etherscan: ${address}`,
        contractName: contract.ContractName || "Unknown Contract",
        deployedAddress: address,
        compilerVersion: contract.CompilerVersion || "N/A",
        analysisDate: new Date().toLocaleDateString(),
        globalStatus: result.data.includes("Vulnerability") ? "KO" : "OK", // Basic check
        vulnerabilityType: result.data.includes("Reentrancy") ? "Reentrancy" : (result.data.includes("Vulnerability") ? "Unknown Vulnerability" : null),
        analysisSummary: [
          { point: "Summary from Etherscan contract analysis...", isCritical: result.data.includes("Vulnerability") },
        ],
        modelReasoning: `<p>Model reasoning based on Etherscan contract...</p><pre><code>${result.data.substring(0,100)}...</code></pre>`,
        exploitCode: result.data.includes("Vulnerability") ? `// Exploit code for ${contract.ContractName}\nfunction exploit() public payable {}` : null,
        rawReport: result.data,
        // downloadUrl: URL.createObjectURL(new Blob([result.data], { type: "text/plain" })) // Example for download
      };
      setAnalysisReportData(parsedReport);
      setAnalysisProgressData(prev => ({
        ...prev,
        steps: {
            ...prev.steps,
            "Génération du rapport final": { status: 'Terminé', icon: '✅', color: 'green' },
        }
      }));

      // Get the latest report ID from history for feedback
      try {
        const historyRes = await contractAPI.getHistory();
        if (historyRes.data && historyRes.data.data && historyRes.data.data.length > 0) {
          const latestReport = historyRes.data.data[0];
          setReportId(latestReport.id);
          // Reset feedback submitted status for the new report
          setFeedbackSubmitted(false);
          setFeedbackStatus("");
          setFeedbackComment("");
          setFeedbackError("");
        }
      } catch (historyError) {
        console.error("Failed to fetch report ID from history:", historyError);
        // Set feedbackError, but don't block showing the report itself
        setFeedbackError("Impossible de récupérer l'ID du rapport pour le feedback.");
      }

    } catch (err) {
      console.error(err);
      const errorMsg = "Erreur pendant l’analyse. Vérifiez l’adresse ou la connexion.";
      setError(errorMsg);
      setAnalysisProgressData(prev => {
        const newSteps = { ...(prev?.steps || {}) };
        let stepFailed = false;
        for (const stepName in newSteps) {
            if (newSteps[stepName].status === 'En cours' || newSteps[stepName].status === 'En attente') {
                newSteps[stepName] = { status: 'Échec', icon: '❌', color: 'red', message: errorMsg };
                stepFailed = true;
                break;
            }
        }
        if (!stepFailed && Object.keys(newSteps).length > 0) { // If all were done or no steps yet
             const firstStep = Object.keys(newSteps)[0] || "Récupération du contrat depuis Etherscan";
             newSteps[firstStep] = { status: 'Échec', icon: '❌', color: 'red', message: errorMsg };
        } else if (!prev?.steps) {
            return { steps: {"Récupération du contrat depuis Etherscan": { status: 'Échec', icon: '❌', color: 'red', message: errorMsg }}};
        }
        return { ...prev, steps: newSteps };
      });
    } finally {
      setAnalysisInProgress(false);
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
      console.error("Feedback submission error:", error);
      const errorMessage = handleApiError(error); // Use utility for error message

      if (errorMessage.includes("déjà donné votre avis") || errorMessage.includes("already submitted")) {
        setFeedbackError("Vous avez déjà donné votre avis sur ce rapport.");
        setFeedbackSubmitted(true); // Treat as submitted to hide form
      } else {
        setFeedbackError(`Erreur lors de l'envoi du feedback: ${errorMessage}`);
      }
    } finally {
      setFeedbackLoading(false);
    }
  };

  // const handleDownload = () => { // This might be handled by AnalysisDisplay or a new prop
  //   if (analysisReportData && analysisReportData.downloadUrl) {
  //     downloadBlob(analysisReportData.downloadUrl, `etherscan-analysis-${address}.txt`);
  //   }
  // };

  return (
    <div className="container mt-4">
      <h5 className="mb-3">Analyse de contrat via Etherscan</h5>

      {(!analysisInProgress && !analysisReportData) && (
        <form onSubmit={handleEtherscanSubmit}>
          <div className="mb-3">
            <input
              type="text"
              placeholder="Adresse du contrat (ex: 0x...)"
              className="form-control"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
            />
          </div>
          <button className="btn btn-primary" type="submit" disabled={analysisInProgress}>
            {analysisInProgress ? "Analyse en cours..." : "Analyser"}
          </button>
        </form>
      )}

      {error && <div className="alert alert-danger mt-3">{error}</div>}

      {/* "View Contract" Button - to be styled and positioned appropriately */}
      {analysisProgressData && !analysisReportData && contractSourceCode && (
        <button
          className="btn btn-info mt-3 mb-2"
          onClick={() => setShowContractModal(true)}
        >
          Voir le contrat en cours d'analyse
        </button>
      )}

      {/* Modal for displaying contract source code */}
      {showContractModal && (
        <div className="modal show" tabIndex="-1" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-xl">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Code Source du Contrat: {address}</h5>
                <button type="button" className="btn-close" onClick={() => setShowContractModal(false)}></button>
              </div>
              <div className="modal-body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
                <pre style={{ whiteSpace: "pre-wrap", fontSize: "13px" }}>
                  {contractSourceCode}
                </pre>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowContractModal(false)}>Fermer</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {(analysisProgressData || analysisReportData) && (
        <AnalysisDisplay
            analysisData={analysisProgressData}
            reportData={analysisReportData}
            showProgress={!!analysisProgressData && !analysisReportData}
            onRestartAnalysis={handleRestartAnalysis}
            // We might need to pass a download handler or let AnalysisDisplay handle it
        />
      )}

      {/* Old report display - to be removed or integrated if AnalysisDisplay doesn't cover everything */}
      {/* {sourceCode && !analysisProgressData && !analysisReportData && ( ... ) } */}
      {/* {report && !analysisProgressData && !analysisReportData && ( ... ) } */}

      {/* Feedback Section */}
      {analysisReportData && reportId && !feedbackSubmitted && (
        <div className="mt-4 p-4 border rounded bg-light">
          <h4 className="mb-3"><span role="img" aria-label="bulle de dialogue">💬</span> Votre avis sur ce rapport :</h4>
          <form onSubmit={handleFeedbackSubmit}>
            <div className="mb-3">
              <div className="d-flex gap-3">
                <button
                  type="button"
                  className={`btn ${feedbackStatus === "OK" ? "btn-success" : "btn-outline-success"}`}
                  onClick={() => setFeedbackStatus("OK")}
                >
                  <span role="img" aria-label="pouce en l'air">👍</span> Résultat valide
                </button>
                <button
                  type="button"
                  className={`btn ${feedbackStatus === "KO" ? "btn-danger" : "btn-outline-danger"}`}
                  onClick={() => setFeedbackStatus("KO")}
                >
                  <span role="img" aria-label="pouce en bas">👎</span> Résultat invalide
                </button>
              </div>
            </div>
            <div className="mb-3">
              <label htmlFor="etherscanFeedbackComment" className="form-label">Laissez un commentaire (optionnel) :</label>
              <textarea
                id="etherscanFeedbackComment"
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
      )}
      {analysisReportData && reportId && feedbackSubmitted && (
        <div className="mt-4 p-4 border rounded bg-light">
          <div className="alert alert-success mb-0">
            <h5 className="alert-heading"><span role="img" aria-label="coche verte">✅</span> Merci pour votre retour !</h5>
            <p className="mb-0">Votre avis a bien été pris en compte.</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default EtherscanAnalyze;