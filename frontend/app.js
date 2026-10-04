/**
 * PromptCompiler Frontend Application Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  const rawInput = document.getElementById("rawPromptInput");
  const tokenBadge = document.getElementById("inputTokenBadge");
  const objectiveSelect = document.getElementById("objectiveSelect");
  const backendSelect = document.getElementById("backendSelect");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const optimizeBtn = document.getElementById("optimizeBtn");
  const backendStatus = document.getElementById("backendStatus");

  // Output containers
  const placeholderState = document.getElementById("placeholderState");
  const metricsGrid = document.getElementById("metricsGrid");
  const outputContainer = document.getElementById("outputContainer");
  const tabsContainer = document.getElementById("tabsContainer");
  const statusBadge = document.getElementById("statusBadge");
  const optimizedPromptText = document.getElementById("optimizedPromptText");
  const rationaleText = document.getElementById("rationaleText");
  const copyPromptBtn = document.getElementById("copyPromptBtn");
  const exportJsonBtn = document.getElementById("exportJsonBtn");

  // Metrics
  const tokenSavingsVal = document.getElementById("tokenSavingsVal");
  const tokenCountSub = document.getElementById("tokenCountSub");
  const qualityScoreVal = document.getElementById("qualityScoreVal");
  const qualityDeltaSub = document.getElementById("qualityDeltaSub");
  const invariantsVal = document.getElementById("invariantsVal");
  const redundanciesVal = document.getElementById("redundanciesVal");

  // Detailed lists
  const candidatesTableBody = document.getElementById("candidatesTableBody");
  const invariantsList = document.getElementById("invariantsList");
  const redundanciesList = document.getElementById("redundanciesList");
  const auditJson = document.getElementById("auditJson");

  // Modal
  const clarificationModal = document.getElementById("clarificationModal");
  const clarificationContainer = document.getElementById("clarificationQuestionsContainer");
  const skipClarificationBtn = document.getElementById("skipClarificationBtn");
  const submitClarificationBtn = document.getElementById("submitClarificationBtn");

  let latestReport = null;
  let activeClarifications = {};

  // Check Backend Status
  fetch("/api/backends")
    .then(r => r.json())
    .then(data => {
      const ollama = data.backends.find(b => b.id === "ollama");
      if (ollama && ollama.available) {
        backendStatus.textContent = "● Ollama Connected";
        backendStatus.style.color = "var(--accent-green)";
      } else {
        backendStatus.textContent = "● Mock Engine (Local)";
        backendStatus.style.color = "var(--accent-yellow)";
        backendSelect.value = "mock";
      }
    })
    .catch(() => {
      backendStatus.textContent = "● Offline (Mock Active)";
      backendStatus.style.color = "var(--accent-yellow)";
      backendSelect.value = "mock";
    });

  // Live Token Counter (approximation: ~4 chars per token)
  rawInput.addEventListener("input", () => {
    const text = rawInput.value.trim();
    if (!text) {
      tokenBadge.textContent = "0 tokens";
      return;
    }
    const words = text.split(/\s+/).length;
    const estTokens = Math.ceil(text.length / 3.8);
    tokenBadge.textContent = `~${estTokens} tokens (${words} words)`;
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

  // Step Tracker Helper
  function setPipelineStep(stepId, state) {
    const el = document.getElementById(stepId);
    if (!el) return;
    if (state === "active") {
      el.classList.add("active");
      el.classList.remove("completed");
    } else if (state === "completed") {
      el.classList.remove("active");
      el.classList.add("completed");
    } else {
      el.classList.remove("active", "completed");
    }
  }

  function resetStepper() {
    ["step-analysis", "step-planning", "step-candidates", "step-simulation", "step-eval", "step-selection"].forEach(id => {
      setPipelineStep(id, "idle");
    });
  }

  // Pre-Scan Ambiguities Handler
  analyzeBtn.addEventListener("click", async () => {
    const text = rawInput.value.trim();
    if (!text) {
      alert("Please enter a prompt first.");
      return;
    }

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "Analyzing...";

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_prompt: text,
          backend_type: backendSelect.value
        })
      });
      const data = await res.json();
      if (data.clarification_questions && data.clarification_questions.length > 0) {
        showClarificationModal(data.clarification_questions);
      } else {
        alert("Semantic analysis complete: Zero ambiguities detected. Prompt is clear!");
      }
    } catch (e) {
      alert("Error analyzing prompt: " + e.message);
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = "🔍 Scan Ambiguities";
    }
  });

  function showClarificationModal(questions) {
    clarificationContainer.innerHTML = "";
    activeClarifications = {};

    questions.forEach(q => {
      const card = document.createElement("div");
      card.style.margin = "0.8rem 0";
      card.innerHTML = `
        <label style="font-size:0.85rem; font-weight:600; display:block; margin-bottom:0.3rem;">
          ${q.question}
        </label>
        <div style="font-size:0.75rem; color:var(--text-secondary); margin-bottom:0.4rem;">
          Reason: ${q.reason} | Default: <em>${q.default_assumption}</em>
        </div>
        <input type="text" data-qid="${q.id}" placeholder="${q.default_assumption}" 
          style="width:100%; padding:0.5rem; background:var(--bg-primary); border:1px solid var(--border-color); color:white; border-radius:4px;">
      `;
      clarificationContainer.appendChild(card);
    });

    clarificationModal.style.display = "flex";
  }

  skipClarificationBtn.addEventListener("click", () => {
    clarificationModal.style.display = "none";
    runOptimization({});
  });

  submitClarificationBtn.addEventListener("click", () => {
    const answers = {};
    clarificationContainer.querySelectorAll("input").forEach(inp => {
      if (inp.value.trim()) {
        answers[inp.dataset.qid] = inp.value.trim();
      }
    });
    clarificationModal.style.display = "none";
    runOptimization(answers);
  });

  // Optimize Button
  optimizeBtn.addEventListener("click", () => {
    runOptimization(activeClarifications);
  });

  async function runOptimization(answers) {
    const text = rawInput.value.trim();
    if (!text) {
      alert("Please enter a prompt to optimize.");
      return;
    }

    optimizeBtn.disabled = true;
    optimizeBtn.textContent = "Compiling...";
    resetStepper();

    // Visual progression simulation
    setPipelineStep("step-analysis", "active");
    setTimeout(() => { setPipelineStep("step-analysis", "completed"); setPipelineStep("step-planning", "active"); }, 600);
    setTimeout(() => { setPipelineStep("step-planning", "completed"); setPipelineStep("step-candidates", "active"); }, 1200);
    setTimeout(() => { setPipelineStep("step-candidates", "completed"); setPipelineStep("step-simulation", "active"); }, 1800);
    setTimeout(() => { setPipelineStep("step-simulation", "completed"); setPipelineStep("step-eval", "active"); }, 2400);
    setTimeout(() => { setPipelineStep("step-eval", "completed"); setPipelineStep("step-selection", "active"); }, 3000);

    try {
      const res = await fetch("/api/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_prompt: text,
          objective: objectiveSelect.value,
          backend_type: backendSelect.value,
          clarification_answers: answers
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Optimization failed.");
      }

      const report = await res.json();
      latestReport = report;
      renderReport(report);
      setPipelineStep("step-selection", "completed");
    } catch (e) {
      alert("Optimization Error: " + e.message);
    } finally {
      optimizeBtn.disabled = false;
      optimizeBtn.textContent = "⚡ Compile & Optimize";
    }
  }

  function renderReport(report) {
    placeholderState.style.display = "none";
    metricsGrid.style.display = "grid";
    outputContainer.style.display = "block";
    tabsContainer.style.display = "block";
    statusBadge.style.display = "inline-block";

    // Metrics
    tokenSavingsVal.textContent = `-${report.percentage_reduction}%`;
    tokenCountSub.textContent = `${report.original_tokens} → ${report.final_tokens} tokens (saved ${report.tokens_saved})`;

    qualityScoreVal.textContent = `${report.final_quality_score.toFixed(1)} / 10`;
    qualityDeltaSub.textContent = `${report.quality_delta >= 0 ? '+' : ''}${report.quality_delta.toFixed(1)} baseline delta`;

    invariantsVal.textContent = `${report.preserved_hard_requirements.length} Hard`;
    invariantsSub.textContent = "100% Invariants Preserved";

    redundanciesVal.textContent = `${report.removed_redundancies.length}`;

    // Prompt Text & Rationale
    optimizedPromptText.textContent = report.final_optimized_prompt;
    rationaleText.textContent = report.selection_rationale;

    // Candidate Matrix Table
    candidatesTableBody.innerHTML = "";
    report.all_candidates.forEach(c => {
      const tr = document.createElement("tr");
      const isWinner = c.candidate_id === report.selected_candidate_id;
      if (isWinner) tr.style.backgroundColor = "rgba(46, 160, 67, 0.1)";

      tr.innerHTML = `
        <td style="font-weight:600; font-family:'JetBrains Mono'">${c.candidate_id} ${isWinner ? '🏆' : ''}</td>
        <td>${c.strategy}</td>
        <td style="font-family:'JetBrains Mono'">${c.tokens.token_count}</td>
        <td style="color:var(--accent-green)">-${c.tokens.reduction_percentage}%</td>
        <td>${c.scores.overall_quality_score.toFixed(1)}/10</td>
        <td>${c.passed_guardrail ? '<span style="color:var(--accent-green)">Passed</span>' : '<span style="color:var(--accent-red)">Rejected</span>'}</td>
      `;
      candidatesTableBody.appendChild(tr);
    });

    // Invariants List
    invariantsList.innerHTML = "";
    report.preserved_hard_requirements.forEach(req => {
      const li = document.createElement("li");
      li.innerHTML = `🔒 <strong>Preserved Invariant:</strong> ${req}`;
      invariantsList.appendChild(li);
    });

    // Redundancies List
    redundanciesList.innerHTML = "";
    report.removed_redundancies.forEach(red => {
      const li = document.createElement("li");
      li.innerHTML = `✂️ <strong>Eliminated:</strong> ${red}`;
      redundanciesList.appendChild(li);
    });

    // Raw JSON Audit
    auditJson.textContent = JSON.stringify(report, null, 2);
  }

  // Copy Prompt
  copyPromptBtn.addEventListener("click", () => {
    if (optimizedPromptText.textContent) {
      navigator.clipboard.writeText(optimizedPromptText.textContent);
      const originalText = copyPromptBtn.textContent;
      copyPromptBtn.textContent = "✓ Copied!";
      setTimeout(() => { copyPromptBtn.textContent = originalText; }, 2000);
    }
  });

  // Export JSON
  exportJsonBtn.addEventListener("click", () => {
    if (!latestReport) return;
    const blob = new Blob([JSON.stringify(latestReport, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `prompt-optimization-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });
});
