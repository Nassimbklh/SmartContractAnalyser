import React, { useState, useEffect, useRef } from 'react';
import { contractAPI } from '../services/api';
import './AnalysisProgress.css'; // Import CSS for animations

const AnalysisProgress = ({ reportId, onComplete, reportData, downloadUrl, file }) => {
  // Reference for scrolling to results
  const resultRef = useRef(null);

  // Reference to track previous reportId for state reset
  const prevReportIdRef = useRef(null);
  const [steps, setSteps] = useState([
    { 
      title: "Vérification du format Solidity", 
      key: "format_check",
      description: "Vérification de la syntaxe et de la structure du code Solidity",
      technicalDetails: "Analyse lexicale et syntaxique du code source pour vérifier sa conformité avec les standards Solidity.",
      reasoning: "Cette étape est cruciale pour s'assurer que le code peut être correctement interprété par le compilateur Solidity.",
      recommendation: "Assurez-vous que votre code respecte la syntaxe Solidity et inclut les directives de pragma appropriées."
    },
    { 
      title: "Compilation du contrat", 
      key: "compilation",
      description: "Compilation du code source en bytecode pour la blockchain Ethereum",
      technicalDetails: "Transformation du code Solidity en bytecode EVM (Ethereum Virtual Machine) et génération de l'ABI (Application Binary Interface).",
      reasoning: "La compilation vérifie que le code est syntaxiquement correct et peut être exécuté sur la blockchain Ethereum.",
      recommendation: "Utilisez une version stable du compilateur Solidity et résolvez toutes les erreurs de compilation avant le déploiement."
    },
    { 
      title: "Analyse des fonctions", 
      key: "function_analysis",
      description: "Analyse des fonctions et des variables du contrat pour identifier les points d'entrée",
      technicalDetails: "Examen des fonctions publiques, des modificateurs d'accès et des variables d'état pour comprendre le comportement du contrat.",
      reasoning: "Cette analyse permet d'identifier les points d'entrée potentiels pour les attaques et de comprendre le flux de contrôle du contrat.",
      recommendation: "Limitez l'accès aux fonctions critiques et utilisez des modificateurs appropriés pour contrôler qui peut appeler chaque fonction."
    },
    { 
      title: "Détection de vulnérabilités connues", 
      key: "vulnerability_scan",
      description: "Recherche de vulnérabilités connues comme les débordements, les réentrances, etc.",
      technicalDetails: "Analyse statique et dynamique du code pour détecter des modèles connus de vulnérabilités comme les réentrances, les débordements arithmétiques, et les problèmes de contrôle d'accès.",
      reasoning: "Les vulnérabilités connues sont souvent exploitées par les attaquants pour compromettre les contrats intelligents.",
      recommendation: "Utilisez des bibliothèques sécurisées comme OpenZeppelin, suivez les meilleures pratiques de sécurité, et effectuez des audits réguliers.",
      owasp: "SWC-107 (Reentrancy), SWC-101 (Integer Overflow and Underflow), SWC-115 (Authorization through tx.origin)"
    },
    { 
      title: "Génération du rapport final", 
      key: "report_generation",
      description: "Création d'un rapport détaillé avec les résultats de l'analyse",
      technicalDetails: "Compilation des résultats de toutes les étapes précédentes dans un rapport structuré avec des recommandations.",
      reasoning: "Le rapport final fournit une vue d'ensemble de la sécurité du contrat et des actions recommandées.",
      recommendation: "Examinez attentivement le rapport et corrigez tous les problèmes identifiés avant de déployer le contrat en production."
    },
  ]);

  const [status, setStatus] = useState({
    format_check: 'in_progress',
    compilation: 'pending',
    function_analysis: 'pending',
    vulnerability_scan: 'pending',
    report_generation: 'pending'
  });
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState('');
  const [expandedSteps, setExpandedSteps] = useState({});
  const [vulnerabilities, setVulnerabilities] = useState({});
  const [showProgressBar, setShowProgressBar] = useState(true);
  const [analysisDone, setAnalysisDone] = useState(false);

  // Toggle expanded state for a step
  const toggleStepDetails = (stepKey) => {
    setExpandedSteps(prev => ({
      ...prev,
      [stepKey]: !prev[stepKey]
    }));
  };

  // Calculate progress percentage based on status
  const calculateProgress = () => {
    const totalSteps = steps.length;
    let completedSteps = 0;

    steps.forEach(step => {
      if (status[step.key] === 'completed') {
        completedSteps += 1;
      } else if (status[step.key] === 'in_progress') {
        completedSteps += 0.5; // Count in-progress steps as half complete
      }
    });

    return Math.round((completedSteps / totalSteps) * 100);
  };

  // Function to get status icon based on status value
  const getStatusIcon = (statusValue) => {
    // Normalize status value (backend uses underscores, frontend might use camelCase)
    const status = statusValue.replace('_', '');

    switch (status) {
      case 'pending':
        return <span className="status-icon">⏳</span>;
      case 'inprogress':
      case 'in_progress':
        return <span className="status-icon spinning-icon">⏳</span>;
      case 'completed':
        return <span className="status-icon">✅</span>;
      case 'failed':
        return <span className="status-icon">❌</span>;
      default:
        return <span className="status-icon">⏳</span>;
    }
  };

  // Function to get status text based on status value
  const getStatusText = (statusValue) => {
    // Normalize status value (backend uses underscores, frontend might use camelCase)
    const status = statusValue.replace('_', '');

    switch (status) {
      case 'pending':
        return 'En attente';
      case 'inprogress':
      case 'in_progress':
        return 'En cours';
      case 'completed':
        return 'Terminé';
      case 'failed':
        return 'Échec';
      default:
        return 'En attente';
    }
  };

  // Track if we've received a response from the backend
  const [receivedBackendStatus, setReceivedBackendStatus] = useState(false);

  // Get step duration based on step key (for more realistic simulation)
  const getStepDuration = (stepKey) => {
    // Different steps take different amounts of time
    const durations = {
      format_check: 1000,    // Format check is quick
      compilation: 3000,     // Compilation takes longer
      function_analysis: 2500, // Function analysis is medium
      vulnerability_scan: 4000, // Vulnerability scan is the longest
      report_generation: 2000  // Report generation is medium
    };
    return durations[stepKey] || 2000; // Default to 2 seconds
  };

  // Simulate progress when no reportId is available or when backend status hasn't been received yet
  useEffect(() => {
    console.log('Simulation useEffect triggered', { reportId, receivedBackendStatus, currentStep });

    // Only run simulation if no reportId or if we haven't received backend status yet
    if (!reportId || !receivedBackendStatus) {
      console.log('Starting/continuing simulation');

      // If all steps are completed, call onComplete
      if (currentStep >= steps.length) {
        console.log('All simulation steps completed, calling onComplete');
        if (onComplete) {
          onComplete();
        }
        return;
      }

      // Update current step status to in_progress
      const currentKey = steps[currentStep].key;
      console.log('Setting step to in_progress:', currentKey);
      setStatus(prevStatus => {
        const newStatus = {
          ...prevStatus,
          [currentKey]: 'in_progress'
        };
        console.log('New status after setting in_progress:', newStatus);
        return newStatus;
      });

      // Get duration for current step
      const stepDuration = getStepDuration(currentKey);
      console.log(`Step ${currentKey} will take ${stepDuration}ms to complete`);

      // Set a timeout to complete the current step and move to the next one
      const timeout = setTimeout(() => {
        // Only update if we haven't received backend status yet
        if (!receivedBackendStatus) {
          console.log('Completing step and moving to next:', currentKey);
          setStatus(prevStatus => {
            const newStatus = {
              ...prevStatus,
              [currentKey]: 'completed'
            };
            console.log('New status after completing step:', newStatus);
            return newStatus;
          });
          setCurrentStep(prevStep => prevStep + 1);
        } else {
          console.log('Received backend status, not updating simulation');
        }
      }, stepDuration);

      return () => {
        console.log('Clearing simulation timeout');
        clearTimeout(timeout);
      };
    } else {
      console.log('Not running simulation because reportId is available and backend status has been received');
    }
  }, [currentStep, steps, onComplete, reportId, receivedBackendStatus]);

  // If reportId is available, try to fetch real status
  useEffect(() => {
    console.log('Backend status useEffect triggered', { reportId });

    if (reportId) {
      console.log('ReportId is available, setting up status polling');

      const fetchStatus = async () => {
        try {
          console.log('Fetching status for report ID:', reportId);
          const response = await contractAPI.getAnalysisStatus(reportId);
          console.log('Status response:', response.data);

          if (response.data && response.data.status === 'success') {
            // Marquer que nous avons reçu un statut backend
            setReceivedBackendStatus(true);

            // Mapper les clés
            const statusMap = {
              format_check: 'format_check',
              compilation: 'compilation',
              function_analysis: 'function_analysis',
              vulnerability_scan: 'vulnerability_scan',
              report_generation: 'report_generation'
            };

            const newStatus = {};
            Object.keys(statusMap).forEach(key => {
              const backendStatus = response.data.data[statusMap[key]];
              newStatus[key] = backendStatus;
            });

            setStatus(newStatus);

            // 💥 Nouvelle logique : on vérifie si TOUT est completed ou failed
            const allStepsCompleted = Object.values(newStatus).every(s => s === 'completed' || s === 'failed');

            if (allStepsCompleted) {
              console.log('All steps completed, setting analysisDone to true');
              setAnalysisDone(true);
              setShowProgressBar(false);

              if (onComplete) {
                onComplete();
              }

              // ✅ Important : retourner true pour signaler d’arrêter le polling
              return true;
            }

            return false; // continuer le polling
          }

          return false; // continuer si pas de succès
        } catch (error) {
          console.error('Error fetching analysis status:', error);
          setShowProgressBar(true);
          setError('❌ Pas de réponse du serveur. Vérifiez votre connexion.');
          return false; // continuer à poller en cas d’erreur
        }
      };

      // Initial fetch
      try {
        fetchStatus();
      } catch (error) {
        console.error('Error during initial fetch:', error);
        // Log the error but don't hide the progress table
        setShowProgressBar(true);

        // Display a message to the user
        setError('❌ Pas de réponse du serveur. Vérifiez votre connexion.');
      }

      // Set up polling interval
      const interval = setInterval(async () => {
        try {
          // If fetchStatus returns true, all steps are completed, so clear the interval
          const completed = await fetchStatus();
          console.log('Polling completed:', completed);
          if (completed) {
            console.log('Clearing polling interval');
            clearInterval(interval);
          }
        } catch (error) {
          console.error('Error during polling:', error);
          // Log the error but don't hide the progress table
          // This ensures the table remains visible even if there's an error during polling
          setShowProgressBar(true);

          // Display a message to the user
          setError('❌ Pas de réponse du serveur. Vérifiez votre connexion.');
        }
      }, 2000);

      return () => {
        console.log('Clearing backend status polling interval');
        clearInterval(interval);
      };
    } else {
      console.log('ReportId is not available, not setting up status polling');
    }
  }, [reportId, onComplete, steps]);

  // Process report data to extract vulnerabilities and update steps with dynamic data
  useEffect(() => {
    if (reportData) {
      try {
        // Extract vulnerabilities for each step
        const vulnMap = {
          format_check: [],
          compilation: [],
          function_analysis: [],
          vulnerability_scan: [],
          report_generation: []
        };

        // Check if there's an attack mentioned in the report
        if (reportData.attack) {
          vulnMap.vulnerability_scan.push(reportData.attack);
        }

        // Set the vulnerabilities state
        setVulnerabilities(vulnMap);

        // Update steps with dynamic data from the report
        setSteps(prevSteps => {
          // Create a copy of the steps array
          const updatedSteps = [...prevSteps];

          // Update format_check step with Solidity version if available
          if (reportData.solc_version) {
            const formatCheckStep = updatedSteps.find(step => step.key === 'format_check');
            if (formatCheckStep) {
              formatCheckStep.technicalDetails = `Analyse lexicale et syntaxique du code source pour vérifier sa conformité avec les standards Solidity. Version détectée: ${reportData.solc_version}`;
            }
          }

          // Update function_analysis step with contract name if available
          if (reportData.contract_name) {
            const functionAnalysisStep = updatedSteps.find(step => step.key === 'function_analysis');
            if (functionAnalysisStep) {
              functionAnalysisStep.technicalDetails = `Examen des fonctions publiques, des modificateurs d'accès et des variables d'état pour comprendre le comportement du contrat "${reportData.contract_name}".`;
            }
          }

          // Update vulnerability_scan step with attack details if available
          if (reportData.attack) {
            const vulnerabilityScanStep = updatedSteps.find(step => step.key === 'vulnerability_scan');
            if (vulnerabilityScanStep) {
              vulnerabilityScanStep.technicalDetails = `Analyse statique et dynamique du code pour détecter des vulnérabilités. Vulnérabilité détectée: ${reportData.attack}`;
              vulnerabilityScanStep.reasoning = reportData.reasoning || vulnerabilityScanStep.reasoning;
            }
          }

          // Update report_generation step with summary if available
          if (reportData.summary) {
            const reportGenerationStep = updatedSteps.find(step => step.key === 'report_generation');
            if (reportGenerationStep) {
              reportGenerationStep.technicalDetails = `Compilation des résultats de l'analyse dans un rapport structuré. ${reportData.summary}`;
            }
          }

          return updatedSteps;
        });
      } catch (error) {
        console.error('Error processing report data:', error);
      }
    }
  }, [reportData]);

  // Calculate the current progress
  const progressPercentage = calculateProgress();

  // Determine if there are any failed steps
  const hasFailedSteps = Object.values(status).some(s => s === 'failed');

  // Determine if there are any vulnerabilities
  const hasVulnerabilities = Object.values(vulnerabilities).some(v => v.length > 0);

  // Effect to reset state when reportId changes
  useEffect(() => {
    // If reportId is different from previous reportId, reset state
    if (reportId !== prevReportIdRef.current && reportId !== null) {
      console.log('ReportId changed, resetting state');

      // Reset status
      setStatus({
        format_check: 'in_progress',
        compilation: 'pending',
        function_analysis: 'pending',
        vulnerability_scan: 'pending',
        report_generation: 'pending'
      });

      // Reset other state variables
      setCurrentStep(0);
      setError('');
      setExpandedSteps({});
      setVulnerabilities({});
      setShowProgressBar(true);
      setAnalysisDone(false);
      setReceivedBackendStatus(false);

      // Update previous reportId
      prevReportIdRef.current = reportId;
    }
  }, [reportId]);

  // Effect to handle analysis completion
  useEffect(() => {
    // Check if progress is 100% and all steps are completed or failed
    const allStepsCompleted = Object.values(status).every(s => s === 'completed' || s === 'failed');

    if (progressPercentage === 100 && allStepsCompleted) {
      // Set analysis as done to show detailed results and hide progress table
      setAnalysisDone(true);
      setShowProgressBar(false);

      // Scroll to results
      if (resultRef.current) {
        resultRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    }
  }, [progressPercentage, status]);

  // Calculate a score based on status and vulnerabilities
  const calculateScore = () => {
    // If any steps failed, lowest score
    if (hasFailedSteps) return 1.0;

    // If vulnerabilities were found, medium score
    if (hasVulnerabilities) {
      // If it's a critical vulnerability like reentrancy, lower score
      if (Object.values(vulnerabilities).some(v => 
        v.some(vuln => 
          vuln.toLowerCase().includes('reentrancy') || 
          vuln.toLowerCase().includes('overflow') ||
          vuln.toLowerCase().includes('underflow')
        )
      )) {
        return 2.0;
      }
      return 2.5;
    }

    // If all steps completed successfully and no vulnerabilities, highest score
    if (Object.values(status).every(s => s === 'completed')) {
      return 5.0;
    }

    // Default score for in-progress analysis
    return 3.0;
  };

  const score = calculateScore();

  return (
    <div className="mt-4">
      {/* Display error message if there is one */}
      {error && (
        <div className="alert alert-danger mb-3">
          {error}
        </div>
      )}

      {/* Tableau d'avancement dynamique - affiché uniquement pendant l'analyse */}
      {showProgressBar && (
        <div className="mb-4">
          <h4>Tableau d'avancement</h4>
          <table className="analysis-table">
            <thead>
              <tr>
                <th>Étape</th>
                <th>Statut</th>
                <th>Icône</th>
              </tr>
            </thead>
            <tbody>
              {steps.map((step, index) => {
                const stepStatus = status[step.key];

                return (
                  <tr key={step.key} className={
                    stepStatus === 'in_progress' || stepStatus === 'in-progress' ? 'in-progress' : 
                    stepStatus === 'completed' ? 'completed' : 
                    stepStatus === 'failed' ? 'failed' : ''
                  }>
                    <td>{step.title}</td>
                    <td>
                      <span className={`status-badge ${
                        stepStatus === 'completed' ? 'success' : 
                        stepStatus === 'failed' ? 'danger' : 
                        stepStatus === 'in_progress' || stepStatus === 'in-progress' ? 'info' :
                        'secondary'
                      }`}>
                        {getStatusText(stepStatus)}
                      </span>
                    </td>
                    <td>
                      <span className={`status-icon ${
                        stepStatus === 'in_progress' || stepStatus === 'in-progress' ? 'spinning-icon' : ''
                      }`}>
                        {getStatusIcon(stepStatus)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Tableau détaillé final - affiché uniquement lorsque l'analyse est terminée */}
      {analysisDone && (
        <div ref={resultRef} className="detailed-results">
          {/* Informations globales */}
          {reportData && (
            <div className="global-info mb-4">
              <h4>Informations globales</h4>
              <table className="info-table">
                <tbody>
                  <tr>
                    <th>Nom du fichier</th>
                    <td>{file ? file.name : reportData && reportData.contract_name ? `${reportData.contract_name}.sol` : 'Code saisi'}</td>
                  </tr>
                  {reportData.contract_name && (
                    <tr>
                      <th>Nom du contrat</th>
                      <td>{reportData.contract_name}</td>
                    </tr>
                  )}
                  {reportData.contract_address && (
                    <tr>
                      <th>Adresse déployée</th>
                      <td>{reportData.contract_address}</td>
                    </tr>
                  )}
                  {reportData.solc_version && (
                    <tr>
                      <th>Version du compilateur Solidity</th>
                      <td>{reportData.solc_version}</td>
                    </tr>
                  )}
                  <tr>
                    <th>Date d'analyse</th>
                    <td>{new Date().toLocaleString()}</td>
                  </tr>
                  <tr>
                    <th>Statut global</th>
                    <td className={hasFailedSteps || hasVulnerabilities ? 'text-danger' : 'text-success'}>
                      {hasFailedSteps || hasVulnerabilities ? '❌ KO' : '✅ OK'}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* Bloc Résultat global */}
          <div className={`result-block mb-4 ${hasFailedSteps || hasVulnerabilities ? 'danger' : 'success'}`}>
            <h4>Résultat global</h4>
            <div className="result-status">
              <strong>Statut :</strong> {hasFailedSteps || hasVulnerabilities ? '❌ KO – Vulnérabilité détectée' : '✅ OK – Aucun problème détecté'}
            </div>
            {hasVulnerabilities && reportData && reportData.attack && (
              <div className="vulnerability-type mt-2">
                <strong>Type de vulnérabilité :</strong> {reportData.attack}
              </div>
            )}
          </div>

          {/* Résumé de l'analyse */}
          {reportData && reportData.summary && (
            <div className="analysis-summary mb-4">
              <h4>🔎 Résumé de l'analyse</h4>
              <div className="summary-content">
                {reportData.summary.split('\n').map((line, index) => {
                  // Highlight critical points in red
                  if (line.toLowerCase().includes('critique') || 
                      line.toLowerCase().includes('critical') || 
                      line.toLowerCase().includes('vulnérabilité') || 
                      line.toLowerCase().includes('vulnerability')) {
                    return <p key={index} className="text-danger">{line}</p>;
                  }
                  return <p key={index}>{line}</p>;
                })}
              </div>
            </div>
          )}

          {/* Raisonnement du modèle */}
          {reportData && reportData.reasoning && (
            <div className="model-reasoning mb-4">
              <h4>🧠 Raisonnement du modèle</h4>
              <div className="reasoning-content">
                {reportData.reasoning.split('\n').map((line, index) => {
                  // Check if line contains code (starts with spaces or tabs)
                  if (line.match(/^\s{2,}/) || line.match(/^\t+/)) {
                    return <pre key={index} className="code-snippet">{line}</pre>;
                  }
                  return <p key={index}>{line}</p>;
                })}
              </div>
            </div>
          )}

          {/* Code d'exploit */}
          {reportData && reportData.exploit_code && (
            <div className="exploit-code-block mb-4">
              <h4>⚔️ Code d'exploit</h4>
              <pre className="exploit-code">
                {reportData.exploit_code}
              </pre>
            </div>
          )}

          {/* Download report button */}
          {downloadUrl && (
            <div className="mt-3 mb-4">
              <a
                href={downloadUrl}
                download="rapport.pdf"
                className="btn btn-success"
              >
                <span role="img" aria-label="télécharger">📥</span> Télécharger le rapport
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AnalysisProgress;
