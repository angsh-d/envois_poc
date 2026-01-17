import { useState } from 'react'
import { Folder, FileText, Check, X, Database, BookOpen, Loader2, FolderOpen, AlertCircle } from 'lucide-react'

export interface FileInfo {
  id: string
  name: string
  path: string
  size?: number
  type?: string
  validated?: boolean
  stats?: {
    rows?: number
    tables?: number
    pages?: number
  }
}

// Analysis results for study data files (Excel/CSV)
export interface StudyDataAnalysis {
  fileName: string
  rows: number
  columns: number
  columnNames: string[]
  dataTypes: Record<string, string>
  sampleValues: Record<string, string[]>
  dateRange?: { start: string; end: string }
  keyInsights?: string[]
}

// Analysis results for protocol document
export interface ProtocolAnalysis {
  fileName: string
  pages: number
  studyTitle: string
  indication: string
  studyPhase: string
  primaryEndpoints: string[]
  secondaryEndpoints: string[]
  populationSize: string
  followUpDuration: string
  inclusionCriteriaSummary?: string
  extractedSections?: string[]
}

// Analysis results for literature PDFs
export interface LiteratureAnalysis {
  fileName: string
  title: string
  authors: string
  journal: string
  year: number
  pages: number
  relevanceScore: number
  keyFindings: string[]
  studyType?: string
  sampleSize?: string
}

// Analysis results for extracted JSON files
export interface ExtractedJsonAnalysis {
  fileName: string
  schemaType: string
  recordCount: number
  keyFields: string[]
  dataPreview: Record<string, unknown>
  lastUpdated?: string
}

export interface FolderContents {
  path: string
  validated: boolean
  studyData: {
    count: number
    files: string[]
    analysis?: StudyDataAnalysis[]
  }
  protocol: {
    found: boolean
    file: string | null
    analysis?: ProtocolAnalysis
  }
  literature: {
    count: number
    files: string[]
    analysis?: LiteratureAnalysis[]
  }
  extractedJson: {
    count: number
    files: string[]
    analysis?: ExtractedJsonAnalysis[]
  }
}

interface LocalDataConfigProps {
  folderPath: string
  folderContents: FolderContents | null
  onFolderPathChange: (path: string) => void
  onValidateFolder?: (path: string) => Promise<FolderContents>
  disabled?: boolean
}

