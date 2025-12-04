import React, { useState } from 'react';
import { Upload, CheckCircle, XCircle, AlertCircle, FileText, Filter } from 'lucide-react';

const InvoiceQCConsole = () => {
  const [invoices, setInvoices] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filterInvalid, setFilterInvalid] = useState(false);
  const [jsonInput, setJsonInput] = useState('');
  const [mode, setMode] = useState('upload'); // 'upload' or 'json'

  const API_BASE = 'http://localhost:8000';

  const handleFileUpload = async (event) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      const response = await fetch(`${API_BASE}/extract-and-validate-pdfs`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to process PDFs');
      }

      const data = await response.json();
      setInvoices(data.extracted_invoices || []);
      setSummary(data.validation_summary);
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleJsonValidation = async () => {
    if (!jsonInput.trim()) {
      setError('Please enter valid JSON');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const invoicesData = JSON.parse(jsonInput);
      
      const response = await fetch(`${API_BASE}/validate-json`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(invoicesData),
      });

      if (!response.ok) {
        throw new Error('Failed to validate JSON');
      }

      const data = await response.json();
      setInvoices(invoicesData);
      setSummary(data);
    } catch (err) {
      setError(err.message || 'Invalid JSON or validation error');
    } finally {
      setLoading(false);
    }
  };

  const getValidationResults = () => {
    if (!summary || !summary.validation_results) return [];
    
    const results = summary.validation_results;
    if (filterInvalid) {
      return results.filter(r => !r.is_valid);
    }
    return results;
  };

  const getStatusBadge = (isValid) => {
    if (isValid) {
      return (
        <span className="flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
          <CheckCircle size={16} />
          Valid
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1 px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium">
        <XCircle size={16} />
        Invalid
      </span>
    );
  };

  const displayedResults = getValidationResults();

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <FileText className="text-blue-600" size={32} />
            <div>
              <h1 className="text-3xl font-bold text-gray-800">Invoice QC Console</h1>
              <p className="text-gray-600">Quality Control & Validation System</p>
            </div>
          </div>

          {/* Mode Selector */}
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setMode('upload')}
              className={`px-4 py-2 rounded font-medium ${
                mode === 'upload'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Upload PDFs
            </button>
            <button
              onClick={() => setMode('json')}
              className={`px-4 py-2 rounded font-medium ${
                mode === 'json'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Validate JSON
            </button>
          </div>

          {/* Upload Mode */}
          {mode === 'upload' && (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
              <Upload className="mx-auto mb-4 text-gray-400" size={48} />
              <label className="cursor-pointer">
                <span className="text-blue-600 font-medium hover:text-blue-700">
                  Choose PDF files
                </span>
                <input
                  type="file"
                  multiple
                  accept=".pdf"
                  onChange={handleFileUpload}
                  className="hidden"
                  disabled={loading}
                />
              </label>
              <p className="text-gray-500 text-sm mt-2">or drag and drop</p>
            </div>
          )}

          {/* JSON Mode */}
          {mode === 'json' && (
            <div>
              <textarea
                value={jsonInput}
                onChange={(e) => setJsonInput(e.target.value)}
                placeholder='[{"invoice_number": "INV-001", ...}]'
                className="w-full h-32 p-3 border border-gray-300 rounded font-mono text-sm"
                disabled={loading}
              />
              <button
                onClick={handleJsonValidation}
                disabled={loading}
                className="mt-2 px-6 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 disabled:bg-gray-400"
              >
                {loading ? 'Validating...' : 'Validate JSON'}
              </button>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded flex items-start gap-2">
              <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="mt-4 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
              <p className="mt-2 text-gray-600">Processing...</p>
            </div>
          )}
        </div>

        {/* Summary Stats */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-gray-600 text-sm">Total Invoices</p>
              <p className="text-3xl font-bold text-gray-800">{summary.total_invoices}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-gray-600 text-sm">Valid</p>
              <p className="text-3xl font-bold text-green-600">{summary.valid_invoices}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-gray-600 text-sm">Invalid</p>
              <p className="text-3xl font-bold text-red-600">{summary.invalid_invoices}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-gray-600 text-sm">Error Types</p>
              <p className="text-3xl font-bold text-orange-600">
                {Object.keys(summary.error_counts || {}).length}
              </p>
            </div>
          </div>
        )}

        {/* Results Table */}
        {displayedResults.length > 0 && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-800">Validation Results</h2>
              <button
                onClick={() => setFilterInvalid(!filterInvalid)}
                className={`flex items-center gap-2 px-4 py-2 rounded font-medium ${
                  filterInvalid
                    ? 'bg-red-100 text-red-800'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Filter size={16} />
                {filterInvalid ? 'Show All' : 'Show Invalid Only'}
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Invoice ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Errors
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {displayedResults.map((result, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">
                        {result.invoice_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(result.is_valid)}
                      </td>
                      <td className="px-6 py-4">
                        {result.errors && result.errors.length > 0 ? (
                          <div className="space-y-1">
                            {result.errors.map((err, errIndex) => (
                              <div
                                key={errIndex}
                                className="text-sm text-red-600 flex items-start gap-2"
                              >
                                <span className="font-mono text-xs bg-red-50 px-2 py-1 rounded">
                                  {err.rule}
                                </span>
                                <span>{err.message}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="text-green-600 text-sm">No errors</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && displayedResults.length === 0 && summary && (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <CheckCircle className="mx-auto mb-4 text-green-500" size={64} />
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              {filterInvalid ? 'No Invalid Invoices' : 'No Results'}
            </h3>
            <p className="text-gray-600">
              {filterInvalid
                ? 'All invoices passed validation!'
                : 'Upload PDFs or paste JSON to get started'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default InvoiceQCConsole;