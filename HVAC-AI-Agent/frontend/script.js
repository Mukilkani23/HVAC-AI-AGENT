/* ═══════════════════════════════════════════════════════════════
   HVAC AI Agent v2.0 – Frontend Logic
   Pipeline · Report · Analytics · History · Comparison · Charts
   ═══════════════════════════════════════════════════════════════ */

const API_BASE = window.location.origin;
const AGENTS = ['location', 'weather', 'forecast', 'diagnostic', 'ai', 'report'];

/* ── Pipeline Animation ──────────────────────────────────────── */

function resetPipeline() {
    AGENTS.forEach(id => {
        const el = document.querySelector(`.pipeline__agent[data-agent="${id}"]`);
        if (el) el.classList.remove('active', 'done');
        const st = document.getElementById(`status-${id}`);
        if (st) st.textContent = 'Idle';
    });
    document.querySelectorAll('.pipeline__connector').forEach(c => c.classList.remove('done'));
}

function activateAgent(index) {
    return new Promise(resolve => {
        const id = AGENTS[index];
        const el = document.querySelector(`.pipeline__agent[data-agent="${id}"]`);
        const st = document.getElementById(`status-${id}`);
        if (el) el.classList.add('active');
        if (st) st.textContent = 'Running…';
        setTimeout(() => {
            if (el) { el.classList.remove('active'); el.classList.add('done'); }
            if (st) st.textContent = '✓ Done';
            const connectors = document.querySelectorAll('.pipeline__connector');
            if (index < connectors.length) connectors[index].classList.add('done');
            resolve();
        }, 500);
    });
}

async function animatePipeline() {
    for (let i = 0; i < AGENTS.length; i++) await activateAgent(i);
}

/* ── Badge Helpers ───────────────────────────────────────────── */

function effBadge(status) {
    if (!status) return '<span class="badge badge--blue">Unknown</span>';
    const s = status.toLowerCase();
    if (s.includes('optimal') || s.includes('excellent')) return `<span class="badge badge--green">${status}</span>`;
    if (s.includes('acceptable') || s.includes('good')) return `<span class="badge badge--green">${status}</span>`;
    if (s.includes('degradation') || s.includes('moderate')) return `<span class="badge badge--amber">${status}</span>`;
    return `<span class="badge badge--red">${status}</span>`;
}

function priorityBadge(priority) {
    if (!priority) return '';
    const p = priority.toLowerCase();
    if (p.startsWith('low')) return `<span class="badge badge--green">${priority}</span>`;
    if (p.startsWith('medium')) return `<span class="badge badge--amber">${priority}</span>`;
    return `<span class="badge badge--red">${priority}</span>`;
}

function impactBadge(level) {
    if (!level) return '';
    const l = level.toLowerCase();
    if (l === 'low') return '<span class="badge badge--green">LOW</span>';
    if (l === 'moderate') return '<span class="badge badge--amber">MODERATE</span>';
    return '<span class="badge badge--red">HIGH</span>';
}

function healthBadge(status) {
    if (!status) return '';
    const s = status.toLowerCase();
    if (s === 'healthy') return '<span class="badge badge--green">Healthy</span>';
    if (s === 'warning') return '<span class="badge badge--amber">Warning</span>';
    return '<span class="badge badge--red">Critical</span>';
}

/* ── Main Generate ───────────────────────────────────────────── */

