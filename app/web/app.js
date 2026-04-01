const form = document.getElementById("audit-form");
const screenshotInput = document.getElementById("screenshot");
const screenshotPreview = document.getElementById("screenshot-preview");
const previewImage = document.getElementById("preview-image");
const formStatus = document.getElementById("form-status");
const emptyState = document.getElementById("empty-state");
const results = document.getElementById("results");
const submitButton = document.getElementById("submit-button");

const croScore = document.getElementById("cro-score");
const biggestLeak = document.getElementById("biggest-leak");
const scoreBadgeValue = document.getElementById("score-badge-value");
const overallConfidence = document.getElementById("overall-confidence");

const categoryScores = document.getElementById("category-scores");
const categoryConfidence = document.getElementById("category-confidence");
const highPriorityFixes = document.getElementById("high-priority-fixes");
const mediumPriorityFixes = document.getElementById("medium-priority-fixes");
const lowPriorityFixes = document.getElementById("low-priority-fixes");
const rewriteSuggestions = document.getElementById("rewrite-suggestions");
const abTestIdeas = document.getElementById("ab-test-ideas");
const psychologicalImprovements = document.getElementById("psychological-improvements");
const mobileImprovements = document.getElementById("mobile-improvements");
const missingEvidenceNotes = document.getElementById("missing-evidence-notes");
const recommendedNextUploads = document.getElementById("recommended-next-uploads");
const analysisNotes = document.getElementById("analysis-notes");

function setStatus(message, isError = false) {
  formStatus.textContent = message;
  formStatus.classList.toggle("error", isError);
}

function createCard(title, body, className = "") {
  const article = document.createElement("article");
  article.className = className;

  const heading = document.createElement("h4");
  heading.textContent = title;
  article.appendChild(heading);

  if (Array.isArray(body)) {
    const list = document.createElement("ul");
    body.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      list.appendChild(li);
    });
    article.appendChild(list);
    return article;
  }

  const paragraph = document.createElement("p");
  paragraph.textContent = body;
  article.appendChild(paragraph);
  return article;
}

function renderEmptyMessage(container, message) {
  container.innerHTML = "";
  const card = createCard("No items", message, "idea-card");
  container.appendChild(card);
}

function renderFixes(container, items, tone) {
  container.innerHTML = "";
  if (!items.length) {
    renderEmptyMessage(container, "Nothing urgent surfaced in this bucket.");
    return;
  }

  items.forEach((item) => {
    const article = document.createElement("article");
    article.className = `fix-card ${tone}`;

    const title = document.createElement("h4");
    title.textContent = item.issue;
    article.appendChild(title);

    const recommendation = document.createElement("p");
    recommendation.textContent = item.recommendation;
    article.appendChild(recommendation);

    const impact = document.createElement("p");
    impact.className = "fix-impact";
    impact.textContent = `Impact: ${item.expected_impact}`;
    article.appendChild(impact);

    container.appendChild(article);
  });
}

function renderScoreGrid(scores) {
  categoryScores.innerHTML = "";
  Object.entries(scores).forEach(([label, value]) => {
    const card = document.createElement("article");
    card.className = "score-card";

    const scoreValue = document.createElement("p");
    scoreValue.className = "score-value";
    scoreValue.textContent = `${value}/10`;
    card.appendChild(scoreValue);

    const scoreLabel = document.createElement("p");
    scoreLabel.className = "score-label";
    scoreLabel.textContent = label.replaceAll("_", " ");
    card.appendChild(scoreLabel);

    categoryScores.appendChild(card);
  });
}

function renderCategoryConfidence(data) {
  categoryConfidence.innerHTML = "";
  Object.entries(data).forEach(([label, value]) => {
    const article = document.createElement("article");
    article.className = "insight-card";

    const title = document.createElement("h4");
    title.textContent = label.replaceAll("_", " ");
    article.appendChild(title);

    const body = document.createElement("p");
    body.textContent = `Visibility: ${value.evidence_visibility}. Confidence: ${value.confidence}.`;
    article.appendChild(body);

    if (value.note) {
      const note = document.createElement("p");
      note.className = "confidence-note";
      note.textContent = value.note;
      article.appendChild(note);
    }

    categoryConfidence.appendChild(article);
  });
}

function renderRewriteSuggestions(data) {
  rewriteSuggestions.innerHTML = "";
  rewriteSuggestions.appendChild(
    createCard("Outcome-driven headline", data.headline, "rewrite-card")
  );
  rewriteSuggestions.appendChild(
    createCard("Stronger CTA text", data.cta_text, "rewrite-card")
  );
  rewriteSuggestions.appendChild(
    createCard("Bundle pricing structure", data.bundle_pricing, "rewrite-card")
  );
  rewriteSuggestions.appendChild(
    createCard("Benefit-driven bullets", data.bullets, "rewrite-card")
  );
}