export function LocalDataConfig({
  folderPath,
  folderContents,
  onFolderPathChange,
  onValidateFolder,
  disabled = false,
}: LocalDataConfigProps) {
  const [isValidating, setIsValidating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [browseHint, setBrowseHint] = useState<string | null>(null)

  const handlePathChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null)
    setBrowseHint(null)
    onFolderPathChange(e.target.value)
  }

  const handleValidate = async () => {
    if (!folderPath.trim() || !onValidateFolder) return

    setIsValidating(true)
    setError(null)

    try {
      await onValidateFolder(folderPath)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to validate folder')
    } finally {
      setIsValidating(false)
    }
  }

  const handleBrowse = async () => {
    setError(null)
    setBrowseHint(null)

    // Use File System Access API if available (modern browsers)
    if ('showDirectoryPicker' in window) {
      try {
        const dirHandle = await (window as any).showDirectoryPicker({
          mode: 'read',
        })
        // Get the directory name - we can't get full path for security reasons
        // but we can at least show the folder name was selected
        const folderName = dirHandle.name

        // For local development, construct a likely path based on common patterns
        // User may need to adjust to their actual path
        const suggestedPath = `./${folderName}`
        onFolderPathChange(suggestedPath)

        // Show a hint that the user should verify the path
        setBrowseHint(`Selected "${folderName}". Adjust the path if needed, then click Validate.`)
      } catch (err) {
        // User cancelled the picker or permission denied
        if ((err as Error).name !== 'AbortError') {
          setError('Could not access folder. Please enter the path manually.')
        }
      }
    } else {
      // Fallback for browsers without File System Access API
      setBrowseHint('Enter the full path to your data folder, then click Validate.')
      const input = document.getElementById('folder-path-input')
      input?.focus()
    }
  }

  const totalFiles = folderContents
    ? folderContents.studyData.count +
      (folderContents.protocol.found ? 1 : 0) +
      folderContents.literature.count +
      folderContents.extractedJson.count
    : 0

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <label className="text-xs font-medium text-neutral-500 uppercase tracking-wider">
          Study Data Folder
        </label>
        {folderContents?.validated && (
          <span className="inline-flex items-center gap-1 text-xs text-emerald-600">
            <Check className="w-3.5 h-3.5" />
            {totalFiles} files found
          </span>
        )}
      </div>

      {/* Folder Path Input */}
      <div className="space-y-3">
        <div
          className={`
            relative border rounded-xl transition-all duration-200
            ${folderContents?.validated
              ? 'border-emerald-200 bg-emerald-50/30'
              : error
                ? 'border-red-200 bg-red-50/30'
                : 'border-neutral-200 bg-white'
            }
          `}
        >
          <div className="p-4">
            <div className="flex items-start gap-3">
              <div className={`
                w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0
                ${folderContents?.validated ? 'bg-emerald-100' : 'bg-neutral-100'}
              `}>
                {folderContents?.validated ? (
                  <FolderOpen className="w-5 h-5 text-emerald-600" />
                ) : (
                  <Folder className="w-5 h-5 text-neutral-400" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <input
                  id="folder-path-input"
                  type="text"
                  value={folderPath}
                  onChange={handlePathChange}
                  disabled={disabled}
                  placeholder="./demo_data or /absolute/path/to/folder"
                  className={`
                    w-full px-0 py-1 bg-transparent border-0 text-sm font-medium text-neutral-900
                    placeholder-neutral-400 focus:outline-none focus:ring-0
                    ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                />
                <p className="text-xs text-neutral-500 mt-1">
                  Point to your local folder, EDC export, CTMS folder, or SharePoint sync location
                </p>
              </div>

              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={handleBrowse}
                  disabled={disabled}
                  className="px-3 py-1.5 text-xs font-medium text-neutral-600 bg-neutral-100 rounded-lg hover:bg-neutral-200 transition-colors disabled:opacity-50"
                >
                  Browse
                </button>
                <button
                  onClick={handleValidate}
                  disabled={disabled || !folderPath.trim() || isValidating}
                  className={`
                    px-3 py-1.5 text-xs font-medium rounded-lg transition-colors disabled:opacity-50
                    ${folderContents?.validated
                      ? 'text-emerald-700 bg-emerald-100 hover:bg-emerald-200'
                      : 'text-white bg-neutral-900 hover:bg-neutral-800'
                    }
                  `}
                >
                  {isValidating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : folderContents?.validated ? (
                    'Rescan'
                  ) : (
                    'Validate'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="flex items-center gap-2 text-sm text-red-600">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {/* Browse Hint */}
        {browseHint && !error && (
          <div className="flex items-center gap-2 text-sm text-blue-600">
            <Folder className="w-4 h-4" />
            {browseHint}
          </div>
        )}

        {/* Folder Contents Summary */}
        {folderContents?.validated && (
          <div className="grid grid-cols-2 gap-2">
            {/* Study Data */}
            <div className="p-3 bg-neutral-50 rounded-lg">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-neutral-500" />
                <span className="text-xs font-medium text-neutral-700">Study Data</span>
                <span className={`
                  ml-auto text-xs font-medium px-1.5 py-0.5 rounded
                  ${folderContents.studyData.count > 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-neutral-200 text-neutral-500'}
                `}>
                  {folderContents.studyData.count}
                </span>
              </div>
              {folderContents.studyData.count > 0 && (
                <p className="text-xs text-neutral-500 mt-1 truncate">
                  {folderContents.studyData.files.slice(0, 2).join(', ')}
                  {folderContents.studyData.count > 2 && ` +${folderContents.studyData.count - 2} more`}
                </p>
              )}
            </div>

            {/* Protocol */}
            <div className="p-3 bg-neutral-50 rounded-lg">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-neutral-500" />
                <span className="text-xs font-medium text-neutral-700">Protocol</span>
                <span className={`
                  ml-auto text-xs font-medium px-1.5 py-0.5 rounded
                  ${folderContents.protocol.found ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}
                `}>
                  {folderContents.protocol.found ? '1' : '0'}
                </span>
              </div>
              {folderContents.protocol.file && (
                <p className="text-xs text-neutral-500 mt-1 truncate">
                  {folderContents.protocol.file}
                </p>
              )}
            </div>

            {/* Literature */}
            <div className="p-3 bg-neutral-50 rounded-lg">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-neutral-500" />
                <span className="text-xs font-medium text-neutral-700">Literature</span>
                <span className={`
                  ml-auto text-xs font-medium px-1.5 py-0.5 rounded
                  ${folderContents.literature.count > 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-neutral-200 text-neutral-500'}
                `}>
                  {folderContents.literature.count}
                </span>
              </div>
              {folderContents.literature.count > 0 && (
                <p className="text-xs text-neutral-500 mt-1 truncate">
                  {folderContents.literature.files.slice(0, 2).join(', ')}
                  {folderContents.literature.count > 2 && ` +${folderContents.literature.count - 2} more`}
                </p>
              )}
            </div>

            {/* Extracted JSON */}
            <div className="p-3 bg-neutral-50 rounded-lg">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-neutral-500" />
                <span className="text-xs font-medium text-neutral-700">Extracted JSON</span>
                <span className={`
                  ml-auto text-xs font-medium px-1.5 py-0.5 rounded
                  ${folderContents.extractedJson.count > 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-neutral-200 text-neutral-500'}
                `}>
                  {folderContents.extractedJson.count}
                </span>
              </div>
              {folderContents.extractedJson.count > 0 && (
                <p className="text-xs text-neutral-500 mt-1 truncate">
                  {folderContents.extractedJson.files.slice(0, 2).join(', ')}
                  {folderContents.extractedJson.count > 2 && ` +${folderContents.extractedJson.count - 2} more`}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Help Text */}
        {!folderContents?.validated && (
          <div className="text-xs text-neutral-400 space-y-1">
            <p>The folder should contain:</p>
            <ul className="list-disc list-inside pl-2 space-y-0.5">
              <li>Study data files (Excel, CSV)</li>
              <li>Protocol document (PDF) and extracted JSONs</li>
              <li>Licensed literature PDFs</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

// Compact inline version for displaying configured sources
interface ConfiguredSourceProps {
  label: string
  fileName: string
  count?: number
  icon: 'database' | 'document' | 'publication' | 'folder'
  onEdit?: () => void
}

export function ConfiguredSource({ label, fileName, count, icon, onEdit }: ConfiguredSourceProps) {
  const icons = {
    database: Database,
    document: FileText,
    publication: BookOpen,
    folder: Folder,
  }
  const Icon = icons[icon]

  return (
    <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-xl">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-neutral-900 flex items-center justify-center">
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-xs text-neutral-500 uppercase tracking-wider">{label}</p>
          <p className="text-sm font-medium text-neutral-900">
            {fileName}
            {count && count > 1 && <span className="text-neutral-500 font-normal"> +{count - 1} more</span>}
          </p>
        </div>
      </div>
      {onEdit && (
        <button
          onClick={onEdit}
          className="text-xs text-neutral-500 hover:text-neutral-700 transition-colors"
        >
          Change
        </button>
      )}
    </div>
  )
}
