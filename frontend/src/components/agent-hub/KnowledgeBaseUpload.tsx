/**
 * Knowledge Base Upload Component
 * 
 * Displays file upload UI and file list for agent knowledge base.
 */
import React, { useState, useRef } from 'react';
import { Upload, File, Trash2, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { uploadFile, listFiles, deleteFile, type KnowledgeFile } from '../../services/knowledgeBase';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';

interface KnowledgeBaseUploadProps {
  agentId: string;
}

const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.md', '.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.yaml', '.yml'];

const KnowledgeBaseUpload: React.FC<KnowledgeBaseUploadProps> = ({ agentId }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{ fileId: string; filename: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  
  // Fetch files
  const { data: files = [], isLoading } = useQuery<KnowledgeFile[]>({
    queryKey: ['knowledge-files', agentId],
    queryFn: () => listFiles(agentId),
  });
  
  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadFile(agentId, file),
    onSuccess: (data) => {
      if (data.success) {
        setUploadStatus({
          type: 'success',
          message: `✅ ${data.filename} uploaded successfully! (${data.chunks_added} chunks processed)`
        });
        queryClient.invalidateQueries({ queryKey: ['knowledge-files', agentId] });
      } else {
        setUploadStatus({
          type: 'error',
          message: `❌ Error: ${data.error}`
        });
      }
      
      // Clear status after 5 seconds
      setTimeout(() => setUploadStatus(null), 5000);
    },
    onError: (error: any) => {
      setUploadStatus({
        type: 'error',
        message: `❌ Upload failed: ${error.response?.data?.detail || error.message}`
      });
      setTimeout(() => setUploadStatus(null), 5000);
    },
  });
  
  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (fileId: string) => deleteFile(agentId, fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-files', agentId] });
      setDeleteConfirm(null);
    },
  });

  const handleDeleteClick = (fileId: string, filename: string) => {
    setDeleteConfirm({ fileId, filename });
  };

  const handleDeleteConfirm = () => {
    if (deleteConfirm) {
      deleteMutation.mutate(deleteConfirm.fileId);
    }
  };
  
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };
  
  const handleFiles = (files: FileList) => {
    const file = files[0];
    
    // Validate file extension
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setUploadStatus({
        type: 'error',
        message: `❌ File type ${ext} not supported. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`
      });
      return;
    }
    
    // Upload
    uploadMutation.mutate(file);
  };
  
  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">📚 Knowledge Base</h3>
        <span className="text-xs text-gray-500">{files.length} file{files.length !== 1 ? 's' : ''}</span>
      </div>
      
      {/* Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${uploadMutation.isPending ? 'opacity-50 pointer-events-none' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleButtonClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleChange}
          accept={ALLOWED_EXTENSIONS.join(',')}
        />
        
        {uploadMutation.isPending ? (
          <div className="flex flex-col items-center">
            <Loader className="w-10 h-10 text-blue-500 animate-spin mb-2" />
            <p className="text-sm text-gray-600">Uploading...</p>
          </div>
        ) : (
          <>
            <Upload className="w-10 h-10 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">
              <span className="font-semibold text-blue-600">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-gray-500">
              PDF, TXT, MD, Code files (max 10MB)
            </p>
          </>
        )}
      </div>
      
      {/* Status Message */}
      {uploadStatus && (
        <div className={`flex items-start gap-2 p-3 rounded-lg ${
          uploadStatus.type === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        }`}>
          {uploadStatus.type === 'success' ? (
            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          )}
          <p className={`text-sm ${uploadStatus.type === 'success' ? 'text-green-700' : 'text-red-700'}`}>
            {uploadStatus.message}
          </p>
        </div>
      )}
      
      {/* File List */}
      {isLoading ? (
        <div className="text-center py-4">
          <Loader className="w-6 h-6 text-gray-400 animate-spin mx-auto" />
        </div>
      ) : files.length > 0 ? (
        <div className="space-y-2">
          {files.map((file) => (
            <div
              key={file.file_id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <File className="w-5 h-5 text-blue-600 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.filename}
                  </p>
                  <p className="text-xs text-gray-500">{file.file_type}</p>
                </div>
              </div>
              
              <button
                onClick={() => handleDeleteClick(file.file_id, file.filename)}
                disabled={deleteMutation.isPending}
                className="flex-shrink-0 p-2 text-red-600 hover:bg-red-50 rounded-lg transition disabled:opacity-50"
                title="Delete file"
              >
                {deleteMutation.isPending ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-6 text-sm text-gray-500">
          No files uploaded yet
        </div>
      )}
      
      {/* Info */}
      <div className="text-xs text-gray-500 bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="font-semibold text-blue-900 mb-1">💡 How it works:</p>
        <ul className="list-disc list-inside space-y-1 text-blue-800">
          <li>Upload documents to give your agent custom knowledge</li>
          <li>Files are processed and indexed for semantic search</li>
          <li>Agent can search and reference uploaded content</li>
          <li>Enable "Knowledge Base" tool when creating conversations</li>
        </ul>
      </div>

      {/* Delete Confirmation Dialog */}
      {deleteConfirm && (
        <ConfirmDialog
          isOpen={true}
          onClose={() => setDeleteConfirm(null)}
          onConfirm={handleDeleteConfirm}
          title="Delete File"
          message={`Are you sure you want to delete "${deleteConfirm.filename}"?\n\nThis will remove all associated knowledge base chunks. This action cannot be undone.`}
          confirmText="Delete"
          confirmVariant="danger"
          isLoading={deleteMutation.isPending}
        />
      )}
    </div>
  );
};

export default KnowledgeBaseUpload;
