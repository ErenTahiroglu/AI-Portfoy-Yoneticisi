// ==============================================================================
// AI PORTFOLIO MANAGER - FRONTEND LOGIC
// ==============================================================================

document.addEventListener('DOMContentLoaded', () => {

    // ==========================================
    // 1. CONSTANTS & CONFIGURATION
    // ==========================================
    // Empty string since frontend is now served directly from the same FastAPI backend
    const API_BASE_URL = '';

    // ==========================================
    // 2. DOM ELEMENTS (CACHED)
    // ==========================================

    // Settings & Controls
    const useAIToggle = document.getElementById('use-ai-toggle');
    const checkIslamicToggle = document.getElementById('check-islamic-toggle');
    const checkFinancialsToggle = document.getElementById('check-financials-toggle');
    const aiSettingsPanel = document.getElementById('ai-settings-panel');
    const apiKeyInput = document.getElementById('api-key');
    const avApiKeyInput = document.getElementById('av-api-key');
    const aiModelSelect = document.getElementById('ai-model');

    // Inputs (File & Text)
    const fileDropArea = document.getElementById('file-drop-area');
    const fileInput = document.getElementById('portfolio-file');
    const fileNameDisplay = document.getElementById('file-name-display');
    const tickersInput = document.getElementById('tickers-input');
    const analyzeBtn = document.getElementById('analyze-btn');

    // UI States & Results Output
    const loaderContainer = document.getElementById('loader-container');
    const loaderText = document.getElementById('loader-text');
    const resultsSection = document.getElementById('results-section');
    const resultsContainer = document.getElementById('results-container');
    const summaryTableBody = document.getElementById('summary-table-body');
    const template = document.getElementById('result-card-template');


    // ==========================================
    // 3. EVENT LISTENERS
    // ==========================================

    // Toggle AI Settings visibility dynamically
    useAIToggle.addEventListener('change', (e) => {
        aiSettingsPanel.classList.toggle('hidden', !e.target.checked);
    });

    // File Drag & Drop Handlers
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, () => fileDropArea.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, () => fileDropArea.classList.remove('dragover'), false);
    });

    fileDropArea.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length) {
            fileInput.files = files;
            updateFileNameDisplay(files[0].name);
        }
    });

    fileInput.addEventListener('change', function () {
        if (this.files && this.files.length > 0) {
            updateFileNameDisplay(this.files[0].name);
        }
    });

    // Main Analysis Trigger
    analyzeBtn.addEventListener('click', handleAnalysisRequest);

    // Enter key triggers analysis from the tickers input
    tickersInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleAnalysisRequest();
        }
    });


    // ==========================================
    // 4. UI HANDLERS & HELPERS
    // ==========================================

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function updateFileNameDisplay(name) {
        fileNameDisplay.textContent = `Seçilen dosya: ${name}`;
    }

    function showLoader(message) {
        resultsSection.classList.add('hidden');
        loaderContainer.classList.remove('hidden');
        loaderText.textContent = message;
    }

    function hideLoader() {
        loaderContainer.classList.add('hidden');
    }

    // ==========================================
    // 5. CORE BUSINESS LOGIC & API INTEGRATION
    // ==========================================

    async function handleAnalysisRequest() {
        const textValue = tickersInput.value.trim();
        const fileValue = fileInput.files[0];
        const useAI = useAIToggle.checked;
        const checkIslamic = checkIslamicToggle.checked;
        const checkFinancials = checkFinancialsToggle.checked;
        const apiKey = apiKeyInput.value.trim();
        const avApiKey = avApiKeyInput.value.trim();
        const model = aiModelSelect.value;

        // Validation Checks
        if (!textValue && !fileValue) {
            alert("Lütfen en az bir hisse sembolü girin veya dosya yükleyin.");
            return;
        }

        if (!checkIslamic && !checkFinancials) {
            alert("Lütfen en az bir analiz türü seçin (İslami veya Finansal).");
            return;
        }

        if (useAI && !apiKey) {
            alert("Lütfen AI yorumları için Gemini API anahtarınızı girin.");
            return;
        }

        // Initialize UI State
        showLoader(fileValue ? "Dosya işleniyor..." : "Veriler analiz ediliyor...");

        try {
            let response;

            // Branch API request based on input type (File vs Text)
            if (fileValue) {
                const formData = new FormData();
                formData.append("file", fileValue);
                formData.append("use_ai", useAI);
                formData.append("check_islamic", checkIslamic);
                formData.append("check_financials", checkFinancials);
                formData.append("model", model);
                if (useAI && apiKey) formData.append("api_key", apiKey);
                if (avApiKey) formData.append("av_api_key", avApiKey);

                response = await fetch(`${API_BASE_URL}/api/analyze/file`, {
                    method: 'POST',
                    body: formData
                });
            } else {
                const payload = {
                    text: textValue,
                    use_ai: useAI,
                    check_islamic: checkIslamic,
                    check_financials: checkFinancials,
                    model: model,
                    api_key: apiKey,
                    av_api_key: avApiKey
                };

                response = await fetch(`${API_BASE_URL}/api/analyze/text`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }

            // Handle Response
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Bir hata oluştu");
            }

            const data = await response.json();
            renderResults(data.results);

        } catch (error) {
            console.error(error);
            alert(`Hata: ${error.message}`);
        } finally {
            hideLoader();
        }
    }

    // ==========================================
    // 6. RENDER LOGIC
    // ==========================================

    function renderResults(results) {
        resultsContainer.innerHTML = '';
        summaryTableBody.innerHTML = '';

        if (!results || results.length === 0) {
            alert("Analiz edilecek sonuç bulunamadı.");
            return;
        }

        results.forEach(res => {
            // Show error results as a simple error card instead of silently skipping
            if (res.error && !res.financials && !res.fin_error) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'result-card';
                errorDiv.innerHTML = `
                    <div class="card-header">
                        <h3 class="ticker-name">${res.ticker}</h3>
                        <span class="status-badge status-rejected">Hata</span>
                    </div>
                    <div class="ai-comment-section">
                        <h4><i class="fa-solid fa-triangle-exclamation"></i> Analiz Hatası</h4>
                        <div class="ai-content"><p style="color:#f87171;">${res.error}</p></div>
                    </div>`;
                resultsContainer.appendChild(errorDiv);
                return;
            }

            const cardClone = template.content.cloneNode(true);
            const currencySymbol = res.market === 'TR' ? '₺' : '$';

            // Set Header
            cardClone.querySelector('.ticker-name').textContent = res.ticker;

            // 6.1. Render Islamic Metrics
            const islamicMetrics = cardClone.querySelector('.islamic-metrics-grid');
            const statusBadge = cardClone.querySelector('.status-badge');
            let isHalal = false;

            if (res.status) {
                statusBadge.textContent = res.status;
                if (res.status === 'Uygun' || res.status === 'Katılım Fonu (Uygun)') {
                    isHalal = true;
                } else {
                    statusBadge.classList.replace('status-approved', 'status-rejected');
                }

                if (res.is_tefas) {
                    // TEFAS Fund: hide ratios, show fund note
                    if (islamicMetrics) islamicMetrics.style.display = 'none';
                    // Add fund note after header
                    const noteDiv = document.createElement('div');
                    noteDiv.style.cssText = 'padding: 0.75rem 1rem; font-size: 0.85rem; line-height: 1.5; color: var(--text-secondary); border-bottom: 1px solid var(--glass-border);';
                    noteDiv.innerHTML = res.fund_note || '';
                    const cardHeader = cardClone.querySelector('.card-header');
                    if (cardHeader) cardHeader.after(noteDiv);
                } else {
                    // Stock/ETF: show full metrics
                    const debtRatioElem = cardClone.querySelector('.debt-ratio');
                    debtRatioElem.textContent = `%${res.debt_ratio.toFixed(2)}`;
                    if (res.debt_ratio > 30) debtRatioElem.classList.add('danger');

                    const purRatioElem = cardClone.querySelector('.pur-ratio');
                    purRatioElem.textContent = `%${res.purification_ratio.toFixed(2)}`;
                    if (res.purification_ratio > 5) purRatioElem.classList.add('danger');

                    cardClone.querySelector('.interest-val').textContent = (res.interest !== null && res.interest !== undefined) ? `${currencySymbol}${res.interest.toLocaleString(undefined, { maximumFractionDigits: 0 })}` : 'Veri Yok';
                    cardClone.querySelector('.is-etf').textContent = res.is_etf ? 'ETF/Fon' : 'Hisse';
                }

            } else {
                if (islamicMetrics) islamicMetrics.style.display = 'none';
                if (statusBadge) statusBadge.style.display = 'none';
            }

            // 6.2. Render Financial Metrics
            const finMetrics = cardClone.querySelector('.financial-metrics-grid');
            if (finMetrics) {
                if (res.financials) {
                    finMetrics.style.display = 'grid';
                    const fin = res.financials;

                    cardClone.querySelector('.fin-5y-real').textContent = fin.s5 !== null ? `%${fin.s5.toFixed(2)}` : 'Veri Yok';
                    cardClone.querySelector('.fin-3y-real').textContent = fin.s3 !== null ? `%${fin.s3.toFixed(2)}` : 'Veri Yok';

                    let div = 'Yok';
                    if (fin.yt) {
                        const years = Object.keys(fin.yt).sort((a, b) => b - a);
                        if (years.length > 0) div = `%${fin.yt[years[0]].toFixed(2)}`;
                    }
                    cardClone.querySelector('.fin-div').textContent = div;
                    cardClone.querySelector('.fin-status').textContent = "Başarılı";

                    // 6.2.1. Render Multi-Period Returns Table
                    if (fin.ay && Object.keys(fin.ay).length > 0) {
                        const periodSection = document.createElement('div');
                        periodSection.style.cssText = 'padding: 0.75rem 1rem; border-top: 1px solid var(--glass-border); overflow-x: auto;';

                        const periodLabels = {
                            1: '1 Ay', 2: '2 Ay', 3: '3 Ay', 4: '4 Ay', 5: '5 Ay',
                            6: '6 Ay', 9: '9 Ay', 12: '1 Yıl', 24: '2 Yıl',
                            36: '3 Yıl', 60: '5 Yıl', 120: '10 Yıl'
                        };

                        let tableHTML = `<h4 style="margin:0 0 0.5rem 0;font-size:0.85rem;color:var(--text-secondary);">📊 Dönemsel Getiri Analizi</h4>`;
                        tableHTML += `<table style="width:100%;border-collapse:collapse;font-size:0.75rem;">`;
                        tableHTML += `<tr style="border-bottom:1px solid var(--glass-border);">
                            <th style="text-align:left;padding:4px 6px;color:var(--text-secondary);">Dönem</th>
                            <th style="text-align:right;padding:4px 6px;color:var(--text-secondary);">Nominal</th>
                            <th style="text-align:right;padding:4px 6px;color:var(--text-secondary);">Reel</th>
                            <th style="text-align:right;padding:4px 6px;color:var(--text-secondary);">Enflasyon</th>
                        </tr>`;

                        const periods = Object.keys(fin.ay).map(Number).sort((a, b) => a - b);
                        for (const p of periods) {
                            const d = fin.ay[p];
                            const label = periodLabels[p] || `${p} Ay`;
                            const nomColor = d.g >= 0 ? '#4ade80' : '#f87171';
                            const realColor = d.r >= 0 ? '#4ade80' : '#f87171';
                            tableHTML += `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                                <td style="padding:3px 6px;color:var(--text-primary);">${label}</td>
                                <td style="padding:3px 6px;text-align:right;color:${nomColor};">${d.g >= 0 ? '+' : ''}${d.g.toFixed(2)}%</td>
                                <td style="padding:3px 6px;text-align:right;color:${realColor};">${d.r >= 0 ? '+' : ''}${d.r.toFixed(2)}%</td>
                                <td style="padding:3px 6px;text-align:right;color:var(--text-secondary);">${d.enf >= 0 ? '+' : ''}${d.enf.toFixed(2)}%</td>
                            </tr>`;
                        }
                        tableHTML += `</table>`;
                        periodSection.innerHTML = tableHTML;

                        // Get the card element and append
                        const cardEl = cardClone.querySelector('.result-card');
                        if (cardEl) cardEl.appendChild(periodSection);
                    }

                } else if (res.fin_error) {
                    finMetrics.style.display = 'grid';
                    cardClone.querySelector('.fin-status').textContent = res.fin_error;
                    cardClone.querySelector('.fin-5y-real').textContent = 'Hata';
                    cardClone.querySelector('.fin-3y-real').textContent = 'Hata';
                    cardClone.querySelector('.fin-div').textContent = 'Hata';
                }
            }

            // 6.3. Render AI Comments
            const aiContentObj = cardClone.querySelector('.ai-content');
            if (res.ai_comment) {
                if (typeof marked !== 'undefined') {
                    aiContentObj.innerHTML = marked.parse(res.ai_comment);
                } else {
                    aiContentObj.textContent = res.ai_comment;
                }
            } else {
                aiContentObj.innerHTML = "<em>AI Yorumu istenmedi veya üretilemedi.</em>";
            }

            resultsContainer.appendChild(cardClone);

            // 6.4. Render Summary Table Row
            let rowHtml = `<td><strong>${res.ticker}</strong> ${res.is_etf ? '<small class="text-muted">(Fon)</small>' : ''}</td>`;

            if (res.status) {
                if (res.is_tefas) {
                    rowHtml += `
                        <td>-</td>
                        <td>-</td>
                        <td><span class="status-badge ${isHalal ? 'status-approved' : 'status-rejected'}">${res.status}</span></td>
                    `;
                } else {
                    rowHtml += `
                        <td class="${res.purification_ratio > 5 ? 'metric-value danger' : ''}">%${res.purification_ratio.toFixed(2)}</td>
                        <td class="${res.debt_ratio > 30 ? 'metric-value danger' : ''}">%${res.debt_ratio.toFixed(2)}</td>
                        <td><span class="status-badge ${isHalal ? 'status-approved' : 'status-rejected'}">${res.status}</span></td>
                    `;
                }
            } else {
                rowHtml += `<td>-</td><td>-</td><td>-</td>`;
            }

            if (res.financials) {
                let y5 = res.financials.s5 !== null ? `%${res.financials.s5.toFixed(2)}` : '-';
                let div = '-';
                if (res.financials.yt) {
                    const years = Object.keys(res.financials.yt).sort((a, b) => b - a);
                    if (years.length > 0) div = `%${res.financials.yt[years[0]].toFixed(2)}`;
                }
                rowHtml += `<td>${y5}</td><td>${div}</td>`;
            } else {
                rowHtml += `<td>${res.fin_error || '-'}</td><td>-</td>`;
            }

            const tr = document.createElement('tr');
            tr.innerHTML = rowHtml;
            summaryTableBody.appendChild(tr);
        });

        // Show Results Area
        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
});
