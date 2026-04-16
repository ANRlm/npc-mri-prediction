import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Edit3 } from 'lucide-react';
import FileDropZone from '@/components/prediction/FileDropZone';
import ClinicalEditor, { DEFAULT_CLINICAL, type ClinicalData } from '@/components/prediction/ClinicalEditor';
import ResultsPanel from '@/components/prediction/ResultsPanel';
import Button from '@/components/ui/Button';
import { usePredictionStore } from '@/store/predictionStore';

type ImageType = 'T1' | 'T2' | 'T1C';
type ClinicalMode = 'edit' | 'upload';

const IMAGE_TYPE_OPTIONS: { value: ImageType; label: string; tip: string }[] = [
  { value: 'T1', label: 'T1', tip: '治疗前基线序列' },
  { value: 'T2', label: 'T2', tip: '治疗后序列' },
  { value: 'T1C', label: 'T1C', tip: '增强序列' },
];

function clinicalDataToFile(data: ClinicalData): File {
  const csv = `patient_id,sex,age,t_stage,n_stage,total_stage,dna_before,dna_after\n${data.patient_id},${data.sex},${data.age},${data.t_stage},${data.n_stage},${data.total_stage},${data.dna_before},${data.dna_after}\n`;
  return new File([csv], 'clinical_inline.csv', { type: 'text/csv' });
}

export function PredictionPage() {
  const { uploadAndPredict, isLoading, error } = usePredictionStore();

  const [imageType, setImageType] = useState<ImageType>('T1');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [maskFile, setMaskFile] = useState<File | null>(null);
  const [clinicalFile, setClinicalFile] = useState<File | null>(null);
  const [clinicalMode, setClinicalMode] = useState<ClinicalMode>('edit');
  const [clinicalData, setClinicalData] = useState<ClinicalData>(DEFAULT_CLINICAL);
  const [tooltip, setTooltip] = useState<ImageType | null>(null);

  const clinicalReady = clinicalMode === 'edit' || clinicalFile !== null;
  const canSubmit = imageFile && maskFile && clinicalReady && !isLoading;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!imageFile || !maskFile) return;
    const fd = new FormData();
    fd.append('image_file', imageFile);
    fd.append('mask_file', maskFile);
    fd.append('clinical_file', clinicalMode === 'edit' ? clinicalDataToFile(clinicalData) : clinicalFile!);
    fd.append('image_type', imageType);
    await uploadAndPredict(fd);
  };

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mb-10"
      >
        <h1 className="text-3xl font-semibold tracking-tight">生存预测</h1>
        <p className="text-sm text-muted mt-2">
          上传影像、掩膜及临床数据，生成个体化生存预测与临床建议。
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-8 items-start">
        <motion.section
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.05 }}
          className="bg-card border border-border rounded-xl p-6 lg:sticky lg:top-20"
        >
          <form onSubmit={handleSubmit} className="flex flex-col gap-6">

            {/* Image type */}
            <div className="flex flex-col gap-2">
              <span className="text-xs font-medium text-fg/80">影像序列类型</span>
              <div className="flex gap-2">
                {IMAGE_TYPE_OPTIONS.map((opt) => (
                  <div key={opt.value} className="relative">
                    <button
                      type="button"
                      onClick={() => setImageType(opt.value)}
                      onMouseEnter={() => setTooltip(opt.value)}
                      onMouseLeave={() => setTooltip(null)}
                      className={`px-4 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                        imageType === opt.value
                          ? 'bg-accent text-white border-accent'
                          : 'bg-card text-fg/70 border-border hover:border-accent/50'
                      }`}
                    >
                      {opt.label}
                    </button>
                    <AnimatePresence>
                      {tooltip === opt.value && (
                        <motion.div
                          initial={{ opacity: 0, y: 4 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: 4 }}
                          className="absolute top-full mt-1.5 left-1/2 -translate-x-1/2 z-10 whitespace-nowrap bg-fg text-bg text-xs rounded-md px-2.5 py-1.5 pointer-events-none"
                        >
                          {opt.tip}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                ))}
              </div>
            </div>

            {/* MRI image */}
            <FileDropZone
              label="MRI影像文件 (T1/T2/T1C)"
              accept=".nii,.nii.gz,application/gzip,application/x-gzip,application/octet-stream"
              file={imageFile}
              onChange={setImageFile}
              onClear={() => setImageFile(null)}
              description=".nii 或 .nii.gz 格式"
            />

            {/* Mask */}
            <FileDropZone
              label="分割掩膜文件 (mask_all)"
              accept=".nii,.nii.gz,application/gzip,application/x-gzip,application/octet-stream"
              file={maskFile}
              onChange={setMaskFile}
              onClear={() => setMaskFile(null)}
              description=".nii 或 .nii.gz 格式"
            />

            {/* Clinical data */}
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-fg/80">临床数据</span>
                <div className="flex rounded-lg border border-border overflow-hidden text-xs">
                  <button
                    type="button"
                    onClick={() => setClinicalMode('edit')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 transition-colors ${
                      clinicalMode === 'edit'
                        ? 'bg-accent text-white'
                        : 'bg-card text-fg/60 hover:text-fg'
                    }`}
                  >
                    <Edit3 className="w-3 h-3" />
                    在线编辑
                  </button>
                  <button
                    type="button"
                    onClick={() => setClinicalMode('upload')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 transition-colors ${
                      clinicalMode === 'upload'
                        ? 'bg-accent text-white'
                        : 'bg-card text-fg/60 hover:text-fg'
                    }`}
                  >
                    <Upload className="w-3 h-3" />
                    上传文件
                  </button>
                </div>
              </div>

              <AnimatePresence mode="wait">
                {clinicalMode === 'edit' ? (
                  <motion.div
                    key="editor"
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ClinicalEditor value={clinicalData} onChange={setClinicalData} />
                  </motion.div>
                ) : (
                  <motion.div
                    key="uploader"
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    transition={{ duration: 0.2 }}
                  >
                    <FileDropZone
                      label="临床数据文件"
                      accept=".csv,.xlsx,.xls"
                      file={clinicalFile}
                      onChange={setClinicalFile}
                      onClear={() => setClinicalFile(null)}
                      description=".csv / .xlsx / .xls 格式"
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="text-xs text-red-500"
                >
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            <Button
              type="submit"
              variant="primary"
              size="md"
              fullWidth
              loading={isLoading}
              disabled={!canSubmit}
            >
              开始预测
            </Button>
          </form>
        </motion.section>

        {/* Results */}
        <motion.section
          initial={{ opacity: 0, x: 8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          <ResultsPanel />
        </motion.section>
      </div>
    </main>
  );
}

export default PredictionPage;
