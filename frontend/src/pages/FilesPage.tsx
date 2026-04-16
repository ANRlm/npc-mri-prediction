import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { FileText, Download, Loader2, FileSpreadsheet } from 'lucide-react';
import api, { downloadFile } from '@/api/client';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';

const CSV_TEMPLATE_HEADERS = 'patient_id,sex,age,t_stage,n_stage,dna_after\n';

function downloadCsvTemplate() {
  const blob = new Blob([CSV_TEMPLATE_HEADERS], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'clinical_template.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function FilesPage() {
  const [files, setFiles] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingFile, setDownloadingFile] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await api.get('/get-file-list');
        if (!cancelled) {
          setFiles(res.data.files || []);
        }
      } catch (e: any) {
        if (!cancelled) setError(e?.response?.data?.message || '加载文件列表失败');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleDownload = async (filename: string) => {
    setDownloadingFile(filename);
    try {
      await downloadFile(filename);
    } catch (e: any) {
      setError(`下载 ${filename} 失败`);
    } finally {
      setDownloadingFile(null);
    }
  };

  const getExt = (name: string) => {
    const i = name.lastIndexOf('.');
    return i > -1 ? name.slice(i + 1).toLowerCase() : 'file';
  };

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-semibold tracking-tight">文件库</h1>
        <p className="text-sm text-muted mt-2">查看并下载系统提供的资料与报告文件。</p>
      </motion.div>

      {/* Clinical template download section */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.05 }}
        className="bg-card border border-border rounded-lg p-6 mb-8"
      >
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-md border border-border flex items-center justify-center text-accent shrink-0">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-medium">临床数据模板下载</h3>
              <p className="text-xs text-muted mt-1.5 max-w-md">
                下载临床数据模板，按格式填写后上传至预测页面。模板包含必填列：patient_id, sex, age, t_stage, n_stage, dna_after
              </p>
            </div>
          </div>
          <Button variant="secondary" size="sm" onClick={downloadCsvTemplate}>
            <Download className="w-4 h-4" /> 下载模板
          </Button>
        </div>
      </motion.div>

      {error && (
        <p className="text-xs text-red-500 mb-4">{error}</p>
      )}

      {loading ? (
        <div className="border border-border rounded-lg py-16 flex items-center justify-center text-sm text-muted">
          <Loader2 className="w-4 h-4 animate-spin mr-2" /> 加载中…
        </div>
      ) : files.length === 0 ? (
        <div className="border border-dashed border-border rounded-lg py-16 text-center text-sm text-muted">
          暂无可下载的文件
        </div>
      ) : (
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{
            hidden: {},
            visible: { transition: { staggerChildren: 0.04 } },
          }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {files.map((filename) => (
            <motion.button
              key={filename}
              variants={{
                hidden: { opacity: 0, y: 12 },
                visible: { opacity: 1, y: 0 },
              }}
              whileHover={{ y: -2 }}
              transition={{ duration: 0.25 }}
              onClick={() => handleDownload(filename)}
              disabled={downloadingFile === filename}
              className="text-left bg-card border border-border rounded-lg p-5 hover:border-fg/30 transition-colors group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-10 h-10 rounded-md border border-border flex items-center justify-center text-muted group-hover:text-fg transition-colors">
                  <FileText className="w-4 h-4" />
                </div>
                <Badge variant="info">.{getExt(filename)}</Badge>
              </div>
              <p className="text-sm font-medium truncate" title={filename}>
                {filename}
              </p>
              <div className="flex items-center gap-1.5 text-xs text-muted mt-3">
                {downloadingFile === filename ? (
                  <>
                    <Loader2 className="w-3 h-3 animate-spin" /> 正在下载…
                  </>
                ) : (
                  <>
                    <Download className="w-3 h-3" /> 点击下载
                  </>
                )}
              </div>
            </motion.button>
          ))}
        </motion.div>
      )}
    </main>
  );
}

export default FilesPage;
