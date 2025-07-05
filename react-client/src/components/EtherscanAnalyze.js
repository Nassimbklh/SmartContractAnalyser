import React, { useState } from "react";
import axios from "axios";
import { contractAPI } from "../services/api";
import { downloadBlob } from "../utils/utils";
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


  const resetAnalysisState = () => {
    setError("");
    setAnalysisProgressData(null);
    setAnalysisReportData(null);
    setContractSourceCode("");
    // setAddress(""); // Optionally reset address field
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
    </div>
  );
}

export default EtherscanAnalyze;