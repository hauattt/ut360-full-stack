import { useState, useEffect } from 'react';
import axios from 'axios';

export default function FileSelection() {
  const [folders, setFolders] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedFiles, setSelectedFiles] = useState({
    n1_files: [],
    n2_files: [],
    n3_files: [],
    n4_files: [],
    n5_files: [],
    n6_files: [],
    n7_files: [],
    n8_files: [],
    n10_files: []
  });
  const [runningPipeline, setRunningPipeline] = useState(false);
  const [runId, setRunId] = useState(null);
  const [selectedMonths, setSelectedMonths] = useState(new Set());

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/data/files');
      console.log('API Response:', response.data);

      if (response.data && response.data.folders) {
        setFolders(response.data.folders);
      } else {
        console.error('Invalid response format:', response.data);
        alert('Lỗi: Định dạng dữ liệu không đúng');
      }
    } catch (error) {
      console.error('Error fetching files:', error);
      console.error('Error details:', error.response?.data || error.message);
      alert(`Lỗi khi tải danh sách file: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const toggleFile = (folderKey, filePath) => {
    setSelectedFiles(prev => {
      const currentFiles = prev[folderKey] || [];
      const isSelected = currentFiles.includes(filePath);

      return {
        ...prev,
        [folderKey]: isSelected
          ? currentFiles.filter(f => f !== filePath)
          : [...currentFiles, filePath]
      };
    });
  };

  const selectAllInFolder = (folderKey, files) => {
    setSelectedFiles(prev => ({
      ...prev,
      [folderKey]: files.map(f => f.path)
    }));
  };

  const deselectAllInFolder = (folderKey) => {
    setSelectedFiles(prev => ({
      ...prev,
      [folderKey]: []
    }));
  };

  const selectByMonth = (month) => {
    const newSelected = { ...selectedFiles };
    Object.entries(folders).forEach(([folderName, folderData]) => {
      if (folderData?.exists && folderData?.files?.length > 0) {
        const folderKey = `${folderName.toLowerCase()}_files`;
        const monthFiles = folderData.files.filter(f => f.month === month);
        newSelected[folderKey] = monthFiles.map(f => f.path);
      }
    });
    setSelectedFiles(newSelected);
    setSelectedMonths(new Set([month]));
  };

  const toggleMonth = (month) => {
    const newMonths = new Set(selectedMonths);
    const isSelected = newMonths.has(month);

    if (isSelected) {
      newMonths.delete(month);
      // Deselect all files of this month
      const newSelected = { ...selectedFiles };
      Object.entries(folders).forEach(([folderName, folderData]) => {
        if (folderData?.exists && folderData?.files?.length > 0) {
          const folderKey = `${folderName.toLowerCase()}_files`;
          const currentFiles = selectedFiles[folderKey] || [];
          const monthFiles = folderData.files.filter(f => f.month === month).map(f => f.path);
          newSelected[folderKey] = currentFiles.filter(path => !monthFiles.includes(path));
        }
      });
      setSelectedFiles(newSelected);
    } else {
      newMonths.add(month);
      // Select all files of this month
      const newSelected = { ...selectedFiles };
      Object.entries(folders).forEach(([folderName, folderData]) => {
        if (folderData?.exists && folderData?.files?.length > 0) {
          const folderKey = `${folderName.toLowerCase()}_files`;
          const monthFiles = folderData.files.filter(f => f.month === month).map(f => f.path);
          const currentFiles = selectedFiles[folderKey] || [];
          newSelected[folderKey] = [...new Set([...currentFiles, ...monthFiles])];
        }
      });
      setSelectedFiles(newSelected);
    }
    setSelectedMonths(newMonths);
  };

  const selectAll = () => {
    const newSelected = {};
    Object.entries(folders).forEach(([folderName, folderData]) => {
      if (folderData?.exists && folderData?.files?.length > 0) {
        const folderKey = `${folderName.toLowerCase()}_files`;
        newSelected[folderKey] = folderData.files.map(f => f.path);
      }
    });
    setSelectedFiles(newSelected);
  };

  const deselectAll = () => {
    setSelectedFiles({
      n1_files: [],
      n2_files: [],
      n3_files: [],
      n4_files: [],
      n5_files: [],
      n6_files: [],
      n7_files: [],
      n8_files: [],
      n10_files: []
    });
    setSelectedMonths(new Set());
  };

  const runPipeline = async () => {
    const hasSelectedFiles = Object.values(selectedFiles).some(files => files.length > 0);

    if (!hasSelectedFiles) {
      alert('Vui lòng chọn ít nhất 1 file');
      return;
    }

    try {
      setRunningPipeline(true);
      const response = await axios.post('/api/pipeline/run', {
        phases: ['phase1', 'phase2', 'phase3a', 'phase3b', 'phase4', 'phase5'],
        file_selection: selectedFiles
      });

      setRunId(response.data.id);
      alert(`Pipeline đã được khởi chạy!\nRun ID: ${response.data.id}`);
    } catch (error) {
      console.error('Error running pipeline:', error);
      alert('Lỗi khi chạy pipeline');
    } finally {
      setRunningPipeline(false);
    }
  };

  const folderNames = {
    N1: 'ARPU Data',
    N2: 'Package Data',
    N3: 'Usage Data',
    N4: 'Advance Data',
    N5: 'Topup Data',
    N6: 'Usage Detail',
    N7: 'Location Data',
    N8: 'Device Data',
    N10: 'Subscriber Info'
  };

  // Get all unique months
  const allMonths = [...new Set(
    Object.values(folders).flatMap(folder =>
      folder?.files?.map(f => f.month) || []
    )
  )].sort();

  // Calculate total selected
  const totalSelected = Object.values(selectedFiles).reduce((sum, files) => sum + files.length, 0);
  const totalFiles = Object.values(folders).reduce((sum, folder) => sum + (folder?.files?.length || 0), 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-xl">Đang tải danh sách file...</div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '2rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '0.5rem', color: '#333' }}>
          Chọn File Dữ Liệu Đầu Vào
        </h1>
        <p style={{ fontSize: '0.875rem', color: '#666' }}>
          Đã chọn: <span style={{ fontWeight: '600', color: '#667eea' }}>{totalSelected}</span> / {totalFiles} files
        </p>
      </div>

      {/* Quick Selection by Month */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 className="card-title" style={{ margin: 0 }}>Chọn nhanh theo tháng:</h3>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={selectAll}
              className="button button-primary"
              style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
            >
              Chọn tất cả
            </button>
            <button
              onClick={deselectAll}
              className="button button-secondary"
              style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
            >
              Bỏ chọn tất cả
            </button>
          </div>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {allMonths.map(month => {
            const isMonthSelected = selectedMonths.has(month);
            return (
              <button
                key={month}
                onClick={() => toggleMonth(month)}
                style={{
                  padding: '0.5rem 1rem',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'all 0.3s',
                  background: isMonthSelected ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#e0e0e0',
                  color: isMonthSelected ? 'white' : '#333'
                }}
              >
                Tháng {month}
              </button>
            );
          })}
        </div>
      </div>

      {/* Table View */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="table">
          <thead>
            <tr>
              <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#555', background: '#f9f9f9' }}>Folder</th>
              {allMonths.map(month => (
                <th key={month} style={{ padding: '1rem', textAlign: 'center', fontWeight: '600', color: '#555', background: '#f9f9f9' }}>
                  {month}
                </th>
              ))}
              <th style={{ padding: '1rem', textAlign: 'center', fontWeight: '600', color: '#555', background: '#f9f9f9' }}>Đã chọn</th>
              <th style={{ padding: '1rem', textAlign: 'center', fontWeight: '600', color: '#555', background: '#f9f9f9' }}>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(folders).map(([folderName, folderData]) => {
              if (!folderData || !folderData.exists || !folderData.files || folderData.files.length === 0) return null;

              const folderKey = `${folderName.toLowerCase()}_files`;
              const selectedInFolder = selectedFiles[folderKey] || [];

              return (
                <tr key={folderName}>
                  <td style={{ padding: '1rem' }}>
                    <div style={{ fontWeight: '600', color: '#333' }}>{folderName}</div>
                    <div style={{ fontSize: '0.75rem', color: '#888' }}>{folderNames[folderName]}</div>
                  </td>
                  {allMonths.map(month => {
                    const file = folderData.files.find(f => f.month === month);
                    if (!file) {
                      return <td key={month} style={{ padding: '1rem', textAlign: 'center', color: '#ccc' }}>-</td>;
                    }
                    const isSelected = selectedInFolder.includes(file.path);
                    return (
                      <td key={month} style={{ padding: '1rem', textAlign: 'center' }}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleFile(folderKey, file.path)}
                          style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                        />
                      </td>
                    );
                  })}
                  <td style={{ padding: '1rem', textAlign: 'center' }}>
                    <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#667eea' }}>
                      {selectedInFolder.length}/{folderData.files.length}
                    </span>
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center' }}>
                    <button
                      onClick={() => selectAllInFolder(folderKey, folderData.files)}
                      style={{ fontSize: '0.75rem', color: '#667eea', background: 'none', border: 'none', cursor: 'pointer', marginRight: '0.5rem' }}
                    >
                      Tất cả
                    </button>
                    <button
                      onClick={() => deselectAllInFolder(folderKey)}
                      style={{ fontSize: '0.75rem', color: '#888', background: 'none', border: 'none', cursor: 'pointer' }}
                    >
                      Bỏ
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Summary & Run Button */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 className="card-title" style={{ margin: 0, marginBottom: '0.25rem' }}>Sẵn sàng chạy Pipeline</h3>
            <p style={{ fontSize: '0.875rem', color: '#666' }}>
              {totalSelected > 0 ? (
                <>Đã chọn <span style={{ fontWeight: '600', color: '#667eea' }}>{totalSelected} files</span> từ {Object.values(selectedFiles).filter(f => f.length > 0).length} folders</>
              ) : (
                <span style={{ color: '#f44336' }}>Vui lòng chọn ít nhất 1 file để tiếp tục</span>
              )}
            </p>
          </div>
          <button
            onClick={runPipeline}
            disabled={runningPipeline || totalSelected === 0}
            className="button button-success"
          >
            {runningPipeline ? 'Đang khởi chạy...' : 'Chạy Pipeline'}
          </button>
        </div>

        {runId && (
          <div className="status-completed" style={{ marginTop: '1rem', padding: '1rem', borderRadius: '6px' }}>
            <p style={{ fontSize: '0.875rem', fontWeight: '500' }}>
              ✅ Pipeline đã được khởi chạy với Run ID: <strong style={{ fontFamily: 'monospace' }}>{runId}</strong>
            </p>
            <p style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
              Xem tiến trình tại trang Pipeline Runs
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
