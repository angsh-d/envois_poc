import { useState, useEffect, useCallback } from 'react'
import StudyLayout from './StudyLayout'
import {
  Database,
  Table2,
  ChevronLeft,
  ChevronRight,
  Edit2,
  X,
  Save,
  RefreshCw,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
} from 'lucide-react'
import {
  fetchDataBrowserTables,
  fetchDataBrowserTableData,
  updateDataBrowserRow,
  DataBrowserTableInfo,
  DataBrowserColumnSchema,
} from '../lib/api'

interface DataBrowserProps {
  params: { studyId: string }
}

export default function DataBrowser({ params }: DataBrowserProps) {
  const [tables, setTables] = useState<DataBrowserTableInfo[]>([])
  const [selectedTable, setSelectedTable] = useState<string>('')
  const [rows, setRows] = useState<Record<string, unknown>[]>([])
  const [columns, setColumns] = useState<DataBrowserColumnSchema[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [limit] = useState(25)
  const [sortBy, setSortBy] = useState<string | undefined>()
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [loading, setLoading] = useState(false)
  const [editingRow, setEditingRow] = useState<Record<string, unknown> | null>(null)
  const [editValues, setEditValues] = useState<Record<string, unknown>>({})
  const [saving, setSaving] = useState(false)

  // Load tables list
  useEffect(() => {
    const loadTables = async () => {
      try {
        const data = await fetchDataBrowserTables()
        setTables(data)
        if (data.length > 0 && !selectedTable) {
          setSelectedTable(data[0].name)
        }
      } catch (error) {
        console.error('Failed to load tables:', error)
      }
    }
    loadTables()
  }, [])

  // Load table data when selection changes
  const loadTableData = useCallback(async () => {
    if (!selectedTable) return
    setLoading(true)
    try {
      const data = await fetchDataBrowserTableData(selectedTable, page, limit, sortBy, sortDir)
      setRows(data.rows)
      setColumns(data.columns)
      setTotal(data.total)
    } catch (error) {
      console.error('Failed to load table data:', error)
    } finally {
      setLoading(false)
    }
  }, [selectedTable, page, limit, sortBy, sortDir])

  useEffect(() => {
    loadTableData()
  }, [loadTableData])

  const handleSort = (columnName: string) => {
    if (sortBy === columnName) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(columnName)
      setSortDir('asc')
    }
  }

  const handleEdit = (row: Record<string, unknown>) => {
    setEditingRow(row)
    setEditValues({ ...row })
  }

  const handleCancelEdit = () => {
    setEditingRow(null)
    setEditValues({})
  }

  const handleSave = async () => {
    if (!editingRow || !selectedTable) return

    const pkColumn = columns.find(c => c.primary_key)
    if (!pkColumn) return

    const rowId = editingRow[pkColumn.name] as number

    setSaving(true)
    try {
      await updateDataBrowserRow(selectedTable, rowId, editValues)
      await loadTableData()
      setEditingRow(null)
      setEditValues({})
    } catch (error) {
      console.error('Failed to save:', error)
    } finally {
      setSaving(false)
    }
  }

  const totalPages = Math.ceil(total / limit)
  const selectedTableInfo = tables.find(t => t.name === selectedTable)

  const formatValue = (value: unknown): string => {
    if (value === null || value === undefined) return '-'
    if (typeof value === 'object') return JSON.stringify(value)
    return String(value)
  }

  return (
    <StudyLayout studyId={params.studyId} chatContext="data-browser">
      <div className="max-w-full mx-auto space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Data Browser</h1>
            <p className="text-gray-500 mt-1">View and edit database tables</p>
          </div>
          <button
            onClick={loadTableData}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Table Selector */}
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-gray-600" />
              <label className="text-sm font-medium text-gray-700">Select Table:</label>
            </div>
            <select
              value={selectedTable}
              onChange={(e) => {
                setSelectedTable(e.target.value)
                setPage(1)
                setSortBy(undefined)
              }}
              className="flex-1 max-w-md px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
            >
              {tables.map((table) => (
                <option key={table.name} value={table.name}>
                  {table.name} ({table.row_count} rows)
                </option>
              ))}
            </select>
          </div>
          {selectedTableInfo && (
            <p className="mt-2 text-sm text-gray-500 ml-7">{selectedTableInfo.description}</p>
          )}
        </div>

        {/* Data Grid */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Table2 className="w-5 h-5 text-gray-600" />
              <h3 className="font-semibold text-gray-900">{selectedTable}</h3>
              <span className="text-sm text-gray-500">({total} total rows)</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              Page {page} of {totalPages || 1}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-gray-500 font-medium w-16">Actions</th>
                  {columns.map((col) => (
                    <th
                      key={col.name}
                      className="px-4 py-3 text-left text-gray-500 font-medium cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort(col.name)}
                    >
                      <div className="flex items-center gap-1">
                        <span className={col.primary_key ? 'text-blue-600' : ''}>
                          {col.name}
                        </span>
                        {sortBy === col.name ? (
                          sortDir === 'asc' ? (
                            <ArrowUp className="w-4 h-4" />
                          ) : (
                            <ArrowDown className="w-4 h-4" />
                          )
                        ) : (
                          <ArrowUpDown className="w-4 h-4 text-gray-300" />
                        )}
                      </div>
                      <div className="text-xs text-gray-400 font-normal">{col.type}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {loading ? (
                  <tr>
                    <td colSpan={columns.length + 1} className="px-4 py-8 text-center text-gray-500">
                      Loading...
                    </td>
                  </tr>
                ) : rows.length === 0 ? (
                  <tr>
                    <td colSpan={columns.length + 1} className="px-4 py-8 text-center text-gray-500">
                      No data found
                    </td>
                  </tr>
                ) : (
                  rows.map((row, idx) => {
                    const pkColumn = columns.find(c => c.primary_key)
                    const rowKey = pkColumn ? String(row[pkColumn.name]) : idx

                    return (
                      <tr key={rowKey} className="hover:bg-gray-50">
                        <td className="px-4 py-2">
                          <button
                            onClick={() => handleEdit(row)}
                            className="p-1 text-gray-400 hover:text-gray-600 rounded"
                            title="Edit row"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                        </td>
                        {columns.map((col) => (
                          <td key={col.name} className="px-4 py-2 text-gray-800 max-w-xs truncate">
                            {formatValue(row[col.name])}
                          </td>
                        ))}
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Showing {Math.min((page - 1) * limit + 1, total)} - {Math.min(page * limit, total)} of {total}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <span className="text-sm text-gray-600 min-w-[100px] text-center">
                Page {page} of {totalPages || 1}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page >= totalPages}
                className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Edit Modal */}
        {editingRow && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="font-semibold text-gray-900">Edit Row</h3>
                <button
                  onClick={handleCancelEdit}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 overflow-y-auto max-h-[60vh]">
                <div className="space-y-4">
                  {columns.map((col) => (
                    <div key={col.name}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {col.name}
                        {col.primary_key && (
                          <span className="ml-2 text-xs text-blue-600">(Primary Key)</span>
                        )}
                        <span className="ml-2 text-xs text-gray-400">{col.type}</span>
                      </label>
                      {col.primary_key ? (
                        <input
                          type="text"
                          value={formatValue(editValues[col.name])}
                          disabled
                          className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500"
                        />
                      ) : col.type.includes('JSON') ? (
                        <textarea
                          value={typeof editValues[col.name] === 'object'
                            ? JSON.stringify(editValues[col.name], null, 2)
                            : String(editValues[col.name] ?? '')}
                          onChange={(e) => {
                            try {
                              const parsed = JSON.parse(e.target.value)
                              setEditValues({ ...editValues, [col.name]: parsed })
                            } catch {
                              setEditValues({ ...editValues, [col.name]: e.target.value })
                            }
                          }}
                          rows={4}
                          className="w-full px-3 py-2 border border-gray-200 rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                        />
                      ) : col.type.includes('BOOLEAN') ? (
                        <select
                          value={String(editValues[col.name] ?? '')}
                          onChange={(e) => setEditValues({
                            ...editValues,
                            [col.name]: e.target.value === 'true' ? true : e.target.value === 'false' ? false : null
                          })}
                          className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
                        >
                          <option value="">-</option>
                          <option value="true">true</option>
                          <option value="false">false</option>
                        </select>
                      ) : col.type.includes('TEXT') ? (
                        <textarea
                          value={String(editValues[col.name] ?? '')}
                          onChange={(e) => setEditValues({ ...editValues, [col.name]: e.target.value || null })}
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
                        />
                      ) : (
                        <input
                          type={col.type.includes('INTEGER') || col.type.includes('FLOAT') ? 'number' : 'text'}
                          value={String(editValues[col.name] ?? '')}
                          onChange={(e) => {
                            let value: unknown = e.target.value || null
                            if (value && (col.type.includes('INTEGER') || col.type.includes('FLOAT'))) {
                              value = col.type.includes('INTEGER') ? parseInt(e.target.value) : parseFloat(e.target.value)
                            }
                            setEditValues({ ...editValues, [col.name]: value })
                          }}
                          className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>
              <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3">
                <button
                  onClick={handleCancelEdit}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </StudyLayout>
  )
}
