import React from 'react';
import './Profile360Modal.css';

function Profile360Modal({ profile, monthlyArpu, onClose }) {
  if (!profile || !profile.profile) return null;

  const p = profile.profile; // Shorthand
  const months = profile.monthly_arpu || [];

  const formatNumber = (num) => {
    if (!num && num !== 0) return '0';
    return new Intl.NumberFormat('vi-VN').format(Math.round(num));
  };

  const formatCurrency = (num) => {
    if (!num && num !== 0) return '0 đ';
    return formatNumber(num) + ' đ';
  };

  const formatServiceType = (serviceType) => {
    const map = { 'EasyCredit': 'Fee', 'MBFG': 'Free', 'ungsanluong': 'Quota' };
    return map[serviceType] || serviceType;
  };

  const getServiceBadgeClass = (serviceType) => {
    if (serviceType === 'EasyCredit') return 'service-badge-fee';
    if (serviceType === 'MBFG') return 'service-badge-free';
    return 'service-badge-quota';
  };

  const getRiskBadgeClass = (risk) => {
    if (risk === 'LOW') return 'risk-badge-low';
    if (risk === 'MEDIUM') return 'risk-badge-medium';
    return 'risk-badge-high';
  };

  // Calculate max ARPU for chart scaling
  const maxARPU = months.length > 0 ? Math.max(...months.map(m => m.arpu_total)) : 1;

  return (
    <div className="modal-overlay-360" onClick={onClose}>
      <div className="modal-content-360" onClick={(e) => e.stopPropagation()}>
        {/* HEADER */}
        <div className="modal-header-360">
          <h2>🎯 Customer360-VNS</h2>
          <button className="btn-close-360" onClick={onClose}>×</button>
        </div>

        <div className="modal-body-360">
          {/* 1. OVERVIEW CARDS */}
          <div className="overview-cards">
            <div className="overview-card highlight">
              <div className="card-icon">📱</div>
              <div className="card-content">
                <div className="card-label">ISDN</div>
                <div className="card-value-small">{p.isdn}</div>
              </div>
            </div>
            <div className="overview-card">
              <div className="card-icon">👤</div>
              <div className="card-content">
                <div className="card-label">Loại TB</div>
                <div className="card-value">
                  <span className={`type-badge ${p.subscriber_type === 'PRE' ? 'type-pre' : 'type-pos'}`}>
                    {p.subscriber_type || 'PRE'}
                  </span>
                </div>
              </div>
            </div>
            <div className="overview-card">
              <div className="card-icon">🎁</div>
              <div className="card-content">
                <div className="card-label">Service</div>
                <div className="card-value">
                  <span className={`service-badge ${getServiceBadgeClass(p.service_type)}`}>
                    {formatServiceType(p.service_type)}
                  </span>
                </div>
              </div>
            </div>
            <div className="overview-card">
              <div className="card-icon">💰</div>
              <div className="card-content">
                <div className="card-label">Số tiền ứng</div>
                <div className="card-value">{formatCurrency(p.advance_amount)}</div>
              </div>
            </div>
            <div className="overview-card revenue">
              <div className="card-icon">💵</div>
              <div className="card-content">
                <div className="card-label">Doanh thu dự kiến</div>
                <div className="card-value">{formatCurrency(p.revenue_per_advance)}</div>
              </div>
            </div>
          </div>

          {/* 2. ARPU TREND + REVENUE BREAKDOWN */}
          <div className="charts-row">
            {/* ARPU TREND */}
            <div className="chart-card wide">
              <h3>📈 ARPU Trend (7 tháng)</h3>
              <div className="arpu-trend-info">
                <span className="trend-label">Xu hướng:</span>
                <span className={`trend-badge trend-${p.arpu_trend}`}>{p.arpu_trend}</span>
                <span className="trend-label">Growth:</span>
                <span className={`growth-value ${p.arpu_growth_rate > 0 ? 'positive' : 'negative'}`}>
                  {p.arpu_growth_rate > 0 ? '+' : ''}{p.arpu_growth_rate?.toFixed(1)}%
                </span>
              </div>
              <div className="arpu-chart">
                {months.map((month, idx) => {
                  const height = maxARPU > 0 ? (month.arpu_total / maxARPU * 100) : 0;
                  return (
                    <div key={idx} className="chart-bar-wrapper">
                      <div className="chart-bar-container">
                        <div className="chart-bar" style={{ height: `${Math.max(height, 5)}%` }}>
                          <span className="chart-bar-value">{formatNumber(month.arpu_total)}</span>
                        </div>
                      </div>
                      <div className="chart-bar-label">T{month.data_month.substring(4)}</div>
                    </div>
                  );
                })}
              </div>
              <div className="arpu-stats">
                <div className="stat-item-mini">
                  <span className="stat-label-mini">Avg:</span>
                  <span className="stat-value-mini">{formatCurrency(p.arpu_avg_6m)}</span>
                </div>
                <div className="stat-item-mini">
                  <span className="stat-label-mini">Min:</span>
                  <span className="stat-value-mini">{formatCurrency(p.arpu_min_6m)}</span>
                </div>
                <div className="stat-item-mini">
                  <span className="stat-label-mini">Max:</span>
                  <span className="stat-value-mini">{formatCurrency(p.arpu_max_6m)}</span>
                </div>
              </div>
            </div>

            {/* REVENUE BREAKDOWN */}
            <div className="chart-card">
              <h3>💰 Cơ cấu Doanh thu</h3>
              <div className="revenue-pie">
                <div className="pie-chart">
                  {/* Simple CSS pie chart using conic-gradient */}
                  <div
                    className="pie-circle"
                    style={{
                      background: `conic-gradient(
                        #3b82f6 0% ${p.revenue_call_pct}%,
                        #10b981 ${p.revenue_call_pct}% ${p.revenue_call_pct + p.revenue_sms_pct}%,
                        #f59e0b ${p.revenue_call_pct + p.revenue_sms_pct}% 100%
                      )`
                    }}
                  >
                    <div className="pie-inner"></div>
                  </div>
                </div>
                <div className="pie-legend">
                  <div className="legend-item">
                    <span className="legend-color" style={{background: '#3b82f6'}}></span>
                    <span className="legend-label">Call: {p.revenue_call_pct?.toFixed(1)}%</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-color" style={{background: '#10b981'}}></span>
                    <span className="legend-label">SMS: {p.revenue_sms_pct?.toFixed(1)}%</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-color" style={{background: '#f59e0b'}}></span>
                    <span className="legend-label">Data: {p.revenue_data_pct?.toFixed(1)}%</span>
                  </div>
                </div>
                <div className="user-type-badge">
                  <span className="badge-label">Loại:</span>
                  <span className={`user-type-tag ${p.user_type?.replace(/\s+/g, '-').toLowerCase()}`}>
                    {p.user_type}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 3. TOPUP BEHAVIOR */}
          <div className="info-section">
            <h3>📱 Hành vi Topup</h3>
            <div className="info-grid">
              <div className="info-card-mini">
                <div className="mini-label">Số lần (tháng gần nhất)</div>
                <div className="mini-value">{p.topup_count_last_1m || 0} lần</div>
              </div>
              <div className="info-card-mini">
                <div className="mini-label">Số tiền (tháng gần nhất)</div>
                <div className="mini-value">{formatCurrency(p.topup_amount_last_1m)}</div>
              </div>
              <div className="info-card-mini">
                <div className="mini-label">Average Topup</div>
                <div className="mini-value">{formatCurrency(p.avg_topup_amount)}</div>
              </div>
              <div className="info-card-mini highlight">
                <div className="mini-label">Tần suất</div>
                <div className="mini-value">
                  <span className={`frequency-badge freq-${p.topup_frequency?.replace(/\s+/g, '-').toLowerCase()}`}>
                    {p.topup_frequency}
                  </span>
                </div>
              </div>
              <div className="info-card-mini highlight">
                <div className="mini-label">Topup/Advance Ratio</div>
                <div className="mini-value ratio">{p.topup_advance_ratio?.toFixed(1)}x</div>
              </div>
            </div>
          </div>

          {/* 4. RISK ASSESSMENT */}
          <div className="info-section">
            <h3>⚠️ Đánh giá Rủi ro</h3>
            <div className="risk-assessment">
              <div className="risk-main">
                <div className="risk-level-card">
                  <div className="risk-label">Risk Level</div>
                  <span className={`risk-badge-large ${getRiskBadgeClass(p.bad_debt_risk)}`}>
                    {p.bad_debt_risk}
                  </span>
                </div>
                <div className="risk-score-card">
                  <div className="risk-label">Risk Score</div>
                  <div className="risk-score-display">{p.risk_score}</div>
                  <div className="risk-score-bar">
                    <div
                      className={`risk-score-fill ${getRiskBadgeClass(p.bad_debt_risk)}`}
                      style={{width: `${Math.abs(p.risk_score) / 50 * 100}%`}}
                    ></div>
                  </div>
                </div>
              </div>
              <div className="risk-factors">
                <div className="factor-item">
                  ✅ Topup/Advance: <strong>{p.topup_advance_ratio?.toFixed(1)}x</strong>
                  {p.topup_advance_ratio >= 2 ? ' (Tốt)' : ' (Cần cải thiện)'}
                </div>
                <div className="factor-item">
                  {p.topup_frequency === 'Thường xuyên' ? '✅' : '⚠️'} Tần suất topup: <strong>{p.topup_frequency}</strong>
                </div>
                <div className="factor-item">
                  {p.arpu_growth_rate >= 0 ? '✅' : '⚠️'} ARPU trend: <strong>{p.arpu_trend}</strong>
                  ({p.arpu_growth_rate > 0 ? '+' : ''}{p.arpu_growth_rate?.toFixed(1)}%)
                </div>
              </div>
            </div>
          </div>

          {/* 5. KPI SCORES */}
          <div className="info-section">
            <h3>🔥 KPI Scores</h3>
            <div className="kpi-cards">
              <div className="kpi-card">
                <div className="kpi-label">Customer Value</div>
                <div className="kpi-score">{p.customer_value_score}</div>
                <div className="kpi-bar">
                  <div className="kpi-fill" style={{width: `${p.customer_value_score}%`}}></div>
                </div>
                <div className="kpi-desc">Giá trị khách hàng</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Advance Readiness</div>
                <div className="kpi-score">{p.advance_readiness_score}</div>
                <div className="kpi-bar">
                  <div className="kpi-fill ready" style={{width: `${p.advance_readiness_score}%`}}></div>
                </div>
                <div className="kpi-desc">Khả năng ứng</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Expected Revenue</div>
                <div className="kpi-score-money">{formatCurrency(p.revenue_per_advance)}</div>
                <div className="kpi-desc">Doanh thu kỳ vọng</div>
              </div>
            </div>
          </div>

          {/* 6. INSIGHTS */}
          <div className="info-section">
            <h3>💡 Insights & Recommendations</h3>
            <div className="insights-box">
              <div className="insight-item">
                <div className="insight-label">Tại sao được chọn:</div>
                <div className="insight-value">{p.classification_reason}</div>
              </div>
              <div className="insight-item">
                <div className="insight-label">Điểm mạnh:</div>
                <div className="insight-value">
                  <ul>
                    {p.arpu_avg_6m > 2000 && <li>ARPU ổn định {formatCurrency(p.arpu_avg_6m)}</li>}
                    {p.topup_frequency === 'Thường xuyên' && <li>Topup thường xuyên</li>}
                    {p.topup_advance_ratio >= 3 && <li>Tỷ lệ topup/ứng cao ({p.topup_advance_ratio?.toFixed(1)}x)</li>}
                    {p.bad_debt_risk === 'LOW' && <li>Rủi ro thấp</li>}
                  </ul>
                </div>
              </div>
              <div className="insight-item">
                <div className="insight-label">Đề xuất tối ưu:</div>
                <div className="insight-value">
                  Service: <strong>{formatServiceType(p.service_type)}</strong> -
                  {p.advance_amount && ` ${formatCurrency(p.advance_amount)}`}
                  {p.user_type === 'Heavy Data User' && ' (Có thể cross-sell gói data)'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Profile360Modal;
