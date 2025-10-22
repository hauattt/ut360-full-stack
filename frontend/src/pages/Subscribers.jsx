import React, { useState, useEffect } from 'react';
import { Users, Search, Eye, Download } from 'lucide-react';
import axios from 'axios';
import Profile360Modal from '../components/Profile360Modal';
import './Subscribers.css';

function Subscribers() {
  const [subscribers, setSubscribers] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedSubscriber, setSelectedSubscriber] = useState(null);
  const [showDetail, setShowDetail] = useState(false);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [serviceTypeFilter, setServiceTypeFilter] = useState('all');
  const [riskFilter, setRiskFilter] = useState('all');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 50;

  // Load subscribers whenever filters or page changes
  useEffect(() => {
    loadSubscribers();
  }, [currentPage, searchTerm, serviceTypeFilter, riskFilter]);

  const loadSubscribers = async () => {
    setLoading(true);
    setError(null);
    try {
      const offset = (currentPage - 1) * itemsPerPage;
      const params = new URLSearchParams({
        limit: itemsPerPage,
        offset: offset
      });

      if (searchTerm) params.append('search', searchTerm);
      if (serviceTypeFilter !== 'all') params.append('service_type', serviceTypeFilter);
      if (riskFilter !== 'all') params.append('risk_level', riskFilter);

      const response = await axios.get(`/api/subscribers/list?${params.toString()}`);
      setSubscribers(response.data.subscribers || []);
      setTotalCount(response.data.total || 0);
    } catch (err) {
      setError('Lỗi khi tải danh sách thuê bao: ' + err.message);
      console.error('Error loading subscribers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setSearchTerm(searchInput);
    setCurrentPage(1);
  };

  const handleFilterChange = (filterType, value) => {
    if (filterType === 'service') {
      setServiceTypeFilter(value);
    } else if (filterType === 'risk') {
      setRiskFilter(value);
    }
    setCurrentPage(1);
  };

  const viewSubscriberDetail = async (isdn) => {
    try {
      const response = await axios.get(`/api/subscribers/profile`, {
        params: { isdn: isdn }
      });
      setSelectedSubscriber(response.data);
      setShowDetail(true);
    } catch (err) {
      alert('Lỗi khi tải chi tiết thuê bao: ' + err.message);
      console.error('Error:', err);
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

  const getRiskBadgeClass = (risk) => {
    if (risk === 'LOW') return 'risk-badge-low';
    if (risk === 'MEDIUM') return 'risk-badge-medium';
    return 'risk-badge-high';
  };

  const getServiceBadgeClass = (serviceType) => {
    if (serviceType === 'EasyCredit') return 'service-badge-fee';
    if (serviceType === 'MBFG') return 'service-badge-free';
    return 'service-badge-quota';
  };

  const exportToCSV = () => {
    alert('Export feature coming soon!');
  };

  // Pagination
  const totalPages = Math.ceil(totalCount / itemsPerPage);

  return (
    <div className="subscribers-page">
      <div className="page-header">
        <div className="header-content">
          <Users size={32} />
          <div>
            <h1>Danh sách thuê bao</h1>
            <p>Kết quả cuối cùng sau khi lọc bad debt risk</p>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="results-summary">
        <div className="summary-item">
          <span className="summary-label">Tổng kết quả:</span>
          <span className="summary-value">{formatNumber(totalCount)} thuê bao</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Trang hiện tại:</span>
          <span className="summary-value">{currentPage} / {totalPages}</span>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <div className="search-box">
          <Search size={18} />
          <input
            type="text"
            placeholder="Tìm kiếm ISDN..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button className="btn-search" onClick={handleSearch}>Tìm</button>
        </div>

        <select value={serviceTypeFilter} onChange={(e) => handleFilterChange('service', e.target.value)}>
          <option value="all">Tất cả service type</option>
          <option value="EasyCredit">Fee</option>
          <option value="MBFG">Free</option>
          <option value="ungsanluong">Quota</option>
        </select>

        <select value={riskFilter} onChange={(e) => handleFilterChange('risk', e.target.value)}>
          <option value="all">Tất cả risk level</option>
          <option value="LOW">LOW</option>
          <option value="MEDIUM">MEDIUM</option>
        </select>

        <button className="btn-export" onClick={exportToCSV} disabled>
          <Download size={18} />
          Export CSV
        </button>
      </div>

      {/* Table */}
      {loading ? (
        <div className="loading">Đang tải dữ liệu...</div>
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : (
        <>
          <div className="table-container">
            <table className="subscribers-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>ISDN</th>
                  <th>Type</th>
                  <th>Service</th>
                  <th>Advance</th>
                  <th>Revenue</th>
                  <th>ARPU</th>
                  <th>Risk</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {subscribers.map((sub, idx) => (
                  <tr key={sub.isdn}>
                    <td>{(currentPage - 1) * itemsPerPage + idx + 1}</td>
                    <td className="isdn-cell">{sub.isdn}</td>
                    <td>
                      <span className={`subscriber-type-badge ${sub.subscriber_type === 'PRE' ? 'type-pre' : 'type-pos'}`}>
                        {sub.subscriber_type || 'PRE'}
                      </span>
                    </td>
                    <td>
                      <span className={`service-badge ${getServiceBadgeClass(sub.service_type)}`}>
                        {formatServiceType(sub.service_type)}
                      </span>
                    </td>
                    <td className="number-cell">{formatCurrency(sub.advance_amount)}</td>
                    <td className="number-cell">{formatCurrency(sub.revenue_per_advance)}</td>
                    <td className="number-cell">{formatCurrency(sub.arpu)}</td>
                    <td>
                      <span className={`risk-badge ${getRiskBadgeClass(sub.bad_debt_risk)}`}>
                        {sub.bad_debt_risk}
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn-view-detail"
                        onClick={() => viewSubscriberDetail(sub.isdn)}
                      >
                        <Eye size={16} />
                        Chi tiết
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1 || loading}
            >
              ← Trước
            </button>
            <span>
              Trang {currentPage} / {totalPages} ({formatNumber(totalCount)} thuê bao)
            </span>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages || loading}
            >
              Sau →
            </button>
          </div>
        </>
      )}

      {/* Detail Modal - 360 Profile */}
      {showDetail && selectedSubscriber && (
        <Profile360Modal
          profile={selectedSubscriber}
          monthlyArpu={selectedSubscriber.monthly_arpu}
          onClose={() => setShowDetail(false)}
        />
      )}
    </div>
  );
}

export default Subscribers;