async function generateReport() {
    const btn = document.getElementById('generateBtn');
    const loader = document.getElementById('btnLoader');
    const panel = document.getElementById('reportPanel');

    const building = document.getElementById('building').value.trim();
    const buildingType = document.getElementById('buildingType').value;
    const address = document.getElementById('address').value.trim();
    const occupancy = document.getElementById('occupancy').value.trim();
    const temp = document.getElementById('temp').value.trim();
    const energy = document.getElementById('energy').value.trim();
    const ikwtr = document.getElementById('ikwtr').value.trim();

    const fields = [
        { val: building, id: 'building', name: 'Building Name' },
        { val: address, id: 'address', name: 'Address / City' },
        { val: occupancy, id: 'occupancy', name: 'Occupancy' },
        { val: temp, id: 'temp', name: 'Indoor Temperature' },
        { val: energy, id: 'energy', name: 'Energy Consumption' },
        { val: ikwtr, id: 'ikwtr', name: 'IKW/TR' },
    ];

    const emptyField = fields.find(f => !f.val);
    if (emptyField) {
        const el = document.getElementById(emptyField.id);
        el.focus();
        el.style.borderColor = '#ef4444';
        el.style.boxShadow = '0 0 0 3px rgba(239,68,68,0.15)';
        setTimeout(() => { el.style.borderColor = ''; el.style.boxShadow = ''; }, 2000);
        alert(`Please fill in "${emptyField.name}" before generating the report.`);
        return;
    }

    const data = {
        building, address, building_type: buildingType,
        occupancy: Number(occupancy),
        indoor_temp: Number(temp),
        energy_kwh: Number(energy),
        ikw_tr: Number(ikwtr),
    };

    btn.disabled = true;
    loader.classList.add('visible');
    panel.style.display = 'none';
    const backBtn = document.getElementById('backToHistoryBtn');
    if (backBtn) backBtn.style.display = 'none';
    resetPipeline();

    try {
        const [_, result] = await Promise.all([
            animatePipeline(),
            fetch(`${API_BASE}/ai/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            }).then(r => { if (!r.ok) throw new Error(`Server error ${r.status}`); return r.json(); }),
        ]);

        // Merge frontend input that backend might not have
        result.ikw_tr = data.ikw_tr;
        result.building_type = data.building_type;

        // Reveal Forecast Agent Extra Data in Pipeline
        const fcExtra = document.getElementById('forecast-extra');
        if (fcExtra) {
            fcExtra.style.display = 'block';
            document.getElementById('fc-load').textContent = result.cooling_load ?? result.predicted_cooling_load ?? '--';
            document.getElementById('fc-opt-bill').textContent = `₹${new Intl.NumberFormat('en-IN').format(result.monthly_bill_optimized || 0)}`;
            document.getElementById('fc-non-bill').textContent = `₹${new Intl.NumberFormat('en-IN').format(result.monthly_bill_non_optimized || 0)}`;
        }

        renderReport(result);
        panel.style.display = 'block';
        panel.scrollIntoView({ behavior: 'smooth', block: 'start' });

        await saveReportToHistory(result);
    } catch (err) {
        console.error(err);
        alert('Error generating report. Make sure the backend is running.\n\n' + err.message);
    } finally {
        btn.disabled = false;
        loader.classList.remove('visible');
    }
}

/* ── Efficiency Score Gauge ──────────────────────────────────── */

function renderEfficiencyGauge(score, status) {
    const pct = Math.min(100, Math.max(0, score || 50));
    let color = '#10b981';
    if (pct < 55) color = '#ef4444';
    else if (pct < 75) color = '#f59e0b';

    return `
    <div class="gauge-container">
        <div class="gauge-ring">
            <svg viewBox="0 0 120 120" class="gauge-svg">
                <circle cx="60" cy="60" r="52" stroke="#e5e7eb" stroke-width="10" fill="none"/>
                <circle cx="60" cy="60" r="52" stroke="${color}" stroke-width="10" fill="none"
                    stroke-dasharray="${pct * 3.267} 326.7"
                    stroke-dashoffset="0" stroke-linecap="round"
                    transform="rotate(-90 60 60)"
                    class="gauge-progress"/>
            </svg>
            <div class="gauge-value">${pct}</div>
        </div>
        <div class="gauge-label">HVAC Efficiency Score</div>
        <div class="gauge-status">${effBadge(status)}</div>
    </div>`;
}

/* ── Report Renderer (Professional Page – Feature 14) ────────── */

function renderReport(r) {
    const rid = document.getElementById('reportId');
    if (rid) rid.textContent = r.report_id || 'Report';

    // Extract stored intelligence (from saved report) or compute client-side
    const hvacEff = r.hvac_efficiency || _clientEfficiency(r.ikw_tr);
    const weatherImpact = r.weather_impact || _clientWeatherImpact(r.outdoor_temp, r.humidity);
    const systemHealth = r.system_health || _clientHealth(r);
    const aiExplanation = r.ai_explanation || [];
    const smartAlerts = r.smart_alerts || [];

    const content = document.getElementById('reportContent');
    content.innerHTML = `
        <!-- ── Smart Alerts ──────────────────────────────────── -->
        <div class="alert-strip" id="alertStrip">
            ${smartAlerts.map(a => `
                <div class="alert-item alert-item--${a.type}">
                    <span class="alert-item__icon">${a.type === 'success' ? '✅' : '⚠️'}</span>
                    <div class="alert-item__content">
                        <div class="alert-item__msg">${a.message}</div>
                        <div class="alert-item__action">→ ${a.action}</div>
                    </div>
                </div>
            `).join('')}
        </div>

        <!-- ── KPI + Gauge Row ───────────────────────────────── -->
        <div class="kpi-gauge-row">
            <div class="kpi-side">
                <div class="kpi-row">
                    <div class="kpi-card">
                        <div class="kpi-card__value">${r.cooling_load ?? r.predicted_cooling_load ?? '—'}<small> kW</small></div>
                        <div class="kpi-card__label">Cooling Load</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-card__value">${r.recommended_temp ?? r.recommended_temperature ?? '—'}<small>°C</small></div>
                        <div class="kpi-card__label">Recommended Temp</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-card__value">${r.energy_saving ?? r.energy_savings ?? '—'}</div>
                        <div class="kpi-card__label">Energy Savings</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-card__value">${r.efficiency_score ?? '—'}<small>%</small></div>
                        <div class="kpi-card__label">Efficiency Score</div>
                    </div>
                </div>
            </div>
            <div class="gauge-side">
                ${renderEfficiencyGauge(hvacEff.score, hvacEff.status)}
            </div>
        </div>

        <!-- ── Weather Impact + System Health ────────────────── -->
        <div class="intel-row">
            <div class="intel-card">
                <div class="intel-card__title">🌦 Weather Impact</div>
                <div class="intel-card__body">
                    <div class="report-row"><span class="report-row__label">Outdoor Temp</span><span class="report-row__value">${r.outdoor_temp ?? r.outdoor_temperature ?? '—'}°C</span></div>
                    <div class="report-row"><span class="report-row__label">Humidity</span><span class="report-row__value">${r.humidity ?? '—'}%</span></div>
                    <div class="report-row"><span class="report-row__label">Cooling Demand Impact</span><span class="report-row__value">${impactBadge(weatherImpact.level)}</span></div>
                </div>
                <div class="intel-card__desc">${weatherImpact.description || ''}</div>
            </div>
            <div class="intel-card">
                <div class="intel-card__title">${systemHealth.icon || '⚙'} System Health</div>
                <div class="intel-card__body">
                    <div class="report-row"><span class="report-row__label">Status</span><span class="report-row__value">${healthBadge(systemHealth.status)}</span></div>
                    <div class="report-row"><span class="report-row__label">Maintenance Required</span><span class="report-row__value">${systemHealth.maintenance_required ? '<span class="badge badge--red">Yes</span>' : '<span class="badge badge--green">No</span>'}</span></div>
                    <div class="report-row"><span class="report-row__label">Energy Efficiency</span><span class="report-row__value">${systemHealth.energy_efficiency || '—'}</span></div>
                </div>
            </div>
        </div>

        <!-- ── Detail Sections ───────────────────────────────── -->
        <div class="report-grid">
            <div class="report-section">
                <div class="report-section__title">📍 Building & Location</div>
                <div class="report-row"><span class="report-row__label">Building</span><span class="report-row__value">${r.building ?? r.building_name ?? ''}</span></div>
                <div class="report-row"><span class="report-row__label">Type</span><span class="report-row__value">${(r.building_type || 'office').charAt(0).toUpperCase() + (r.building_type || 'office').slice(1)}</span></div>
                <div class="report-row"><span class="report-row__label">Address</span><span class="report-row__value" style="font-size:0.85em;max-width:60%;text-align:right;">${r.formatted_address || r.address || ''}</span></div>
                <div class="report-row"><span class="report-row__label">Climate Zone</span><span class="report-row__value">${r.climate_zone || '—'}</span></div>
                <div class="report-row"><span class="report-row__label">Coordinates</span><span class="report-row__value">${r.lat ?? r.latitude ?? ''}, ${r.lon ?? r.longitude ?? ''}</span></div>
                <div class="report-row"><span class="report-row__label">Occupancy</span><span class="report-row__value">${r.input_occupancy ?? r.occupancy ?? '—'}</span></div>
                <div class="report-row"><span class="report-row__label">Indoor Temp</span><span class="report-row__value">${r.input_indoor_temp ?? r.indoor_temperature ?? '—'}°C</span></div>
            </div>
            <div class="report-section">
                <div class="report-section__title">📊 Cooling Forecast</div>
                <div class="report-row"><span class="report-row__label">Cooling Load</span><span class="report-row__value">${r.cooling_load ?? r.predicted_cooling_load ?? ''} kW</span></div>
                <div class="report-row"><span class="report-row__label">Cooling (TR)</span><span class="report-row__value">${r.cooling_load_tr ?? ''} TR</span></div>
                <div class="report-row"><span class="report-row__label">Peak Load</span><span class="report-row__value">${r.peak_load ?? ''} kW</span></div>
                <div class="report-row"><span class="report-row__label">Predicted Monthly</span><span class="report-row__value">${r.predicted_monthly_kwh ?? ''} kWh</span></div>
                <div class="report-row"><span class="report-row__label">Wind Speed</span><span class="report-row__value">${r.wind_speed ?? ''} km/h</span></div>
                <div class="report-row"><span class="report-row__label">Condition</span><span class="report-row__value">${r.weather_condition ?? ''}</span></div>
            </div>
            <div class="report-section" style="grid-column: 1 / -1;">
                <div class="report-section__title">💰 Monthly Electricity Cost Comparison</div>
                <div class="report-row"><span class="report-row__label">Non Optimized Cost</span><span class="report-row__value">₹${new Intl.NumberFormat('en-IN').format(r.monthly_bill_non_optimized || 0)}</span></div>
                <div class="report-row"><span class="report-row__label">Optimized Cost</span><span class="report-row__value">₹${new Intl.NumberFormat('en-IN').format(r.monthly_bill_optimized || 0)}</span></div>
                <div class="report-row" style="margin-top: 10px; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 10px;">
                    <span class="report-row__label" style="color:#10b981; font-weight:bold;">Estimated Monthly Savings</span>
                    <span class="report-row__value" style="color:#10b981; font-weight:bold; font-size:1.1em;">₹${new Intl.NumberFormat('en-IN').format(r.estimated_monthly_savings_currency || 0)}</span>
                </div>
            </div>
        </div>

        <!-- ── Faults ────────────────────────────────────────── -->
        ${r.faults && r.faults.length ? `
        <div style="margin-bottom:20px;">
            <div class="report-section__title" style="margin-bottom:10px;">⚠ Detected Issues</div>
            ${r.faults.map(f => `<div class="fault-item">⚠ ${f}</div>`).join('')}
        </div>` : ''}

        <!-- ── AI Recommendations ────────────────────────────── -->
        <div style="margin-bottom:20px;">
            <div class="report-section__title" style="margin-bottom:10px;">🧠 AI Recommendations</div>
            <div style="margin-bottom:10px;">${priorityBadge(r.priority)}</div>
            <ul class="actions-list">
                ${(r.actions || []).map(a => `<li>${a}</li>`).join('')}
            </ul>
        </div>

        <!-- ── AI Decision Explanation ────────────────────────── -->
        ${aiExplanation.length ? `
        <div class="ai-explanation">
            <div class="report-section__title" style="margin-bottom:10px;">🔬 AI Decision Explanation</div>
            <div class="explanation-steps">
                ${aiExplanation.map((step, i) => `
                    <div class="explanation-step">
                        <div class="explanation-step__num">${i + 1}</div>
                        <div class="explanation-step__text">${step}</div>
                    </div>
                `).join('')}
            </div>
        </div>` : ''}
    `;
}

/* ── Client-side intelligence fallbacks ──────────────────────── */

function _clientEfficiency(ikw) {
    if (!ikw) return { score: 50, status: 'Unknown' };
    ikw = parseFloat(ikw);
    if (ikw < 1.1) return { score: 90, status: 'Excellent' };
    if (ikw <= 1.3) return { score: 76, status: 'Good' };
    if (ikw <= 1.5) return { score: 60, status: 'Moderate' };
    return { score: 40, status: 'Poor' };
}

function _clientWeatherImpact(temp, hum) {
    temp = parseFloat(temp) || 25;
    hum = parseFloat(hum) || 50;
    if (temp > 34 || (temp > 32 && hum > 70)) return { level: 'HIGH', description: 'Extreme conditions' };
    if (temp >= 30) return { level: 'MODERATE', description: 'Warm conditions' };
    return { level: 'LOW', description: 'Mild conditions' };
}

function _clientHealth(r) {
    const score = parseFloat(r.efficiency_score) || 50;
    const faults = (r.faults || []).length;
    if (score >= 75 && faults === 0) return { status: 'Healthy', maintenance_required: false, energy_efficiency: 'Good', icon: '✅' };
    if (score >= 55) return { status: 'Warning', maintenance_required: faults > 0, energy_efficiency: 'Moderate', icon: '⚠️' };
    return { status: 'Critical', maintenance_required: true, energy_efficiency: 'Poor', icon: '🔴' };
}



/* ═══════════════════════════════════════════════════════════════
   REPORT HISTORY
   ═══════════════════════════════════════════════════════════════ */

async function saveReportToHistory(reportData) {
    try {
        const res = await fetch(`${API_BASE}/reports/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(reportData),
        });
        if (!res.ok) { console.warn('Save failed'); return; }
        await loadReportHistory();
        await loadAnalytics();
    } catch (err) { console.warn('Save error:', err); }
}

async function loadReportHistory() {
    try {
        const res = await fetch(`${API_BASE}/reports`);
        if (!res.ok) return;
        const data = await res.json();
        const reports = data.reports || [];
        const total = data.total_reports || reports.length;

        document.getElementById('totalReportCount').textContent = total;
        const badge = document.getElementById('historyCount');
        if (badge) badge.textContent = `${total} Report${total !== 1 ? 's' : ''}`;

        const clearBtn = document.getElementById('clearAllBtn');
        if (clearBtn) clearBtn.style.display = total > 0 ? 'inline-flex' : 'none';
        const cmpBtn = document.getElementById('compareBtn');
        if (cmpBtn) cmpBtn.style.display = total >= 2 ? 'inline-flex' : 'none';

        renderHistoryList(reports);
    } catch (err) { console.warn('History load error:', err); }
}

function renderHistoryList(reports) {
    const container = document.getElementById('historyList');
    if (!reports || reports.length === 0) {
        container.innerHTML = `
            <div class="history-empty"><div class="history-empty__icon">📭</div>
            <p class="history-empty__text">No reports generated yet</p>
            <p class="history-empty__hint">Click "Generate Report" to create your first HVAC analysis</p></div>`;
        return;
    }
    const sorted = [...reports].sort((a, b) => b.report_id - a.report_id);
    container.innerHTML = sorted.map(r => `
        <div class="history-item" id="history-item-${r.report_id}">
            <div class="history-item__clickable" onclick="viewHistoryReport(${r.report_id})">
                <div class="history-item__icon">📄</div>
                <div class="history-item__info">
                    <div class="history-item__title">Report #${r.report_id} – ${r.building || 'Unknown'}</div>
                    <div class="history-item__meta">
                        <span class="history-item__building">${r.address || ''}</span>
                        <span class="history-item__separator">·</span>
                        <span class="history-item__time-inline">${r.timestamp_short || r.timestamp || ''}</span>
                        ${r.system_status ? `<span class="history-item__separator">·</span>${healthBadge(r.system_status)}` : ''}
                    </div>
                </div>
            </div>
            <div class="history-item__actions">
                <button class="btn-delete-report" onclick="deleteReport(${r.report_id}, event)" title="Delete">🗑</button>
                <div class="history-item__arrow">→</div>
            </div>
        </div>
    `).join('');
}

async function viewHistoryReport(reportId) {
    const panel = document.getElementById('reportPanel');
    const backBtn = document.getElementById('backToHistoryBtn');
    try {
        document.querySelectorAll('.history-item').forEach(el => el.classList.remove('history-item--active'));
        const item = document.getElementById(`history-item-${reportId}`);
        if (item) item.classList.add('history-item--active');

        const res = await fetch(`${API_BASE}/reports/${reportId}`);
        if (!res.ok) { alert('Could not load report.'); return; }
        const data = await res.json();
        if (data.error) { alert(data.error); return; }

        const reportData = data.full_report || data;
        reportData.report_id = `Report #${data.report_id}`;

        // Carry over stored intelligence
        reportData.hvac_efficiency = data.hvac_efficiency;
        reportData.weather_impact = data.weather_impact;
        reportData.system_health = data.system_health;
        reportData.ai_explanation = data.ai_explanation;
        reportData.smart_alerts = data.smart_alerts;

        renderReport(reportData);
        panel.style.display = 'block';
        if (backBtn) backBtn.style.display = 'inline-flex';
        panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) { console.error(err); alert('Error loading report.'); }
}

async function deleteReport(reportId, event) {
    if (event) event.stopPropagation();
    if (!confirm(`Delete Report #${reportId}?`)) return;
    try {
        const res = await fetch(`${API_BASE}/reports/${reportId}`, { method: 'DELETE' });
        if (!res.ok) { alert('Delete failed.'); return; }
        const item = document.getElementById(`history-item-${reportId}`);
        if (item) {
            item.style.transition = 'all 0.3s ease';
            item.style.opacity = '0';
            item.style.transform = 'translateX(30px)';
            setTimeout(() => { item.style.maxHeight = '0'; item.style.padding = '0'; item.style.marginBottom = '0'; item.style.overflow = 'hidden'; }, 200);
            setTimeout(() => { loadReportHistory(); loadAnalytics(); }, 500);
        } else { await loadReportHistory(); await loadAnalytics(); }
    } catch (err) { console.error(err); alert('Error deleting report.'); }
}

async function clearAllReports() {
    if (!confirm('Delete ALL reports?\n\nThis action cannot be undone.')) return;
    try {
        await fetch(`${API_BASE}/reports`, { method: 'DELETE' });
        document.getElementById('reportPanel').style.display = 'none';
        await loadReportHistory();
        await loadAnalytics();
    } catch (err) { console.error(err); alert('Error clearing reports.'); }
}

function scrollToHistory() {
    document.getElementById('historyPanel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}


/* ═══════════════════════════════════════════════════════════════
   ANALYTICS DASHBOARD
   ═══════════════════════════════════════════════════════════════ */

async function loadAnalytics() {
    try {
        const res = await fetch(`${API_BASE}/reports/analytics`);
        if (!res.ok) return;
        const d = await res.json();
        document.getElementById('anTotalReports').textContent = d.total_reports || 0;
        document.getElementById('anAvgCooling').textContent = `${d.avg_cooling_load || 0} kW`;
        document.getElementById('anAvgTemp').textContent = `${d.avg_recommended_temp || 0}°C`;
        document.getElementById('anEnergySaved').textContent = d.total_energy_saved || '0%';
    } catch (err) { console.warn('Analytics load error:', err); }
}


/* ═══════════════════════════════════════════════════════════════
   REPORT COMPARISON
   ═══════════════════════════════════════════════════════════════ */

async function openCompareModal() {
    const panel = document.getElementById('comparisonPanel');
    panel.style.display = 'block';
    panel.scrollIntoView({ behavior: 'smooth' });

    try {
        const res = await fetch(`${API_BASE}/reports`);
        if (!res.ok) return;
        const data = await res.json();
        const reports = data.reports || [];

        const opts = reports.map(r => `<option value="${r.report_id}">Report #${r.report_id} – ${r.building}</option>`).join('');
        document.getElementById('compareA').innerHTML = '<option value="">Select Report A</option>' + opts;
        document.getElementById('compareB').innerHTML = '<option value="">Select Report B</option>' + opts;
        document.getElementById('comparisonResult').innerHTML = '';
    } catch (err) { console.error(err); }
}

async function runComparison() {
    const idA = document.getElementById('compareA').value;
    const idB = document.getElementById('compareB').value;
    if (!idA || !idB) { alert('Select two reports to compare.'); return; }
    if (idA === idB) { alert('Select two different reports.'); return; }

    try {
        const res = await fetch(`${API_BASE}/reports/compare/${idA}/${idB}`);
        if (!res.ok) { alert('Comparison failed.'); return; }
        const c = await res.json();
        if (c.error) { alert(c.error); return; }

        const resultDiv = document.getElementById('comparisonResult');
        resultDiv.innerHTML = `
            <div class="compare-header">
                <div class="compare-col"><strong>Report #${c.report_a_id}</strong><br>${c.report_a_building}</div>
                <div class="compare-col compare-col--vs">VS</div>
                <div class="compare-col"><strong>Report #${c.report_b_id}</strong><br>${c.report_b_building}</div>
            </div>
            ${renderCompareRow('Cooling Load (kW)', c.cooling_load)}
            ${renderCompareRow('Recommended Temp (°C)', c.recommended_temp)}
            ${renderCompareRow('Energy Savings', c.energy_savings)}
            ${renderCompareRow('Efficiency Score', c.efficiency_score)}
            ${renderCompareRow('Outdoor Temp (°C)', c.outdoor_temperature)}
            ${renderCompareRow('Humidity (%)', c.humidity)}
        `;
    } catch (err) { console.error(err); alert('Comparison error.'); }
}

function renderCompareRow(label, data) {
    if (!data) return '';
    const diff = data.difference;
    let diffClass = '';
    let diffText = diff;
    if (typeof diff === 'number') {
        diffClass = diff > 0 ? 'compare-diff--up' : diff < 0 ? 'compare-diff--down' : '';
        diffText = diff > 0 ? `+${diff}` : diff;
    }
    return `
    <div class="compare-row">
        <div class="compare-row__label">${label}</div>
        <div class="compare-row__val">${data.report_a ?? '—'}</div>
        <div class="compare-row__diff ${diffClass}">${diffText}</div>
        <div class="compare-row__val">${data.report_b ?? '—'}</div>
    </div>`;
}


/* ── Init ────────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
    loadReportHistory();
    loadAnalytics();
});
