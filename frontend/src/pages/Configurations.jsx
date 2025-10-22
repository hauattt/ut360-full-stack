import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Check, X } from 'lucide-react';
import axios from 'axios';
import './Configurations.css';

function Configurations() {
  const [configurations, setConfigurations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [configType, setConfigType] = useState('business_rules');

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    config_type: 'business_rules',
    config_data: {}
  });

  useEffect(() => {
    fetchConfigurations();
  }, []);

  const fetchConfigurations = async () => {
    try {
      const response = await axios.get('/api/configurations');
      setConfigurations(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch configurations');
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingConfig(null);
    setFormData({
      name: '',
      description: '',
      config_type: configType,
      config_data: getDefaultConfigData(configType)
    });
    setShowModal(true);
  };

  const handleEdit = (config) => {
    setEditingConfig(config);
    setFormData({
      name: config.name,
      description: config.description || '',
      config_type: config.config_type,
      config_data: config.config_data
    });
    setShowModal(true);
  };

  const handleDelete = async (configId) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa cấu hình này?')) {
      return;
    }

    try {
      await axios.delete(`/api/configurations/${configId}`);
      fetchConfigurations();
      alert('Đã xóa cấu hình thành công!');
    } catch (err) {
      alert('Lỗi khi xóa cấu hình: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleActivate = async (configId) => {
    try {
      await axios.post(`/api/configurations/${configId}/activate`);
      fetchConfigurations();
      alert('Đã kích hoạt cấu hình thành công!');
    } catch (err) {
      alert('Lỗi khi kích hoạt cấu hình: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (editingConfig) {
        await axios.put(`/api/configurations/${editingConfig.id}`, formData);
        alert('Đã cập nhật cấu hình thành công!');
      } else {
        await axios.post('/api/configurations', formData);
        alert('Đã tạo cấu hình mới thành công!');
      }
      setShowModal(false);
      fetchConfigurations();
    } catch (err) {
      alert('Lỗi: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleConfigDataChange = (key, value) => {
    setFormData({
      ...formData,
      config_data: {
        ...formData.config_data,
        [key]: parseFloat(value) || 0
      }
    });
  };

  const getDefaultConfigData = (type) => {
    if (type === 'bad_debt') {
      return {
        topup_advance_ratio_weight: 40.0,
        topup_frequency_weight: 20.0,
        arpu_stability_weight: 20.0,
        avg_topup_weight: 20.0,
        base_risk_score: 50.0,
        low_risk_threshold: 30.0,
        high_risk_threshold: 60.0
      };
    } else if (type === 'business_rules') {
      return {
        voice_sms_threshold: 70.0,
        ungsanluong_arpu_multiplier: 0.8,
        ungsanluong_min_amount: 10000,
        ungsanluong_max_amount: 50000,
        ungsanluong_revenue_rate: 0.20,
        easycredit_min_topup_count_1m: 1,
        easycredit_min_topup_amount: 50000,
        easycredit_min_topup_count_2m: 1,
        easycredit_vip_arpu_threshold: 100000,
        easycredit_default_amount: 25000,
        easycredit_vip_amount: 50000,
        easycredit_revenue_rate: 0.30,
        mbfg_min_topup_count_1m: 2,
        mbfg_arpu_multiplier: 1.2,
        mbfg_min_amount: 10000,
        mbfg_max_amount: 50000,
        mbfg_revenue_rate: 0.30
      };
    } else if (type === 'clustering') {
      return {
        n_clusters: 3,
        n_init: 20,
        max_iter: 500,
        random_state: 42
      };
    }
    return {};
  };

  const renderConfigFields = () => {
    const type = formData.config_type;
    const data = formData.config_data;

    if (type === 'bad_debt') {
      return (
        <div className="config-fields">
          <h3>Trọng số Bad Debt Risk</h3>
          <div className="form-group">
            <label className="label">Topup/Advance Ratio Weight (0-100)</label>
            <input
              type="number"
              className="input"
              value={data.topup_advance_ratio_weight || 0}
              onChange={(e) => handleConfigDataChange('topup_advance_ratio_weight', e.target.value)}
              step="0.1"
              min="0"
              max="100"
            />
          </div>
          <div className="form-group">
            <label className="label">Topup Frequency Weight (0-100)</label>
            <input
              type="number"
              className="input"
              value={data.topup_frequency_weight || 0}
              onChange={(e) => handleConfigDataChange('topup_frequency_weight', e.target.value)}
              step="0.1"
              min="0"
              max="100"
            />
          </div>
          <div className="form-group">
            <label className="label">ARPU Stability Weight (0-100)</label>
            <input
              type="number"
              className="input"
              value={data.arpu_stability_weight || 0}
              onChange={(e) => handleConfigDataChange('arpu_stability_weight', e.target.value)}
              step="0.1"
              min="0"
              max="100"
            />
          </div>
          <div className="form-group">
            <label className="label">Avg Topup Weight (0-100)</label>
            <input
              type="number"
              className="input"
              value={data.avg_topup_weight || 0}
              onChange={(e) => handleConfigDataChange('avg_topup_weight', e.target.value)}
              step="0.1"
              min="0"
              max="100"
            />
          </div>
          <div className="form-group">
            <label className="label">Base Risk Score (0-100)</label>
            <input
              type="number"
              className="input"
              value={data.base_risk_score || 0}
              onChange={(e) => handleConfigDataChange('base_risk_score', e.target.value)}
              step="0.1"
              min="0"
              max="100"
            />
          </div>
          <div className="form-group">
            <label className="label">Low Risk Threshold (0-100)</label>
            <input
              type="number"
              className="input"
              value={data.low_risk_threshold || 0}
              onChange={(e) => handleConfigDataChange('low_risk_threshold', e.target.value)}
              step="0.1"
              min="0"
              max="100"
            />
          </div>
          <div className="form-group">
            <label className="label">High Risk Threshold (0-100)</label>
            <input
              type="number"
              className="input"
              value={data.high_risk_threshold || 0}
              onChange={(e) => handleConfigDataChange('high_risk_threshold', e.target.value)}
              step="0.1"
              min="0"
              max="100"
            />
          </div>
        </div>
      );
    } else if (type === 'business_rules') {
      return (
        <div className="config-fields">
          <h3>Quota (Voice/SMS)</h3>
          <div className="form-group">
            <label className="label">Voice/SMS Threshold (%)</label>
            <input
              type="number"
              className="input"
              value={data.voice_sms_threshold || 0}
              onChange={(e) => handleConfigDataChange('voice_sms_threshold', e.target.value)}
              step="0.1"
            />
          </div>
          <div className="form-group">
            <label className="label">ARPU Multiplier</label>
            <input
              type="number"
              className="input"
              value={data.ungsanluong_arpu_multiplier || 0}
              onChange={(e) => handleConfigDataChange('ungsanluong_arpu_multiplier', e.target.value)}
              step="0.1"
            />
          </div>
          <div className="form-group">
            <label className="label">Min Amount (VND)</label>
            <input
              type="number"
              className="input"
              value={data.ungsanluong_min_amount || 0}
              onChange={(e) => handleConfigDataChange('ungsanluong_min_amount', e.target.value)}
              step="1000"
            />
          </div>
          <div className="form-group">
            <label className="label">Max Amount (VND)</label>
            <input
              type="number"
              className="input"
              value={data.ungsanluong_max_amount || 0}
              onChange={(e) => handleConfigDataChange('ungsanluong_max_amount', e.target.value)}
              step="1000"
            />
          </div>
          <div className="form-group">
            <label className="label">Revenue Rate (0-1)</label>
            <input
              type="number"
              className="input"
              value={data.ungsanluong_revenue_rate || 0}
              onChange={(e) => handleConfigDataChange('ungsanluong_revenue_rate', e.target.value)}
              step="0.01"
            />
          </div>

          <h3>Fee</h3>
          <div className="form-group">
            <label className="label">Min Topup Count (Last 1M)</label>
            <input
              type="number"
              className="input"
              value={data.easycredit_min_topup_count_1m || 0}
              onChange={(e) => handleConfigDataChange('easycredit_min_topup_count_1m', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="label">Min Topup Amount (VND)</label>
            <input
              type="number"
              className="input"
              value={data.easycredit_min_topup_amount || 0}
              onChange={(e) => handleConfigDataChange('easycredit_min_topup_amount', e.target.value)}
              step="1000"
            />
          </div>
          <div className="form-group">
            <label className="label">Min Topup Count (Last 2M)</label>
            <input
              type="number"
              className="input"
              value={data.easycredit_min_topup_count_2m || 0}
              onChange={(e) => handleConfigDataChange('easycredit_min_topup_count_2m', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="label">VIP ARPU Threshold (VND)</label>
            <input
              type="number"
              className="input"
              value={data.easycredit_vip_arpu_threshold || 0}
              onChange={(e) => handleConfigDataChange('easycredit_vip_arpu_threshold', e.target.value)}
              step="1000"
            />
          </div>
          <div className="form-group">
            <label className="label">Default Amount (VND)</label>
            <input
              type="number"
              className="input"
              value={data.easycredit_default_amount || 0}
              onChange={(e) => handleConfigDataChange('easycredit_default_amount', e.target.value)}
              step="1000"
            />
          </div>
          <div className="form-group">
            <label className="label">VIP Amount (VND)</label>
            <input
              type="number"
              className="input"
              value={data.easycredit_vip_amount || 0}
              onChange={(e) => handleConfigDataChange('easycredit_vip_amount', e.target.value)}
              step="1000"
            />
          </div>
          <div className="form-group">
            <label className="label">Revenue Rate (0-1)</label>
            <input
              type="number"
              className="input"
              value={data.easycredit_revenue_rate || 0}
              onChange={(e) => handleConfigDataChange('easycredit_revenue_rate', e.target.value)}
              step="0.01"
            />
          </div>

          <h3>Free</h3>
          <div className="form-group">
            <label className="label">Min Topup Count (Last 1M)</label>
            <input
              type="number"
              className="input"
              value={data.mbfg_min_topup_count_1m || 0}
              onChange={(e) => handleConfigDataChange('mbfg_min_topup_count_1m', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="label">ARPU Multiplier</label>
            <input
              type="number"
              className="input"
              value={data.mbfg_arpu_multiplier || 0}
              onChange={(e) => handleConfigDataChange('mbfg_arpu_multiplier', e.target.value)}
              step="0.1"
            />
          </div>
          <div className="form-group">
            <label className="label">Min Amount (VND)</label>
            <input
              type="number"
              className="input"
              value={data.mbfg_min_amount || 0}
              onChange={(e) => handleConfigDataChange('mbfg_min_amount', e.target.value)}
              step="1000"
            />
          </div>
          <div className="form-group">
            <label className="label">Max Amount (VND)</label>
            <input
              type="number"
              className="input"
              value={data.mbfg_max_amount || 0}
              onChange={(e) => handleConfigDataChange('mbfg_max_amount', e.target.value)}
              step="1000"
            />
          </div>
          <div className="form-group">
            <label className="label">Revenue Rate (0-1)</label>
            <input
              type="number"
              className="input"
              value={data.mbfg_revenue_rate || 0}
              onChange={(e) => handleConfigDataChange('mbfg_revenue_rate', e.target.value)}
              step="0.01"
            />
          </div>
        </div>
      );
    } else if (type === 'clustering') {
      return (
        <div className="config-fields">
          <h3>K-Means Clustering</h3>
          <div className="form-group">
            <label className="label">Number of Clusters</label>
            <input
              type="number"
              className="input"
              value={data.n_clusters || 3}
              onChange={(e) => handleConfigDataChange('n_clusters', e.target.value)}
              min="2"
              max="10"
            />
          </div>
          <div className="form-group">
            <label className="label">Number of Initializations</label>
            <input
              type="number"
              className="input"
              value={data.n_init || 20}
              onChange={(e) => handleConfigDataChange('n_init', e.target.value)}
              min="1"
              max="100"
            />
          </div>
          <div className="form-group">
            <label className="label">Max Iterations</label>
            <input
              type="number"
              className="input"
              value={data.max_iter || 500}
              onChange={(e) => handleConfigDataChange('max_iter', e.target.value)}
              min="100"
              max="2000"
            />
          </div>
          <div className="form-group">
            <label className="label">Random State</label>
            <input
              type="number"
              className="input"
              value={data.random_state || 42}
              onChange={(e) => handleConfigDataChange('random_state', e.target.value)}
              min="0"
              max="1000"
            />
          </div>
        </div>
      );
    }
  };

  if (loading) {
    return <div className="loading">Đang tải dữ liệu...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  const filteredConfigs = configurations.filter(c => !configType || c.config_type === configType);

  return (
    <div className="configurations">
      <div className="configurations-header">
        <h1>Cấu hình</h1>
        <button className="button button-primary" onClick={handleCreate}>
          <Plus size={20} />
          Tạo cấu hình mới
        </button>
      </div>

      <div className="filter-bar">
        <label className="label">Lọc theo loại:</label>
        <select className="input" value={configType} onChange={(e) => setConfigType(e.target.value)}>
          <option value="">Tất cả</option>
          <option value="bad_debt">Bad Debt Weights</option>
          <option value="business_rules">Business Rules</option>
          <option value="clustering">Clustering Config</option>
        </select>
      </div>

      <div className="card">
        {filteredConfigs.length === 0 ? (
          <div className="empty-state">Chưa có cấu hình nào. Tạo cấu hình mới để bắt đầu.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Tên</th>
                <th>Loại</th>
                <th>Mô tả</th>
                <th>Ngày tạo</th>
                <th>Trạng thái</th>
                <th>Hành động</th>
              </tr>
            </thead>
            <tbody>
              {filteredConfigs.map((config) => (
                <tr key={config.id}>
                  <td>{config.name}</td>
                  <td>
                    <span className="type-badge">
                      {config.config_type === 'bad_debt' && 'Bad Debt'}
                      {config.config_type === 'business_rules' && 'Business Rules'}
                      {config.config_type === 'clustering' && 'Clustering'}
                    </span>
                  </td>
                  <td>{config.description || '-'}</td>
                  <td>{new Date(config.created_at).toLocaleDateString('vi-VN')}</td>
                  <td>
                    {config.is_active ? (
                      <span className="status-badge status-completed">Đang dùng</span>
                    ) : (
                      <span className="status-badge status-pending">Không dùng</span>
                    )}
                  </td>
                  <td>
                    <div className="action-buttons">
                      {!config.is_active && (
                        <button
                          className="button button-success button-sm"
                          onClick={() => handleActivate(config.id)}
                          title="Kích hoạt"
                        >
                          <Check size={16} />
                        </button>
                      )}
                      <button
                        className="button button-secondary button-sm"
                        onClick={() => handleEdit(config)}
                        title="Chỉnh sửa"
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        className="button button-danger button-sm"
                        onClick={() => handleDelete(config.id)}
                        title="Xóa"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">
                {editingConfig ? 'Chỉnh sửa cấu hình' : 'Tạo cấu hình mới'}
              </h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="label">Tên cấu hình *</label>
                <input
                  type="text"
                  className="input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="label">Mô tả</label>
                <textarea
                  className="input"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label className="label">Loại cấu hình *</label>
                <select
                  className="input"
                  value={formData.config_type}
                  onChange={(e) => {
                    const newType = e.target.value;
                    setFormData({
                      ...formData,
                      config_type: newType,
                      config_data: getDefaultConfigData(newType)
                    });
                  }}
                  disabled={!!editingConfig}
                >
                  <option value="bad_debt">Bad Debt Weights</option>
                  <option value="business_rules">Business Rules</option>
                  <option value="clustering">Clustering Config</option>
                </select>
              </div>

              {renderConfigFields()}

              <div className="modal-actions">
                <button type="button" className="button button-secondary" onClick={() => setShowModal(false)}>
                  Hủy
                </button>
                <button type="submit" className="button button-primary">
                  {editingConfig ? 'Cập nhật' : 'Tạo mới'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Configurations;
