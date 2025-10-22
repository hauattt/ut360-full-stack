import React, { useState, useEffect } from 'react';
import { Play, RefreshCw, Eye, Download, BarChart3 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './PipelineRuns.css';

function PipelineRuns() {
  const navigate = useNavigate();
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showRunModal, setShowRunModal] = useState(false);
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [selectedRun, setSelectedRun] = useState(null);
  const [logs, setLogs] = useState('');

  const [runConfig, setRunConfig] = useState({
    phases: ['phase1', 'phase2', 'phase3a', 'phase3b', 'phase4', 'phase5'],
    config_id: null,
    use_existing_data: true
  });

  useEffect(() => {
    fetchRuns();
    const interval = setInterval(fetchRuns, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchRuns = async () => {
    try {
      const response = await axios.get('/api/pipeline/runs');
      setRuns(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch pipeline runs');
      setLoading(false);
    }
  };

  const handleRunPipeline = async () => {
    try {
      const response = await axios.post('/api/pipeline/run', runConfig);
      alert(`Pipeline đã được khởi chạy!\nRun ID: ${response.data.id}`);
      setShowRunModal(false);
      fetchRuns();
    } catch (err) {
      alert('Lỗi khi chạy pipeline: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleResumeFromPhase = (failedPhase) => {
    // Parse phase from error (e.g., "phase3b (3/4)" -> "phase3b")
    const phaseName = failedPhase.split(' ')[0];

    // Determine which phases to run from the failed phase
    const allPhases = ['phase1', 'phase2', 'phase3a', 'phase3b', 'phase4', 'phase5'];
    const phaseIndex = allPhases.findIndex(p => phaseName.includes(p));

    if (phaseIndex >= 0) {
      const resumePhases = allPhases.slice(phaseIndex);
      setRunConfig({
        ...runConfig,
        phases: resumePhases
      });
      setShowRunModal(true);
    }
  };

  const handleViewLogs = async (runId) => {
    try {
      const response = await axios.get(`/api/pipeline/runs/${runId}/logs`);
      setLogs(response.data.logs);
      setShowLogsModal(true);
    } catch (err) {
      alert('Lỗi khi tải logs: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleViewDetails = async (runId) => {
    try {
      const response = await axios.get(`/api/pipeline/runs/${runId}`);
      setSelectedRun(response.data);
    } catch (err) {
      alert('Lỗi khi tải chi tiết: ' + (err.response?.data?.detail || err.message));
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'pending':
        return 'status-badge status-pending';
      case 'running':
        return 'status-badge status-running';
      case 'completed':
        return 'status-badge status-completed';
      case 'failed':
        return 'status-badge status-failed';
      default:
        return 'status-badge';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending':
        return 'Đang chờ';
      case 'running':
        return 'Đang chạy';
      case 'completed':
        return 'Hoàn thành';
      case 'failed':
        return 'Thất bại';
      default:
        return status;
    }
  };

  if (loading) {
    return <div className="loading">Đang tải dữ liệu...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="pipeline-runs">
      <div className="runs-header">
        <h1>Lịch sử chạy Pipeline</h1>
        <div className="header-actions">
          <button className="button button-secondary" onClick={() => navigate('/results')}>
            <BarChart3 size={20} />
            Xem Kết quả
          </button>
          <button className="button button-secondary" onClick={fetchRuns}>
            <RefreshCw size={20} />
            Làm mới
          </button>
          <button className="button button-primary" onClick={() => setShowRunModal(true)}>
            <Play size={20} />
            Chạy Pipeline
          </button>
        </div>
      </div>

      <div className="card">
        {runs.length === 0 ? (
          <div className="empty-state">Chưa có lượt chạy nào. Bắt đầu chạy pipeline để xem kết quả.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Phase</th>
                <th>Trạng thái</th>
                <th>Bắt đầu</th>
                <th>Hoàn thành</th>
                <th>Output</th>
                <th>Hành động</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id}>
                  <td>
                    <code className="run-id">{run.id.substring(0, 8)}</code>
                  </td>
                  <td>
                    <div className="phase-info">
                      <div>{run.phase}</div>
                      {run.status === 'running' && (
                        <div className="phase-progress">
                          <div className="spinner"></div>
                          <span>Đang chạy...</span>
                        </div>
                      )}
                    </div>
                  </td>
                  <td>
                    <span className={getStatusBadgeClass(run.status)}>
                      {getStatusText(run.status)}
                    </span>
                  </td>
                  <td>{new Date(run.started_at).toLocaleString('vi-VN')}</td>
                  <td>
                    {run.completed_at
                      ? new Date(run.completed_at).toLocaleString('vi-VN')
                      : '-'}
                  </td>
                  <td>
                    {run.output_path ? (
                      <code className="output-path">{run.output_path}</code>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td>
                    <div className="action-buttons">
                      {run.status === 'failed' && (
                        <button
                          className="button button-primary button-sm"
                          onClick={() => handleResumeFromPhase(run.phase)}
                          title="Chạy lại từ phase lỗi"
                        >
                          <Play size={16} />
                        </button>
                      )}
                      <button
                        className="button button-secondary button-sm"
                        onClick={() => handleViewDetails(run.id)}
                        title="Xem chi tiết"
                      >
                        <Eye size={16} />
                      </button>
                      <button
                        className="button button-secondary button-sm"
                        onClick={() => handleViewLogs(run.id)}
                        title="Xem logs"
                      >
                        <Download size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedRun && (
        <div className="card">
          <h2 className="card-title">Chi tiết Run</h2>

          {/* Progress Bar for Running Status */}
          {selectedRun.status === 'running' && (
            <div className="progress-section">
              <h3>Tiến trình</h3>
              <div className="phase-tracker">
                {['phase1', 'phase2', 'phase3a', 'phase3b', 'phase4'].map((phase, idx) => {
                  const phaseName = {
                    'phase1': 'Data Loading',
                    'phase2': 'Feature Engineering',
                    'phase3a': 'Clustering',
                    'phase3b': 'Business Rules',
                    'phase4': 'Bad Debt Filter'
                  }[phase];

                  const currentPhase = selectedRun.phase.toLowerCase();
                  const isCompleted = currentPhase.includes(phase) && currentPhase.includes('(') &&
                                     parseInt(currentPhase.split('(')[1]) > idx + 1;
                  const isCurrent = currentPhase.includes(phase);
                  const isPending = !isCompleted && !isCurrent;

                  return (
                    <div key={phase} className={`phase-step ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''} ${isPending ? 'pending' : ''}`}>
                      <div className="phase-indicator">
                        {isCompleted && '✓'}
                        {isCurrent && <div className="spinner-small"></div>}
                        {isPending && (idx + 1)}
                      </div>
                      <div className="phase-name">{phaseName}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="run-details-grid">
            <div className="detail-item">
              <strong>Run ID:</strong>
              <span>{selectedRun.id}</span>
            </div>
            <div className="detail-item">
              <strong>Config ID:</strong>
              <span>{selectedRun.config_id || 'N/A'}</span>
            </div>
            <div className="detail-item">
              <strong>Phase:</strong>
              <span>{selectedRun.phase}</span>
            </div>
            <div className="detail-item">
              <strong>Trạng thái:</strong>
              <span className={getStatusBadgeClass(selectedRun.status)}>
                {getStatusText(selectedRun.status)}
              </span>
            </div>
            <div className="detail-item">
              <strong>Bắt đầu:</strong>
              <span>{new Date(selectedRun.started_at).toLocaleString('vi-VN')}</span>
            </div>
            <div className="detail-item">
              <strong>Hoàn thành:</strong>
              <span>
                {selectedRun.completed_at
                  ? new Date(selectedRun.completed_at).toLocaleString('vi-VN')
                  : 'Chưa hoàn thành'}
              </span>
            </div>
            {selectedRun.output_path && (
              <div className="detail-item full-width">
                <strong>Output Path:</strong>
                <code>{selectedRun.output_path}</code>
              </div>
            )}
            {selectedRun.error_message && (
              <div className="detail-item full-width error-message">
                <strong>Error Message:</strong>
                <pre>{selectedRun.error_message}</pre>
              </div>
            )}
            {selectedRun.metrics && (
              <div className="detail-item full-width">
                <strong>Metrics:</strong>
                <pre>{JSON.stringify(selectedRun.metrics, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Run Pipeline Modal */}
      {showRunModal && (
        <div className="modal-overlay" onClick={() => setShowRunModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Chạy Pipeline</h2>
              <button className="modal-close" onClick={() => setShowRunModal(false)}>
                ×
              </button>
            </div>

            <div className="form-group">
              <label className="label">Chọn Phase</label>
              <div style={{marginBottom: '10px', display: 'flex', gap: '10px', flexWrap: 'wrap'}}>
                <button
                  type="button"
                  className="button button-secondary button-sm"
                  onClick={() => setRunConfig({...runConfig, phases: ['phase1', 'phase2', 'phase3a', 'phase3b', 'phase4', 'phase5']})}
                >
                  Tất cả phases
                </button>
                <button
                  type="button"
                  className="button button-secondary button-sm"
                  onClick={() => setRunConfig({...runConfig, phases: ['phase3a', 'phase3b', 'phase4', 'phase5']})}
                >
                  Từ Phase 3A
                </button>
                <button
                  type="button"
                  className="button button-secondary button-sm"
                  onClick={() => setRunConfig({...runConfig, phases: ['phase3b', 'phase4', 'phase5']})}
                >
                  Từ Phase 3B
                </button>
                <button
                  type="button"
                  className="button button-secondary button-sm"
                  onClick={() => setRunConfig({...runConfig, phases: ['phase5']})}
                >
                  Chỉ Phase 5 (Summary)
                </button>
              </div>
              <div className="phase-checkboxes">
                <label>
                  <input
                    type="checkbox"
                    checked={runConfig.phases.includes('phase1')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setRunConfig({
                          ...runConfig,
                          phases: [...runConfig.phases, 'phase1']
                        });
                      } else {
                        setRunConfig({
                          ...runConfig,
                          phases: runConfig.phases.filter(p => p !== 'phase1')
                        });
                      }
                    }}
                  />
                  Phase 1: Data Loading
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={runConfig.phases.includes('phase2')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setRunConfig({
                          ...runConfig,
                          phases: [...runConfig.phases, 'phase2']
                        });
                      } else {
                        setRunConfig({
                          ...runConfig,
                          phases: runConfig.phases.filter(p => p !== 'phase2')
                        });
                      }
                    }}
                  />
                  Phase 2: Feature Engineering
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={runConfig.phases.includes('phase3a')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setRunConfig({
                          ...runConfig,
                          phases: [...runConfig.phases, 'phase3a']
                        });
                      } else {
                        setRunConfig({
                          ...runConfig,
                          phases: runConfig.phases.filter(p => p !== 'phase3a')
                        });
                      }
                    }}
                  />
                  Phase 3A: Clustering
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={runConfig.phases.includes('phase3b')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setRunConfig({
                          ...runConfig,
                          phases: [...runConfig.phases, 'phase3b']
                        });
                      } else {
                        setRunConfig({
                          ...runConfig,
                          phases: runConfig.phases.filter(p => p !== 'phase3b')
                        });
                      }
                    }}
                  />
                  Phase 3B: Business Rules
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={runConfig.phases.includes('phase4')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setRunConfig({
                          ...runConfig,
                          phases: [...runConfig.phases, 'phase4']
                        });
                      } else {
                        setRunConfig({
                          ...runConfig,
                          phases: runConfig.phases.filter(p => p !== 'phase4')
                        });
                      }
                    }}
                  />
                  Phase 4: Bad Debt Filter
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={runConfig.phases.includes('phase5')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setRunConfig({
                          ...runConfig,
                          phases: [...runConfig.phases, 'phase5']
                        });
                      } else {
                        setRunConfig({
                          ...runConfig,
                          phases: runConfig.phases.filter(p => p !== 'phase5')
                        });
                      }
                    }}
                  />
                  Phase 5: Generate Summaries
                </label>
              </div>
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={runConfig.use_existing_data}
                  onChange={(e) =>
                    setRunConfig({ ...runConfig, use_existing_data: e.target.checked })
                  }
                />
                Sử dụng dữ liệu trung gian có sẵn (nếu có)
              </label>
            </div>

            <div className="modal-actions">
              <button
                type="button"
                className="button button-secondary"
                onClick={() => setShowRunModal(false)}
              >
                Hủy
              </button>
              <button
                type="button"
                className="button button-primary"
                onClick={handleRunPipeline}
                disabled={runConfig.phases.length === 0}
              >
                Bắt đầu chạy
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Logs Modal */}
      {showLogsModal && (
        <div className="modal-overlay" onClick={() => setShowLogsModal(false)}>
          <div className="modal modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Pipeline Logs</h2>
              <button className="modal-close" onClick={() => setShowLogsModal(false)}>
                ×
              </button>
            </div>

            <div className="logs-container">
              <pre>{logs || 'Không có logs'}</pre>
            </div>

            <div className="modal-actions">
              <button
                type="button"
                className="button button-secondary"
                onClick={() => setShowLogsModal(false)}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default PipelineRuns;
