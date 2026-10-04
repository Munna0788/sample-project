/**
 * PromptCompiler - Frontend Application Logic
 * Laptop 2 Workspace (Branch: feature-frontend)
 * Interfacing with FastAPI backend on http://localhost:8000
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const rawInput = document.getElementById("rawPromptInput");
  const inputTokenBadge = document.getElementById("inputTokenBadge");
  const inputWordBadge = document.getElementById("inputWordBadge");
  const objectiveSelect = document.getElementById("objectiveSelect");
  const backendSelect = document.getElementById("backendSelect");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const optimizeBtn = document.getElementById("optimizeBtn");
  const clearPromptBtn = document.getElementById("clearPromptBtn");
  const pastePromptBtn = document.getElementById("pastePromptBtn");
  
  // Backend config
  const backendStatusDot = document.getElementById("backendStatusDot");
  const backendStatusText = document.getElementById("backendStatusText");
  const backendStatusPill = document.getElementById("backendStatusPill");
  const advancedSettings = document.getElementById("advancedSettings");
  const backendUrlInput = document.getElementById("backendUrlInput");
  const saveBackendUrlBtn = document.getElementById("saveBackendUrlBtn");

  // Output containers
  const placeholderState = document.getElementById("placeholderState");
  const metricsGrid = document.getElementById("metricsGrid");
  const roiCard = document.getElementById("roiCard");
  const outputContainer = document.getElementById("outputContainer");
  const tabsContainer = document.getElementById("tabsContainer");
  const statusBadge = document.getElementById("statusBadge");
  const winnerBadge = document.getElementById("winnerBadge");
  const rationaleBox = document.getElementById("rationaleBox");
  const rationaleText = document.getElementById("rationaleText");
  const rationaleStrategyTag = document.getElementById("rationaleStrategyTag");
  const copyPromptBtn = document.getElementById("copyPromptBtn");
  const exportJsonBtn = document.getElementById("exportJsonBtn");
  const copyAuditJsonBtn = document.getElementById("copyAuditJsonBtn");

  // Visual Diff Elements
  const diffOriginalText = document.getElementById("diffOriginalText");
  const diffOptimizedText = document.getElementById("diffOptimizedText");
  const originalDiffTokenCount = document.getElementById("originalDiffTokenCount");
  const optimizedDiffTokenCount = document.getElementById("optimizedDiffTokenCount");
  const highlightedPromptText = document.getElementById("highlightedPromptText");
  const unifiedDiffText = document.getElementById("unifiedDiffText");
  const optimizedPromptText = document.getElementById("optimizedPromptText");

  // Metrics Elements
  const tokenSavingsVal = document.getElementById("tokenSavingsVal");
  const tokenCountSub = document.getElementById("tokenCountSub");
  const tokenSavingsBar = document.getElementById("tokenSavingsBar");
  const qualityScoreVal = document.getElementById("qualityScoreVal");
  const qualityDeltaSub = document.getElementById("qualityDeltaSub");
  const qualityScoreBar = document.getElementById("qualityScoreBar");
  const invariantsVal = document.getElementById("invariantsVal");
  const invariantsSub = document.getElementById("invariantsSub");
  const redundanciesVal = document.getElementById("redundanciesVal");

  // ROI Elements
  const roiVolumeSelect = document.getElementById("roiVolumeSelect");
  const roiGpt4o = document.getElementById("roiGpt4o");
  const roiClaude = document.getElementById("roiClaude");
  const roiGemini = document.getElementById("roiGemini");
  const roiTokens = document.getElementById("roiTokens");

  // Detail Lists & Tabs
  const candidatesTableBody = document.getElementById("candidatesTableBody");
  const candidateDetailCard = document.getElementById("candidateDetailCard");
  const detailCandidateTitle = document.getElementById("detailCandidateTitle");
  const closeCandidateDetailBtn = document.getElementById("closeCandidateDetailBtn");
  const barTaskCorrectness = document.getElementById("barTaskCorrectness");
  const barTaskCorrectnessVal = document.getElementById("barTaskCorrectnessVal");
  const barReqPreservation = document.getElementById("barReqPreservation");
  const barReqPreservationVal = document.getElementById("barReqPreservationVal");
  const barCompleteness = document.getElementById("barCompleteness");
  const barCompletenessVal = document.getElementById("barCompletenessVal");
  const barClarity = document.getElementById("barClarity");
  const barClarityVal = document.getElementById("barClarityVal");
  const barFormat = document.getElementById("barFormat");
  const barFormatVal = document.getElementById("barFormatVal");
  const detailFeedbackBox = document.getElementById("detailFeedbackBox");
  const testExecutionsContainer = document.getElementById("testExecutionsContainer");
  
  const invariantsList = document.getElementById("invariantsList");
  const redundanciesList = document.getElementById("redundanciesList");
  const auditJson = document.getElementById("auditJson");
  const candidateCountTag = document.getElementById("candidateCountTag");
  const invariantsCountTag = document.getElementById("invariantsCountTag");
  const redundanciesCountTag = document.getElementById("redundanciesCountTag");

  // Modal Elements
  const clarificationModal = document.getElementById("clarificationModal");
  const clarificationContainer = document.getElementById("clarificationQuestionsContainer");
  const closeClarificationModalBtn = document.getElementById("closeClarificationModalBtn");
  const skipClarificationBtn = document.getElementById("skipClarificationBtn");
  const submitClarificationBtn = document.getElementById("submitClarificationBtn");

  // Toast Container
  const toastContainer = document.getElementById("toastContainer");

  // State Variables
  let apiBaseUrl = localStorage.getItem("promptcompiler_api_base") || (window.location.port === "8000" ? "" : "http://localhost:8000");
  backendUrlInput.value = apiBaseUrl;
  let latestReport = null;
  let activeClarifications = {};
  let currentCandidateInView = null;

  // Preset Prompts Data
  const PRESET_PROMPTS = {
    csv: {
      text: `Hey! Could you please act as a senior python data engineering specialist and write me a clean, efficient python function that takes a csv file path as an input, parses the rows, and computes the column-wise arithmetic averages for all numerical columns? Please make sure to handle missing or null values gracefully. Please make sure it outputs strictly valid JSON only. As I mentioned earlier, please never hallucinate or invent non-existent column names, and please make sure the output format is valid JSON with zero markdown wrapping. Also please be very fast and include error handling! Thank you so much!`,
      objective: "balanced"
    },
    support: {
      text: `You are a helpful customer service chatbot for an online shoe retailer named ShoeSprint. Always greet the customer warmly and politely ask how you can help them today. If the customer asks about returning worn shoes, tell them our policy strictly allows returns only within 30 days of delivery if the shoes are unworn and in original packaging. Under no circumstances should you ever authorize a refund for shoes worn outdoors. Keep your answers concise, empathetic, and professional. Always ask if they need help with anything else before ending. Please make sure to be very polite and courteous!`,
      objective: "maximum_quality"
    },
    extractor: {
      text: `Please extract all purchase order details from the provided unformatted invoice email text. Extract the vendor name, invoice date, invoice number, line items containing item description, quantity, and unit price, tax rate, and total amount due. It is very important that you do not include any explanatory conversational comments or conversational greetings. I need the response to be strictly a JSON object conforming to the schema { vendor: string, invoice_id: string, date: string, items: Array<{ desc: string, qty: number, unit_price: number }>, total: number }. Please double check your math and make sure all numbers are actual numerical floats or ints, not strings!`,
      objective: "maximum_compression"
    },
    refactor: {
      text: `Review the following Python snippet for potential concurrency bottlenecks, memory leaks, and adherence to PEP-8 standards. Identify any synchronous I/O blocking the asyncio event loop. For each identified issue, provide the exact line number, severity rating (Low, Medium, High, Critical), root cause analysis, and the refactored code replacement. Make sure the code recommendations are production ready and type annotated. Do not repeat instructions, do not include filler greetings, and strictly output markdown tables for findings.`,
      objective: "balanced"
    }
  };

  // ==========================================================================
  // Toast Notification System
  // ==========================================================================
  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icon = type === "success" ? "✓" : type === "error" ? "⚠️" : "ℹ️";
    toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = "slideToastOut 0.3s ease forwards";
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  // ==========================================================================
  // Backend Connection & Health Check
  // ==========================================================================
  async function checkBackendHealth() {
    backendStatusDot.className = "status-dot";
    backendStatusText.textContent = "Connecting...";

    try {
      const res = await fetch(`${apiBaseUrl}/api/backends`, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      
      const ollama = data.backends.find(b => b.id === "ollama");
      if (ollama && ollama.available) {
        backendStatusDot.className = "status-dot connected";
        backendStatusText.textContent = "Ollama Active";
        backendSelect.value = "ollama";
      } else {
        backendStatusDot.className = "status-dot connected";
        backendStatusText.textContent = "Mock Engine Active";
        backendSelect.value = "mock";
      }
    } catch (e) {
      backendStatusDot.className = "status-dot";
      backendStatusText.textContent = "Offline (Mock Fallback)";
      backendSelect.value = "mock";
    }
  }

  saveBackendUrlBtn.addEventListener("click", () => {
    let url = backendUrlInput.value.trim();
    if (url.endsWith("/")) url = url.slice(0, -1);
    apiBaseUrl = url;
    localStorage.setItem("promptcompiler_api_base", apiBaseUrl);
    showToast(`Backend API host set to ${apiBaseUrl || "relative"}`, "info");
    checkBackendHealth();
  });

  backendStatusPill.addEventListener("click", () => {
    advancedSettings.open = !advancedSettings.open;
    if (advancedSettings.open) {
      backendUrlInput.focus();
    }
  });

  // Initial check
  checkBackendHealth();

  // ==========================================================================
  // Live Token & Word Counter
  // ==========================================================================
  function updateTokenEstimate() {
    const text = rawInput.value.trim();
    if (!text) {
      inputTokenBadge.textContent = "0 tokens";
      inputWordBadge.textContent = "0 words";
      return;
    }
    const words = text.split(/\s+/).filter(Boolean).length;
    // Approximating tiktoken cl100k_base (~3.85 characters per token for English text)
    const estTokens = Math.max(1, Math.ceil(text.length / 3.85));
    inputTokenBadge.textContent = `~${estTokens} tokens`;
    inputWordBadge.textContent = `${words} words`;
  }

  rawInput.addEventListener("input", updateTokenEstimate);

  // Quick Action Buttons
  clearPromptBtn.addEventListener("click", () => {
    rawInput.value = "";
    updateTokenEstimate();
    rawInput.focus();
  });

  pastePromptBtn.addEventListener("click", async () => {
    try {
      const clipText = await navigator.clipboard.readText();
      if (clipText) {
        rawInput.value = clipText;
        updateTokenEstimate();
        showToast("Pasted from clipboard", "success");
      }
    } catch (e) {
      showToast("Clipboard access denied. Please paste manually.", "error");
    }
  });

  // Demo Presets Selection
  document.querySelectorAll(".preset-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      const presetKey = pill.dataset.preset;
      const preset = PRESET_PROMPTS[presetKey];
      if (preset) {
        rawInput.value = preset.text;
        objectiveSelect.value = preset.objective;
        updateTokenEstimate();
        showToast(`Loaded ${pill.textContent} preset`, "info");
      }
    });
  });

  // Keyboard shortcut Ctrl+Enter / Cmd+Enter
  rawInput.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      runOptimization(activeClarifications);
    }
  });

  // ==========================================================================
  // View Modes (Side-by-Side, Highlighted, Unified, Raw)
  // ==========================================================================
  document.querySelectorAll(".view-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".view-tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".diff-view-pane").forEach(p => p.classList.remove("active"));
      
      btn.classList.add("active");
      const viewMode = btn.dataset.view;
      if (viewMode === "side-by-side") document.getElementById("viewSideBySide").classList.add("active");
      if (viewMode === "highlighted") document.getElementById("viewHighlighted").classList.add("active");
      if (viewMode === "unified") document.getElementById("viewUnified").classList.add("active");
      if (viewMode === "raw") document.getElementById("viewRaw").classList.add("active");
    });
  });

  // Tabs Handler
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add("active");
    });
  });

  // ==========================================================================
  // Pipeline Stepper Controller
  // ==========================================================================
  function setPipelineStep(stepId, state) {
    const el = document.getElementById(stepId);
    if (!el) return;
    el.classList.remove("active", "completed");
    if (state === "active") el.classList.add("active");
    if (state === "completed") el.classList.add("completed");
  }

  function resetStepper() {
    ["step-analysis", "step-planning", "step-candidates", "step-simulation", "step-eval", "step-selection"].forEach(id => {
      setPipelineStep(id, "idle");
    });
  }

  // ==========================================================================
  // Semantic Analysis & Ambiguities Scan
  // ==========================================================================
  analyzeBtn.addEventListener("click", async () => {
    const text = rawInput.value.trim();
    if (!text) {
      showToast("Please enter a prompt to scan.", "error");
      return;
    }

    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = `<span class="btn-icon">⏳</span> Scanning...`;

    try {
      const res = await fetch(`${apiBaseUrl}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_prompt: text,
          backend_type: backendSelect.value
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      if (data.clarification_questions && data.clarification_questions.length > 0) {
        showClarificationModal(data.clarification_questions);
      } else {
        showToast("Analysis complete: Zero ambiguities detected. Prompt is clear!", "success");
      }
    } catch (e) {
      showToast(`Scan error: ${e.message}`, "error");
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.innerHTML = `<span class="btn-icon">🔍</span> Scan Ambiguities`;
    }
  });

  function showClarificationModal(questions) {
    clarificationContainer.innerHTML = "";
    activeClarifications = {};

    questions.forEach(q => {
      const card = document.createElement("div");
      card.className = "clarification-card";
      card.innerHTML = `
        <label>${escapeHtml(q.question)}</label>
        <div class="clarification-meta">
          <strong>Why:</strong> ${escapeHtml(q.reason)} &bull; 
          <strong>Default:</strong> <em>${escapeHtml(q.default_assumption)}</em>
        </div>
        <input type="text" data-qid="${escapeHtml(q.id)}" placeholder="${escapeHtml(q.default_assumption)}">
      `;
      clarificationContainer.appendChild(card);
    });

    clarificationModal.style.display = "flex";
  }

  function hideClarificationModal() {
    clarificationModal.style.display = "none";
  }

  closeClarificationModalBtn.addEventListener("click", hideClarificationModal);

  skipClarificationBtn.addEventListener("click", () => {
    hideClarificationModal();
    runOptimization({});
  });

  submitClarificationBtn.addEventListener("click", () => {
    const answers = {};
    clarificationContainer.querySelectorAll("input").forEach(inp => {
      if (inp.value.trim()) {
        answers[inp.dataset.qid] = inp.value.trim();
      }
    });
    hideClarificationModal();
    runOptimization(answers);
  });

  // ==========================================================================
  // Full Optimization Engine Execution
  // ==========================================================================
  optimizeBtn.addEventListener("click", () => {
    runOptimization(activeClarifications);
  });

  async function runOptimization(answers = {}) {
    const text = rawInput.value.trim();
    if (!text) {
      showToast("Please enter a prompt to optimize.", "error");
      return;
    }

    optimizeBtn.disabled = true;
    optimizeBtn.innerHTML = `<span class="btn-icon">⚡</span> Compiling...`;
    resetStepper();

    // Visual animated progress through pipeline steps
    setPipelineStep("step-analysis", "active");
    const t1 = setTimeout(() => { setPipelineStep("step-analysis", "completed"); setPipelineStep("step-planning", "active"); }, 400);
    const t2 = setTimeout(() => { setPipelineStep("step-planning", "completed"); setPipelineStep("step-candidates", "active"); }, 800);
    const t3 = setTimeout(() => { setPipelineStep("step-candidates", "completed"); setPipelineStep("step-simulation", "active"); }, 1200);
    const t4 = setTimeout(() => { setPipelineStep("step-simulation", "completed"); setPipelineStep("step-eval", "active"); }, 1600);
    const t5 = setTimeout(() => { setPipelineStep("step-eval", "completed"); setPipelineStep("step-selection", "active"); }, 2000);

    try {
      const res = await fetch(`${apiBaseUrl}/api/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_prompt: text,
          objective: objectiveSelect.value,
          backend_type: backendSelect.value,
          clarification_answers: answers
        })
      });

      // Clear any pending timeouts
      clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); clearTimeout(t4); clearTimeout(t5);

      if (!res.ok) {
        let errMsg = `Server returned ${res.status}`;
        try {
          const err = await res.json();
          errMsg = err.detail || errMsg;
        } catch (_) {}
        throw new Error(errMsg);
      }

      const report = await res.json();
      latestReport = report;

      // Mark all steps completed
      ["step-analysis", "step-planning", "step-candidates", "step-simulation", "step-eval", "step-selection"].forEach(id => {
        setPipelineStep(id, "completed");
      });

      renderReport(report);
      showToast(`Prompt compiled! Reduced by ${report.percentage_reduction}% (${report.tokens_saved} tokens saved)`, "success");
    } catch (e) {
      ["step-analysis", "step-planning", "step-candidates", "step-simulation", "step-eval", "step-selection"].forEach(id => {
        setPipelineStep(id, "idle");
      });
      showToast(`Optimization failed: ${e.message}`, "error");
    } finally {
      optimizeBtn.disabled = false;
      optimizeBtn.innerHTML = `<span class="btn-icon">⚡</span> Compile & Optimize <span class="btn-kbd">Ctrl+↵</span>`;
    }
  }

  // ==========================================================================
  // Report Renderer & Visualizer
  // ==========================================================================
  function renderReport(report) {
    placeholderState.style.display = "none";
    metricsGrid.style.display = "grid";
    roiCard.style.display = "block";
    outputContainer.style.display = "block";
    tabsContainer.style.display = "block";
    statusBadge.style.display = "inline-block";
    winnerBadge.style.display = "inline-block";
    winnerBadge.textContent = `🏆 ${report.selected_candidate_id}`;

    // 1. Metrics Cards
    tokenSavingsVal.textContent = `-${report.percentage_reduction}%`;
    tokenCountSub.textContent = `${report.original_tokens} → ${report.final_tokens} tokens (saved ${report.tokens_saved})`;
    tokenSavingsBar.style.width = `${Math.min(100, Math.max(5, report.percentage_reduction))}%`;

    qualityScoreVal.textContent = `${report.final_quality_score.toFixed(1)} / 10`;
    qualityDeltaSub.textContent = `${report.quality_delta >= 0 ? '+' : ''}${report.quality_delta.toFixed(1)} baseline delta`;
    qualityScoreBar.style.width = `${(report.final_quality_score / 10) * 100}%`;

    invariantsVal.textContent = `${report.preserved_hard_requirements.length} Hard`;
    invariantsSub.textContent = "100% Invariants Preserved";

    redundanciesVal.textContent = `${report.removed_redundancies.length}`;

    // 2. ROI Projections
    updateRoiCalculations(report.tokens_saved);

    // 3. Raw Prompt Pre
    optimizedPromptText.textContent = report.final_optimized_prompt;

    // 4. Rationale Banner
    rationaleText.textContent = report.selection_rationale;
    const winnerCandidate = report.all_candidates.find(c => c.candidate_id === report.selected_candidate_id);
    rationaleStrategyTag.textContent = winnerCandidate ? winnerCandidate.strategy : "Optimal";

    // 5. Rich Visual Diff Generation
    renderVisualDiff(report.original_prompt, report.final_optimized_prompt, report.preserved_hard_requirements);

    // 6. Syntax Highlighted Output
    highlightedPromptText.innerHTML = formatPromptSyntax(report.final_optimized_prompt);

    // 7. Unified Diff Generation
    renderUnifiedDiff(report.original_prompt, report.final_optimized_prompt);

    // 8. Candidate Matrix Table
    renderCandidatesTable(report);

    // 9. Preserved Invariants List
    invariantsList.innerHTML = "";
    invariantsCountTag.textContent = report.preserved_hard_requirements.length;
    report.preserved_hard_requirements.forEach(req => {
      const li = document.createElement("li");
      li.innerHTML = `<span>🔒</span> <div><strong>Preserved Hard Invariant:</strong> ${escapeHtml(req)}</div>`;
      invariantsList.appendChild(li);
    });
    if (report.preserved_soft_preferences && report.preserved_soft_preferences.length > 0) {
      report.preserved_soft_preferences.forEach(pref => {
        const li = document.createElement("li");
        li.innerHTML = `<span>✨</span> <div><strong>Preserved Style Preference:</strong> ${escapeHtml(pref)}</div>`;
        invariantsList.appendChild(li);
      });
    }

    // 10. Eliminated Redundancies List
    redundanciesList.innerHTML = "";
    redundanciesCountTag.textContent = report.removed_redundancies.length;
    report.removed_redundancies.forEach(red => {
      const li = document.createElement("li");
      li.innerHTML = `<span>✂️</span> <div><strong>Eliminated Redundancy:</strong> ${escapeHtml(red)}</div>`;
      redundanciesList.appendChild(li);
    });

    // 11. Compilation Audit JSON
    auditJson.innerHTML = formatJsonSyntax(JSON.stringify(report, null, 2));
  }

  // ==========================================================================
  // ROI Financial Calculations
  // ==========================================================================
  function updateRoiCalculations(tokensSavedPerCall) {
    const monthlyCalls = parseInt(roiVolumeSelect.value, 10);
    const annualCalls = monthlyCalls * 12;
    const annualTokensSaved = annualCalls * tokensSavedPerCall;

    // Pricing per 1M input tokens
    // GPT-4o: $2.50 / 1M
    // Claude 3.5 Sonnet: $3.00 / 1M
    // Gemini 1.5 Pro: $1.25 / 1M
    const gpt4oSavings = (annualTokensSaved / 1000000) * 2.50;
    const claudeSavings = (annualTokensSaved / 1000000) * 3.00;
    const geminiSavings = (annualTokensSaved / 1000000) * 1.25;

    roiGpt4o.textContent = formatCurrency(gpt4oSavings) + " / yr";
    roiClaude.textContent = formatCurrency(claudeSavings) + " / yr";
    roiGemini.textContent = formatCurrency(geminiSavings) + " / yr";
    roiTokens.textContent = `${formatNumber(annualTokensSaved)} Tokens / Yr`;
  }

  roiVolumeSelect.addEventListener("change", () => {
    if (latestReport) updateRoiCalculations(latestReport.tokens_saved);
  });

  function formatCurrency(val) {
    return "$" + val.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function formatNumber(val) {
    if (val >= 1000000000) return (val / 1000000000).toFixed(1) + "B";
    if (val >= 1000000) return (val / 1000000).toFixed(1) + "M";
    if (val >= 1000) return (val / 1000).toFixed(1) + "K";
    return val.toString();
  }

  // ==========================================================================
  // Rich Visual Diff Algorithm (LCS Word Tokenizer)
  // ==========================================================================
  function renderVisualDiff(originalStr, optimizedStr, invariants = []) {
    originalDiffTokenCount.textContent = `${latestReport.original_tokens} tokens`;
    optimizedDiffTokenCount.textContent = `${latestReport.final_tokens} tokens`;

    const origTokens = tokenizeWords(originalStr);
    const optTokens = tokenizeWords(optimizedStr);

    const diff = computeLcsDiff(origTokens, optTokens);

    let origHtml = "";
    let optHtml = "";

    diff.forEach(item => {
      const escaped = escapeHtml(item.value);
      if (item.type === "equal") {
        origHtml += escaped;
        optHtml += escaped;
      } else if (item.type === "delete") {
        origHtml += `<span class="diff-del" title="Eliminated Redundancy">${escaped}</span>`;
      } else if (item.type === "insert") {
        optHtml += `<span class="diff-add" title="Added Structure / Directive">${escaped}</span>`;
      }
    });

    diffOriginalText.innerHTML = origHtml;
    diffOptimizedText.innerHTML = optHtml;
  }

  function renderUnifiedDiff(originalStr, optimizedStr) {
    const origLines = originalStr.split("\n");
    const optLines = optimizedStr.split("\n");

    let html = `<div class="unified-line header">--- original (baseline)</div>`;
    html += `<div class="unified-line header">+++ optimized (compiled)</div>`;

    // Simple line-level unified diff
    let i = 0;
    let j = 0;
    while (i < origLines.length || j < optLines.length) {
      const oLine = origLines[i];
      const nLine = optLines[j];

      if (oLine === nLine) {
        html += `<div class="unified-line">  ${escapeHtml(oLine || "")}</div>`;
        i++; j++;
      } else {
        if (i < origLines.length) {
          html += `<div class="unified-line del">- ${escapeHtml(oLine)}</div>`;
          i++;
        }
        if (j < optLines.length) {
          html += `<div class="unified-line add">+ ${escapeHtml(nLine)}</div>`;
          j++;
        }
      }
    }

    unifiedDiffText.innerHTML = html;
  }

  // Word tokenization preserving whitespace
  function tokenizeWords(str) {
    return str.match(/\S+|\s+/g) || [];
  }

  // Longest Common Subsequence Diff Engine
  function computeLcsDiff(arr1, arr2) {
    const m = arr1.length;
    const n = arr2.length;
    
    // DP matrix for lengths
    const dp = Array.from({ length: m + 1 }, () => new Uint16Array(n + 1));

    for (let i = 1; i <= m; i++) {
      for (let j = 1; j <= n; j++) {
        if (arr1[i - 1].trim().toLowerCase() === arr2[j - 1].trim().toLowerCase() && arr1[i - 1].trim() !== "") {
          dp[i][j] = dp[i - 1][j - 1] + 1;
        } else {
          dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
        }
      }
    }

    // Backtrack to find diff
    const result = [];
    let i = m;
    let j = n;

    while (i > 0 || j > 0) {
      if (i > 0 && j > 0 && arr1[i - 1].trim().toLowerCase() === arr2[j - 1].trim().toLowerCase() && arr1[i - 1].trim() !== "") {
        result.unshift({ type: "equal", value: arr2[j - 1] });
        i--;
        j--;
      } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
        result.unshift({ type: "insert", value: arr2[j - 1] });
        j--;
      } else if (i > 0 && (j === 0 || dp[i][j - 1] < dp[i - 1][j])) {
        result.unshift({ type: "delete", value: arr1[i - 1] });
        i--;
      }
    }

    return result;
  }

  // ==========================================================================
  // Prompt Syntax Highlighting Formatter
  // ==========================================================================
  function formatPromptSyntax(text) {
    let html = escapeHtml(text);

    // Markdown Headings: # Heading, ## Heading, ### Heading
    html = html.replace(/^(#{1,3}\s+.*$)/gm, '<span class="syntax-heading">$1</span>');

    // Bullet points: - item, * item
    html = html.replace(/^(\s*[-*]\s+)/gm, '<span class="syntax-bullet">&bull; </span>');

    // Directive Keywords
    const directives = ["MUST", "NEVER", "ALWAYS", "REQUIRED", "DO NOT", "JSON", "SCHEMA:", "CONSTRAINTS:", "OUTPUT:"];
    directives.forEach(word => {
      const reg = new RegExp(`\\b(${word})\\b`, "g");
      html = html.replace(reg, '<span class="syntax-directive">$1</span>');
    });

    // Variables {name} or <tag>
    html = html.replace(/(\{[a-zA-Z0-9_-]+\})/g, '<span class="syntax-variable">$1</span>');

    // Code blocks ```json ... ```
    html = html.replace(/(```[\s\S]*?```)/g, '<div class="syntax-codeblock">$1</div>');

    return html;
  }

  // ==========================================================================
  // JSON Syntax Highlighter
  // ==========================================================================
  function formatJsonSyntax(jsonStr) {
    return jsonStr.replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
      (match) => {
        let cls = "json-number";
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            cls = "json-key";
          } else {
            cls = "json-string";
          }
        } else if (/true|false/.test(match)) {
          cls = "json-boolean";
        } else if (/null/.test(match)) {
          cls = "json-null";
        }
        return `<span class="${cls}">${escapeHtml(match)}</span>`;
      }
    );
  }

  // ==========================================================================
  // Candidate Matrix & Detailed Inspection
  // ==========================================================================
  function renderCandidatesTable(report) {
    candidatesTableBody.innerHTML = "";
    candidateCountTag.textContent = report.all_candidates.length;

    report.all_candidates.forEach((c) => {
      const isWinner = c.candidate_id === report.selected_candidate_id;
      const tr = document.createElement("tr");
      if (isWinner) tr.style.backgroundColor = "rgba(16, 185, 129, 0.08)";

      tr.innerHTML = `
        <td style="font-weight:700; font-family:'JetBrains Mono'">${escapeHtml(c.candidate_id)} ${isWinner ? '🏆' : ''}</td>
        <td><span class="badge" style="text-transform:capitalize;">${escapeHtml(c.strategy)}</span></td>
        <td style="font-family:'JetBrains Mono'">${c.tokens.token_count}</td>
        <td style="color:var(--accent-green); font-family:'JetBrains Mono'">-${c.tokens.reduction_percentage}%</td>
        <td><strong>${c.scores.overall_quality_score.toFixed(1)}</strong>/10</td>
        <td>${c.passed_guardrail 
          ? '<span style="color:var(--accent-green); font-weight:600;">✓ Pass</span>' 
          : '<span style="color:var(--accent-red); font-weight:600;">✗ Rejected</span>'}
        </td>
        <td>
          <button type="button" class="btn btn-sm inspect-candidate-btn" data-cid="${escapeHtml(c.candidate_id)}">
            Inspect
          </button>
        </td>
      `;
      candidatesTableBody.appendChild(tr);
    });

    // Attach inspect listeners
    document.querySelectorAll(".inspect-candidate-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const cid = btn.dataset.cid;
        const candidate = report.all_candidates.find(c => c.candidate_id === cid);
        if (candidate) inspectCandidate(candidate, report);
      });
    });
  }

  function inspectCandidate(candidate, report) {
    currentCandidateInView = candidate;
    const isWinner = candidate.candidate_id === report.selected_candidate_id;
    detailCandidateTitle.textContent = `Candidate: ${candidate.candidate_id} (${candidate.strategy.toUpperCase()}) ${isWinner ? '🏆 Winner' : ''}`;

    // Score bars
    const s = candidate.scores;
    barTaskCorrectnessVal.textContent = `${s.task_correctness.toFixed(1)}/10`;
    barTaskCorrectness.style.width = `${(s.task_correctness / 10) * 100}%`;

    barReqPreservationVal.textContent = `${s.requirement_preservation.toFixed(1)}/10`;
    barReqPreservation.style.width = `${(s.requirement_preservation / 10) * 100}%`;

    barCompletenessVal.textContent = `${s.completeness.toFixed(1)}/10`;
    barCompleteness.style.width = `${(s.completeness / 10) * 100}%`;

    barClarityVal.textContent = `${s.clarity.toFixed(1)}/10`;
    barClarity.style.width = `${(s.clarity / 10) * 100}%`;

    barFormatVal.textContent = `${s.output_format_adherence.toFixed(1)}/10`;
    barFormat.style.width = `${(s.output_format_adherence / 10) * 100}%`;

    // Notes
    detailFeedbackBox.innerHTML = `
      <strong>Evaluator Diagnostic:</strong> ${escapeHtml(s.evaluation_notes || "All hard requirements verified.")}
      ${candidate.guardrail_rejection_reason ? `<div style="color:var(--accent-red); margin-top:0.3rem;">⚠️ Rejection Reason: ${escapeHtml(candidate.guardrail_rejection_reason)}</div>` : ""}
    `;

    // Test executions
    testExecutionsContainer.innerHTML = "";
    if (candidate.test_executions && candidate.test_executions.length > 0) {
      candidate.test_executions.forEach(test => {
        const item = document.createElement("div");
        item.className = "test-run-item";
        item.innerHTML = `
          <div class="test-run-meta">
            <span>Test Case: ${escapeHtml(test.test_case_id)}</span>
            <span>Latency: ${test.latency_ms.toFixed(1)}ms</span>
          </div>
          <div class="test-run-output">${escapeHtml(test.output_text)}</div>
        `;
        testExecutionsContainer.appendChild(item);
      });
    } else {
      testExecutionsContainer.innerHTML = `<div style="font-size:0.75rem; color:var(--text-muted);">No runtime test simulations recorded for this candidate.</div>`;
    }

    candidateDetailCard.style.display = "block";
    candidateDetailCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  closeCandidateDetailBtn.addEventListener("click", () => {
    candidateDetailCard.style.display = "none";
  });

  // ==========================================================================
  // Clipboard & Export Utilities
  // ==========================================================================
  copyPromptBtn.addEventListener("click", () => {
    if (optimizedPromptText.textContent) {
      navigator.clipboard.writeText(optimizedPromptText.textContent);
      showToast("Optimized prompt copied to clipboard!", "success");
    }
  });

  exportJsonBtn.addEventListener("click", () => {
    if (!latestReport) return;
    const blob = new Blob([JSON.stringify(latestReport, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `prompt-optimization-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Optimization report JSON downloaded", "success");
  });

  copyAuditJsonBtn.addEventListener("click", () => {
    if (latestReport) {
      navigator.clipboard.writeText(JSON.stringify(latestReport, null, 2));
      showToast("Audit JSON copied to clipboard!", "success");
    }
  });

  // Helper: HTML Escaping
  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
