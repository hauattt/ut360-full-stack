import React, { useState, useEffect } from 'react';
import { Play, Settings, Database, TrendingUp } from 'lucide-react';
import axios from 'axios';
import './Dashboard.css';

function Dashboard() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [runningPipeline, setRunningPipeline] = useState(false);

  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await axios.get('/api/system/status');
      setSystemStatus(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch system status');
      setLoading(false);
    }
  };

  const handleRunPipeline = async () => {
    if (!window.confirm('Bạn có chắc chắn muốn chạy toàn bộ pipeline?')) {
      return;
    }

    setRunningPipeline(true);
    try {
      const response = await axios.post('/api/pipeline/run', {
        phases: ['phase1', 'phase2', 'phase3b', 'phase4'],
        use_existing_data: false
      });

      alert(`Pipeline đã được khởi chạy!\nRun ID: ${response.data.id}`);
      window.location.href = '/runs';
    } catch (err) {
      alert('Lỗi khi chạy pipeline: ' + (err.response?.data?.detail || err.message));
    } finally {
      setRunningPipeline(false);
    }
  };

  if (loading) {
    return <div className="loading">Đang tải dữ liệu...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  const totalConfigs = Object.values(systemStatus.configurations || {}).reduce((a, b) => a + b, 0);
  const totalRuns = Object.values(systemStatus.pipeline_runs || {}).reduce((a, b) => a + b, 0);

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <button className="button button-primary" onClick={handleRunPipeline} disabled={runningPipeline}>
          <Play size={20} />
          {runningPipeline ? 'Đang khởi chạy...' : 'Chạy Pipeline'}
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#667eea' }}>
            <Settings size={32} color="white" />
          </div>
          <div className="stat-content">
            <h3>{totalConfigs}</h3>
            <p>Cấu hình</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#764ba2' }}>
            <Database size={32} color="white" />
          </div>
          <div className="stat-content">
            <h3>{totalRuns}</h3>
            <p>Lượt chạy</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#4caf50' }}>
            <TrendingUp size={32} color="white" />
          </div>
          <div className="stat-content">
            <h3>{systemStatus.pipeline_runs?.completed || 0}</h3>
            <p>Thành công</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#f44336' }}>
            <TrendingUp size={32} color="white" />
          </div>
          <div className="stat-content">
            <h3>{systemStatus.pipeline_runs?.failed || 0}</h3>
            <p>Thất bại</p>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <h2 className="card-title">Cấu hình theo loại</h2>
          <div className="config-list">
            <div className="config-item">
              <span className="config-label">Bad Debt Weights:</span>
              <span className="config-value">{systemStatus.configurations?.bad_debt || 0}</span>
            </div>
            <div className="config-item">
              <span className="config-label">Business Rules:</span>
              <span className="config-value">{systemStatus.configurations?.business_rules || 0}</span>
            </div>
            <div className="config-item">
              <span className="config-label">Clustering Config:</span>
              <span className="config-value">{systemStatus.configurations?.clustering || 0}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="card-title">Lượt chạy theo trạng thái</h2>
          <div className="config-list">
            <div className="config-item">
              <span className="config-label">Pending:</span>
              <span className="status-badge status-pending">{systemStatus.pipeline_runs?.pending || 0}</span>
            </div>
            <div className="config-item">
              <span className="config-label">Running:</span>
              <span className="status-badge status-running">{systemStatus.pipeline_runs?.running || 0}</span>
            </div>
            <div className="config-item">
              <span className="config-label">Completed:</span>
              <span className="status-badge status-completed">{systemStatus.pipeline_runs?.completed || 0}</span>
            </div>
            <div className="config-item">
              <span className="config-label">Failed:</span>
              <span className="status-badge status-failed">{systemStatus.pipeline_runs?.failed || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {systemStatus.latest_successful_run && (
        <div className="card">
          <h2 className="card-title">Lần chạy thành công gần nhất</h2>
          <div className="run-details">
            <div className="detail-item">
              <strong>Run ID:</strong> {systemStatus.latest_successful_run.id}
            </div>
            <div className="detail-item">
              <strong>Phase:</strong> {systemStatus.latest_successful_run.phase}
            </div>
            <div className="detail-item">
              <strong>Hoàn thành:</strong> {new Date(systemStatus.latest_successful_run.completed_at).toLocaleString('vi-VN')}
            </div>
            {systemStatus.latest_successful_run.output_path && (
              <div className="detail-item">
                <strong>Output:</strong> {systemStatus.latest_successful_run.output_path}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="card">
        <h2 className="card-title">Thông tin hệ thống</h2>
        <div className="system-info">
          <div className="info-item">
            <strong>Database:</strong> {systemStatus.database_path}
          </div>
          <div className="info-item">
            <strong>Base Directory:</strong> {systemStatus.base_directory}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
