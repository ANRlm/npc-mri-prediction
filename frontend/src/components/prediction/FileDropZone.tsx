import { useRef, useState, DragEvent, ChangeEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, File, X } from 'lucide-react';

interface FileDropZoneProps {
  label: string;
  accept: string;
  file: File | null;
  onChange: (file: File) => void;
  onClear?: () => void;
  description?: string;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileDropZone({
  label,
  accept,
  file,
  onChange,
  onClear,
  description,
}: FileDropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) onChange(dropped);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) onChange(selected);
    // reset so same file can be re-selected
    e.target.value = '';
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onClear?.();
  };

  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-medium text-fg/80">{label}</label>

      <motion.div
        animate={{
          borderColor: file
            ? 'rgb(var(--color-accent))'
            : isDragging
            ? 'rgb(var(--color-accent))'
            : 'rgb(var(--color-border))',
          backgroundColor: isDragging
            ? 'rgba(var(--color-accent), 0.04)'
            : 'transparent',
        }}
        transition={{ duration: 0.15 }}
        onClick={() => !file && inputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className="relative border border-dashed rounded-lg px-4 py-4 cursor-pointer select-none"
        style={{ borderStyle: 'dashed' }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          className="hidden"
          onChange={handleChange}
        />

        <AnimatePresence mode="wait">
          {file ? (
            <motion.div
              key="filled"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-3"
            >
              <div className="w-8 h-8 rounded-md border border-border flex items-center justify-center text-accent shrink-0">
                <File className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate text-fg">{file.name}</p>
                <p className="text-xs text-muted">{formatBytes(file.size)}</p>
              </div>
              <button
                type="button"
                onClick={handleClear}
                className="w-6 h-6 rounded-full flex items-center justify-center text-muted hover:text-fg hover:bg-border/40 transition-colors shrink-0"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col items-center justify-center gap-2 py-2 text-center"
            >
              <div className="w-8 h-8 rounded-full border border-border flex items-center justify-center text-muted">
                <Upload className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs text-fg/70">
                  拖拽文件至此，或{' '}
                  <span className="text-accent underline underline-offset-2">点击选择</span>
                </p>
                {description && (
                  <p className="text-xs text-muted mt-0.5">{description}</p>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}

export default FileDropZone;
