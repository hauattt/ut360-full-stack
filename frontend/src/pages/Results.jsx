import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Users, DollarSign, Target, Shield } from 'lucide-react';
import axios from 'axios';
import './Results.css';

function Results() {
  const [selectedPhase, setSelectedPhase] = useState('phase1');
  const [phaseData, setPhaseData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const phases = [
    { id: 'phase1', name: 'Phase 1: Data Loading', icon: Users },
    { id: 'phase2', name: 'Phase 2: Feature Engineering', icon: TrendingUp },
    { id: 'phase3a', name: 'Phase 3A: Clustering', icon: Target },
    { id: 'phase3b', name: 'Phase 3B: Business Rules', icon: BarChart3 },
    { id: 'phase4', name: 'Phase 4: Bad Debt Filter', icon: Shield }
  ];

  useEffect(() => {
    loadPhaseData(selectedPhase);
  }, [selectedPhase]);

  const loadPhaseData = async (phase) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/results/${phase}`);
      setPhaseData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Không thể tải dữ liệu');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (!num) return '0';
    return new Intl.NumberFormat('vi-VN').format(num);
  };

  const formatCurrency = (num) => {
    if (!num) return '0 đ';
    return new Intl.NumberFormat('vi-VN').format(Math.round(num)) + ' đ';
  };

  const formatServiceType = (serviceType) => {
    const serviceTypeMap = {
      'EasyCredit': 'Fee',
      'MBFG': 'Free',
      'ungsanluong': 'Quota'
    };
    return serviceTypeMap[serviceType] || serviceType;
  };

  const renderPhase1Results = () => {
    if (!phaseData) return null;
    const { summary, subscriber_type_distribution, monthly_stats } = phaseData;

    if (!summary || !subscriber_type_distribution || !monthly_stats) {
      return (
        <div className="results-content">
          <div className="error-message">
            Dữ liệu Phase 1 chưa đầy đủ. Vui lòng chạy pipeline để tạo summary reports.
          </div>
        </div>
      );
    }

    return (
      <div className="results-content">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">
              <Users size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Tổng Records</div>
              <div className="stat-value">{formatNumber(summary.total_records)}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">
              <Users size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Unique Subscribers</div>
              <div className="stat-value">{formatNumber(summary.unique_subscribers)}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">
              <TrendingUp size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Advance Users</div>
              <div className="stat-value">{formatNumber(summary.advance_users)}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">
              <DollarSign size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Total Topup</div>
              <div className="stat-value">{formatCurrency(summary.total_topup_amount)}</div>
            </div>
          </div>
        </div>

        <div className="chart-section">
          <h3>Subscriber Type Distribution</h3>
          <div className="bar-chart">
            {Object.entries(subscriber_type_distribution || {}).map(([type, count]) => (
              <div key={type} className="bar-item">
                <div className="bar-label">{type || 'Unknown'}</div>
                <div className="bar-wrapper">
                  <div
                    className="bar-fill"
                    style={{ width: `${(count / summary.total_records) * 100}%` }}
                  >
                    <span className="bar-value">{formatNumber(count)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="chart-section">
          <h3>Monthly Statistics</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Month</th>
                <th>Unique Subscribers</th>
                <th>Total Topup</th>
                <th>Total Advance</th>
              </tr>
            </thead>
            <tbody>
              {monthly_stats?.map((stat) => (
                <tr key={stat.month}>
                  <td>{stat.month}</td>
                  <td>{formatNumber(stat.unique_subscribers)}</td>
                  <td>{formatCurrency(stat.total_topup)}</td>
                  <td>{formatCurrency(stat.total_advance)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderPhase2Results = () => {
    if (!phaseData) return null;
    const { summary, feature_categories } = phaseData;

    if (!summary || !feature_categories) {
      return <div className="error-message">Dữ liệu Phase 2 chưa đầy đủ</div>;
    }

    return (
      <div className="results-content">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">
              <BarChart3 size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Total Features</div>
              <div className="stat-value">{summary.total_features}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">
              <TrendingUp size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Advance Features</div>
              <div className="stat-value">{summary.advance_features}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">
              <DollarSign size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Topup Features</div>
              <div className="stat-value">{summary.topup_features}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">
              <Users size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Subscribers Processed</div>
              <div className="stat-value">{formatNumber(summary.total_subscribers)}</div>
            </div>
          </div>
        </div>

        <div className="feature-categories">
          <div className="category-section">
            <h3>Advance Features</h3>
            <ul>
              {feature_categories?.advance?.map((feat, idx) => (
                <li key={idx}>{feat}</li>
              )) || <li>No data</li>}
            </ul>
          </div>
          <div className="category-section">
            <h3>Topup Features</h3>
            <ul>
              {feature_categories?.topup?.map((feat, idx) => (
                <li key={idx}>{feat}</li>
              )) || <li>No data</li>}
            </ul>
          </div>
          <div className="category-section">
            <h3>Financial Features</h3>
            <ul>
              {feature_categories?.financial?.map((feat, idx) => (
                <li key={idx}>{feat}</li>
              )) || <li>No data</li>}
            </ul>
          </div>
        </div>
      </div>
    );
  };

  const renderPhase3aResults = () => {
    if (!phaseData) return null;
    const { summary, segment_distribution, cluster_statistics } = phaseData;

    if (!summary || !segment_distribution || !cluster_statistics) {
      return <div className="error-message">Dữ liệu Phase 3A chưa đầy đủ</div>;
    }

    return (
      <div className="results-content">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">
              <Users size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Total Subscribers</div>
              <div className="stat-value">{formatNumber(summary.total_subscribers)}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">
              <Target size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Number of Clusters</div>
              <div className="stat-value">{summary.num_clusters}</div>
            </div>
          </div>
          <div className="stat-card highlight">
            <div className="stat-icon">
              <TrendingUp size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Expansion Target</div>
              <div className="stat-value">{formatNumber(summary.expansion_target)}</div>
            </div>
          </div>
        </div>

        <div className="chart-section">
          <h3>Segment Distribution</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Segment</th>
                <th>Total Subscribers</th>
                <th>Advance Users</th>
                <th>Advance Rate</th>
              </tr>
            </thead>
            <tbody>
              {segment_distribution?.map((seg) => (
                <tr key={seg.segment}>
                  <td>{seg.segment}</td>
                  <td>{formatNumber(seg.total)}</td>
                  <td>{formatNumber(seg.advance_users)}</td>
                  <td>{seg.advance_rate}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="chart-section">
          <h3>Cluster Statistics</h3>
          <div className="bar-chart">
            {cluster_statistics?.map((cluster) => (
              <div key={cluster.cluster} className="bar-item">
                <div className="bar-label">Cluster {cluster.cluster} ({cluster.advance_rate}%)</div>
                <div className="bar-wrapper">
                  <div
                    className="bar-fill"
                    style={{ width: `${(cluster.total / summary.total_subscribers) * 100}%` }}
                  >
                    <span className="bar-value">{formatNumber(cluster.total)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderPhase3bResults = () => {
    if (!phaseData) return null;
    const { summary, service_type_distribution, amount_distribution } = phaseData;

    if (!summary || !service_type_distribution || !amount_distribution) {
      return (
        <div className="results-content">
          <div className="error-message">
            Dữ liệu Phase 3B chưa đầy đủ. Vui lòng chạy pipeline để tạo summary reports.
          </div>
        </div>
      );
    }

    return (
      <div className="results-content">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">
              <Users size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Total Recommendations</div>
              <div className="stat-value">{formatNumber(summary.total_recommendations)}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">
              <DollarSign size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Total Advance Amount</div>
              <div className="stat-value">{formatCurrency(summary.total_advance_amount)}</div>
            </div>
          </div>
          <div className="stat-card highlight">
            <div className="stat-icon">
              <TrendingUp size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Expected Revenue</div>
              <div className="stat-value">{formatCurrency(summary.total_expected_revenue)}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">
              <BarChart3 size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Avg Advance Amount</div>
              <div className="stat-value">{formatCurrency(summary.avg_advance_amount)}</div>
            </div>
          </div>
        </div>

        <div className="info-card">
          <div className="info-icon">ℹ️</div>
          <div className="info-content">
            <h4>Subscriber Type Policy</h4>
            <p><strong>Chỉ mời ứng cho thuê bao trả trước (PRE)</strong></p>
            <p>Tất cả khuyến nghị chỉ áp dụng cho thuê bao trả trước. Thuê bao trả sau (POS) đã được lọc ra khỏi kết quả.</p>
          </div>
        </div>

        <div className="chart-section">
          <h3>Service Type Distribution</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Service Type</th>
                <th>Subscribers</th>
                <th>Total Advance</th>
                <th>Total Revenue</th>
              </tr>
            </thead>
            <tbody>
              {service_type_distribution?.map((service) => (
                <tr key={service.service_type}>
                  <td>{formatServiceType(service.service_type)}</td>
                  <td>{formatNumber(service.subscribers)}</td>
                  <td>{formatCurrency(service.total_advance)}</td>
                  <td>{formatCurrency(service.total_revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="chart-section">
          <h3>Advance Amount Distribution</h3>
          <div className="bar-chart">
            {Object.entries(amount_distribution || {}).map(([range, count]) => (
              <div key={range} className="bar-item">
                <div className="bar-label">{range}</div>
                <div className="bar-wrapper">
                  <div
                    className="bar-fill"
                    style={{ width: `${(count / summary.total_recommendations) * 100}%` }}
                  >
                    <span className="bar-value">{formatNumber(count)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderPhase4Results = () => {
    if (!phaseData) return null;
    const { summary, risk_distribution, service_type_distribution } = phaseData;

    if (!summary || !service_type_distribution) {
      return (
        <div className="results-content">
          <div className="error-message">
            Dữ liệu Phase 4 chưa đầy đủ. Vui lòng chạy pipeline để tạo summary reports.
          </div>
        </div>
      );
    }

    return (
      <div className="results-content">
        <div className="stats-grid">
          <div className="stat-card highlight">
            <div className="stat-icon">
              <Shield size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Final Recommendations</div>
              <div className="stat-value">{formatNumber(summary.final_recommendations)}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">
              <DollarSign size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Total Advance Amount</div>
              <div className="stat-value">{formatCurrency(summary.total_advance_amount)}</div>
            </div>
          </div>
          <div className="stat-card highlight">
            <div className="stat-icon">
              <TrendingUp size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Expected Revenue</div>
              <div className="stat-value">{formatCurrency(summary.total_expected_revenue)}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">
              <BarChart3 size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-label">Avg Advance Amount</div>
              <div className="stat-value">{formatCurrency(summary.avg_advance_amount)}</div>
            </div>
          </div>
        </div>

        <div className="info-card">
          <div className="info-icon">ℹ️</div>
          <div className="info-content">
            <h4>Subscriber Type Policy</h4>
            <p><strong>Chỉ mời ứng cho thuê bao trả trước (PRE)</strong></p>
            <p>Tất cả khuyến nghị cuối cùng chỉ áp dụng cho thuê bao trả trước. Thuê bao trả sau (POS) đã được lọc ra ở Phase 3B.</p>
          </div>
        </div>

        {risk_distribution && Object.keys(risk_distribution).length > 0 && (
          <div className="chart-section">
            <h3>Risk Level Distribution</h3>
            <div className="bar-chart">
              {Object.entries(risk_distribution || {}).map(([risk, count]) => (
                <div key={risk} className="bar-item">
                  <div className="bar-label">{risk}</div>
                  <div className="bar-wrapper">
                    <div
                      className="bar-fill"
                      style={{ width: `${(count / summary.final_recommendations) * 100}%` }}
                    >
                      <span className="bar-value">{formatNumber(count)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="chart-section">
          <h3>Final Service Type Distribution</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Service Type</th>
                <th>Subscribers</th>
                <th>Total Advance</th>
                <th>Total Revenue</th>
              </tr>
            </thead>
            <tbody>
              {service_type_distribution?.map((service) => (
                <tr key={service.service_type}>
                  <td>{formatServiceType(service.service_type)}</td>
                  <td>{formatNumber(service.subscribers)}</td>
                  <td>{formatCurrency(service.total_advance)}</td>
                  <td>{formatCurrency(service.total_revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderPhaseContent = () => {
    if (loading) {
      return <div className="loading">Đang tải dữ liệu...</div>;
    }

    if (error) {
      return <div className="error-message">{error}</div>;
    }

    switch (selectedPhase) {
      case 'phase1':
        return renderPhase1Results();
      case 'phase2':
        return renderPhase2Results();
      case 'phase3a':
        return renderPhase3aResults();
      case 'phase3b':
        return renderPhase3bResults();
      case 'phase4':
        return renderPhase4Results();
      default:
        return null;
    }
  };

  return (
    <div className="results-page">
      <div className="results-header">
        <h1>Pipeline Results</h1>
        <p>Xem kết quả chi tiết và thống kê từng phase</p>
      </div>

      <div className="phase-tabs">
        {phases.map((phase) => {
          const Icon = phase.icon;
          return (
            <button
              key={phase.id}
              className={`phase-tab ${selectedPhase === phase.id ? 'active' : ''}`}
              onClick={() => setSelectedPhase(phase.id)}
            >
              <Icon size={20} />
              <span>{phase.name}</span>
            </button>
          );
        })}
      </div>

      {renderPhaseContent()}
    </div>
  );
}

export default Results;
