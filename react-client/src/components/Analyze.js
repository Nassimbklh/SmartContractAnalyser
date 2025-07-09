import React, { useState } from "react";
import { contractAPI, feedbackAPI } from "../services/api";
import { handleApiError } from "../utils/utils";
import AnalysisDisplay from "./AnalysisDisplay"; // Import the new component

function Analyze() {
  const [code, setCode] = useState("");
  const [file, setFile] = useState(null);
  // const [reportContent, setReportContent] = useState(""); // Replaced by analysisReportData
  // const [downloadUrl, setDownloadUrl] = useState(null); // Will be handled within AnalysisDisplay or passed to it
  const [error, setError] = useState("");
  const [reportId, setReportId] = useState(null);
  const [feedbackStatus, setFeedbackStatus] = useState("");
  const [feedbackComment, setFeedbackComment] = useState("");
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [feedbackError, setFeedbackError] = useState("");

  // State for the new AnalysisDisplay component
  const [analysisProgressData, setAnalysisProgressData] = useState(null);
  const [analysisReportData, setAnalysisReportData] = useState(null);
  const [analysisInProgress, setAnalysisInProgress] = useState(false);


  const resetAnalysisState = () => {
    setError("");
    setAnalysisProgressData(null);
    setAnalysisReportData(null);
    setReportId(null);
    setFeedbackStatus("");
    setFeedbackComment("");
    setFeedbackSubmitted(false);
    setFeedbackError("");
    // setFile(null); // Optionally reset file input
    // setCode(""); // Optionally reset code input
  };

  const handleRestartAnalysis = () => {
    resetAnalysisState();
    // Optionally, clear file/code input fields if desired
    // setFile(null);
    // setCode("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    resetAnalysisState();
    setAnalysisInProgress(true); // Start analysis progress

    // Simulate initial progress steps
    setAnalysisProgressData({
      steps: {
        'Vérification du format Solidity': { status: 'En cours', icon: '⏳', color: 'blue' },
        'Compilation du contrat': { status: 'En attente', icon: '⏳', color: 'gray' },
        'Analyse des fonctions': { status: 'En attente', icon: '⏳', color: 'gray' },
        'Détection de vulnérabilités': { status: 'En attente', icon: '⏳', color: 'gray' },
        'Génération du rapport final': { status: 'En attente', icon: '⏳', color: 'gray' },
      }
    });


    if (file && code.trim()) {
      setError("❗️ Choisissez soit un fichier, soit du code, pas les deux");
      setAnalysisInProgress(false);
      setAnalysisProgressData(null); // Clear progress on error
      return;
    }

    if (!file && !code.trim()) {
      setError("❗️ Fournissez un fichier ou du code à analyser");
      setAnalysisInProgress(false);
      setAnalysisProgressData(null); // Clear progress on error
      return;
    }

    const formData = new FormData();
    if (file) formData.append("file", file);
    if (code.trim()) formData.append("code", code);

    try {
      // Simulate progress updates (replace with actual API calls and progress logic)
      await new Promise(resolve => setTimeout(resolve, 500));
      setAnalysisProgressData(prev => ({
        ...prev,
        steps: {
          ...prev.steps,
          'Vérification du format Solidity': { status: 'Terminé', icon: '✅', color: 'green' },
          'Compilation du contrat': { status: 'En cours', icon: '⏳', color: 'blue' },
        }
      }));

      const res = await contractAPI.analyze(formData);

      await new Promise(resolve => setTimeout(resolve, 500));
      setAnalysisProgressData(prev => ({
        ...prev,
        steps: {
          ...prev.steps,
          'Compilation du contrat': { status: 'Terminé', icon: '✅', color: 'green' },
          'Analyse des fonctions': { status: 'En cours', icon: '⏳', color: 'blue' },
        }
      }));

      // Simulate more steps
      await new Promise(resolve => setTimeout(resolve, 500));
       setAnalysisProgressData(prev => ({
        ...prev,
        steps: {
          ...prev.steps,
          'Analyse des fonctions': { status: 'Terminé', icon: '✅', color: 'green' },
          'Détection de vulnérabilités': { status: 'En cours', icon: '⏳', color: 'blue' },
        }
      }));

      await new Promise(resolve => setTimeout(resolve, 500));
      setAnalysisProgressData(prev => ({
        ...prev,
        steps: {
          ...prev.steps,
          'Détection de vulnérabilités': { status: 'Terminé', icon: '✅', color: 'green' },
          'Génération du rapport final': { status: 'En cours', icon: '⏳', color: 'blue' },
        }
      }));


      // This is where you would parse the 'res.data' (report text)
      // and transform it into the structured 'analysisReportData' object.
      // For now, let's use a placeholder.
      const parsedReport = {
        fileName: file ? file.name : "Code Snippet",
        contractName: "MyContract", // Placeholder - extract from report or user input
        deployedAddress: "N/A", // Placeholder
        compilerVersion: "0.8.x", // Placeholder - extract from report
        analysisDate: new Date().toLocaleDateString(),
        globalStatus: res.data.includes("Vulnerability") ? "KO" : "OK", // Basic check
        vulnerabilityType: res.data.includes("Reentrancy") ? "Reentrancy" : (res.data.includes("Vulnerability") ? "Unknown Vulnerability" : null), // Placeholder
        analysisSummary: [ // Placeholder - extract and structure from report
          { point: "Function X seems safe.", isCritical: false },
          { point: "Potential reentrancy in function Y.", isCritical: true },
        ],
        modelReasoning: `<p>The model analyzed the contract structure...</p><pre><code>${res.data.substring(0,100)}...</code></pre>`, // Placeholder
        exploitCode: res.data.includes("Vulnerability") ? `// Exploit code for ${"MyContract"}\nfunction exploit() public payable {}` : null, // Placeholder
        rawReport: res.data // Keep the raw report if needed
      };
      setAnalysisReportData(parsedReport);
      setAnalysisProgressData(prev => ({ // Mark final step as complete
        ...prev,
        steps: {
          ...prev.steps,
          'Génération du rapport final': { status: 'Terminé', icon: '✅', color: 'green' },
        }
      }));


      // Get the latest report ID from history
      try {
        const historyRes = await contractAPI.getHistory();
        if (historyRes.data && historyRes.data.data && historyRes.data.data.length > 0) {
          const latestReport = historyRes.data.data[0];
          setReportId(latestReport.id);
        }
      } catch (historyError) {
        console.error("Failed to fetch report ID from history:", historyError);
        setFeedbackError("Impossible de récupérer l'ID du rapport. Le feedback pourrait ne pas fonctionner correctement.");
      }

    } catch (error) {
      console.error(error);
      let errorMsg = "❌ Une erreur est survenue lors de l'analyse.";
      if (error.response && error.response.data && error.response.data.is_contract === false) {
        errorMsg = error.response.data.message || "❌ Le code fourni ne contient pas de contrat Solidity valide.";
      } else if (error.response && error.response.status === 400) {
         errorMsg = `❌ Le code soumis ne semble pas être un smart contract valide. Veuillez coller un contrat Solidity correct ou importer un fichier .sol.`;
      }
      setError(errorMsg);
      // Update progress to show failure
      setAnalysisProgressData(prev => {
        const newSteps = { ...prev.steps };
        // Find the current or first pending step and mark it as failed
        let failedStepSet = false;
        for (const stepName in newSteps) {
          if (newSteps[stepName].status === 'En cours' || newSteps[stepName].status === 'En attente') {
            newSteps[stepName] = { status: 'Échec', icon: '❌', color: 'red' };
            failedStepSet = true;
            break;
          }
        }
        // If all were done before error, mark last one as failed (though ideally error occurs during a step)
        if (!failedStepSet && Object.keys(newSteps).length > 0) {
            const lastStepName = Object.keys(newSteps)[Object.keys(newSteps).length -1];
            newSteps[lastStepName] = { status: 'Échec', icon: '❌', color: 'red' };
        }
        return { ...prev, steps: newSteps };
      });
    } finally {
      setAnalysisInProgress(false); // Analysis attempt is finished (success or fail)
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
      <h2><span role="img" aria-label="loupe">🔍</span> Analyse de Smart Contract Solidity</h2>

      {/* Hide form if analysis is in progress or report is shown, unless explicitly decided otherwise */}
      {(!analysisInProgress && !analysisReportData) && (
        <form onSubmit={handleSubmit}>
          <label className="form-label mt-3"><span role="img" aria-label="ordinateur">💻</span> Coller le code :</label>
          <textarea
            className="form-control"
            placeholder={`// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\ncontract Example {\n    uint256 public value;\n    function setValue(uint256 _value) public {\n        value = _value;\n    }\n}`}
            rows="10"
            value={code}
            onChange={(e) => {
              setCode(e.target.value);
              if (file) setFile(null); // reset fichier si code saisi
            }}
          ></textarea>

          <div className="text-center my-3">— ou —</div>

          <label className="form-label"><span role="img" aria-label="dossier">📁</span> Fichier .sol :</label>
          <input
            type="file"
            accept=".sol"
            className="form-control"
            onChange={(e) => {
              setFile(e.target.files[0]);
              if (code.trim()) setCode(""); // vide le code si fichier choisi
            }}
          />

          <button type="submit" className="btn btn-primary mt-3" disabled={analysisInProgress}>
            <span role="img" aria-label="fusée">🚀</span> Lancer l'analyse
          </button>
        </form>
      )}

      {/* ❌ Global Error Message */}
      {error && <div className="alert alert-danger mt-3">{error}</div>}

      {/* Display Analysis Progress or Final Report */}
      {(analysisProgressData || analysisReportData) && (
          <AnalysisDisplay
            analysisData={analysisProgressData}
            reportData={analysisReportData}
            // Display progress table if there's progress data AND no final report yet.
            showProgress={!!analysisProgressData && !analysisReportData}
            onRestartAnalysis={handleRestartAnalysis}
          />
      )}

      {/* Feedback section - shown only after a report is generated and not submitted yet */}
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

export default Analyze;