function renderSimpleCards(container, items, titleKey, bodyKey, className, emptyMessage) {
  container.innerHTML = "";
  if (!items.length) {
    renderEmptyMessage(container, emptyMessage);
    return;
  }

  items.forEach((item) => {
    const title = typeof titleKey === "function" ? titleKey(item) : item[titleKey];
    const body = typeof bodyKey === "function" ? bodyKey(item) : item[bodyKey];
    container.appendChild(createCard(title, body, className));
  });
}

function renderResults(data) {
  emptyState.classList.add("hidden");
  results.classList.remove("hidden");

  croScore.textContent = `CRO Score: ${data.cro_score}/100`;
  biggestLeak.textContent = data.biggest_leak;
  scoreBadgeValue.textContent = data.cro_score;
  overallConfidence.textContent = data.overall_confidence;

  renderScoreGrid(data.category_scores);
  renderCategoryConfidence(data.category_confidence);
  renderFixes(highPriorityFixes, data.high_priority_fixes, "high");
  renderFixes(mediumPriorityFixes, data.medium_priority_fixes, "medium");
  renderFixes(lowPriorityFixes, data.low_priority_fixes, "low");
  renderRewriteSuggestions(data.rewrite_suggestions);

  renderSimpleCards(
    abTestIdeas,
    data.ab_test_ideas,
    "hypothesis",
    (item) => `Variant: ${item.variant} Primary metric: ${item.primary_metric}`,
    "idea-card",
    "No A/B test ideas were generated for this audit."
  );

  renderSimpleCards(
    psychologicalImprovements,
    data.psychological_improvements,
    "principle",
    "suggestion",
    "insight-card",
    "No additional psychological improvements were identified."
  );

  renderSimpleCards(
    mobileImprovements,
    data.mobile_specific_improvements.map((suggestion) => ({
      title: "Mobile recommendation",
      body: suggestion,
    })),
    "title",
    "body",
    "mobile-card",
    "No mobile-specific improvements were flagged."
  );

  renderSimpleCards(
    missingEvidenceNotes,
    data.missing_evidence_notes.map((note) => ({
      title: "Evidence gap",
      body: note,
    })),
    "title",
    "body",
    "insight-card",
    "Everything important was visible in the supplied input."
  );

  renderSimpleCards(
    recommendedNextUploads,
    data.recommended_next_uploads.map((note) => ({
      title: "Recommended upload",
      body: note,
    })),
    "title",
    "body",
    "mobile-card",
    "No extra screenshot is required for this audit."
  );

  renderSimpleCards(
    analysisNotes,
    data.analysis_notes.map((note) => ({
      title: "Analysis note",
      body: note,
    })),
    "title",
    "body",
    "idea-card",
    "No extra analysis notes."
  );
}

screenshotInput.addEventListener("change", () => {
  const file = screenshotInput.files?.[0];
  if (!file) {
    screenshotPreview.classList.add("hidden");
    previewImage.removeAttribute("src");
    return;
  }

  const objectUrl = URL.createObjectURL(file);
  previewImage.src = objectUrl;
  screenshotPreview.classList.remove("hidden");
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const storeUrl = document.getElementById("store_url").value.trim();
  const productPageHtml = document.getElementById("product_page_html").value.trim();
  const basePayload = {
    product_price: Number(document.getElementById("product_price").value),
    target_audience: document.getElementById("target_audience").value.trim(),
    traffic_source: document.getElementById("traffic_source").value.trim(),
    device_focus: document.getElementById("device_focus").value.trim(),
  };
  const screenshotFile = screenshotInput.files?.[0];

  submitButton.disabled = true;
  setStatus("Running audit...");

  try {
    let response;

    if (screenshotFile) {
      const formData = new FormData();
      formData.append("screenshot", screenshotFile);
      formData.append("product_price", String(basePayload.product_price));
      formData.append("target_audience", basePayload.target_audience);
      formData.append("traffic_source", basePayload.traffic_source);
      formData.append("device_focus", basePayload.device_focus);
      formData.append("store_url", storeUrl);
      formData.append("product_page_html", productPageHtml);
      formData.append("save_image", document.getElementById("save_image").checked ? "true" : "false");

      response = await fetch("/api/v1/cro/audit-image", {
        method: "POST",
        body: formData,
      });
    } else if (storeUrl || productPageHtml) {
      response = await fetch("/api/v1/cro/audit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          store_url: storeUrl,
          product_page_html: productPageHtml || null,
          ...basePayload,
        }),
      });
    } else {
      throw new Error("Upload a screenshot or provide advanced fallback input.");
    }

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `Request failed with status ${response.status}.`);
    }

    const data = await response.json();
    renderResults(data);
    setStatus("Audit complete.");
  } catch (error) {
    const message = error instanceof Error ? error.message : "Something went wrong while running the audit.";
    setStatus(message, true);
  } finally {
    submitButton.disabled = false;
  }
});
