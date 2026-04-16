import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Loader2, ImageOff } from 'lucide-react';
import api from '@/api/client';

interface MriImage {
  filename: string;
  slice_number?: number;
  base64?: string;
  error?: string;
}

export function MriViewerPage() {
  const [images, setImages] = useState<MriImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<MriImage | null>(null);

  useEffect(() => {
    api.get('/images')
      .then((res) => {
        if (res.data.success) {
          setImages(res.data.images || []);
        } else {
          setError(res.data.message || '获取图像失败');
        }
      })
      .catch((e: any) => {
        setError(e?.response?.data?.message || '获取图像失败');
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-semibold tracking-tight">MRI 影像查看</h1>
        <p className="text-sm text-muted mt-2">查看 MRI 轮廓图像。</p>
      </motion.div>

      {loading && (
        <div className="flex items-center justify-center py-20 text-sm text-muted">
          <Loader2 className="w-4 h-4 animate-spin mr-2" /> 加载中…
        </div>
      )}

      {error && (
        <div className="flex flex-col items-center justify-center py-20 text-sm text-muted gap-2">
          <ImageOff className="w-8 h-8" />
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && images.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-sm text-muted gap-2">
          <ImageOff className="w-8 h-8" />
          <p>暂无可用图像</p>
        </div>
      )}

      {!loading && images.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {images.map((img) => (
            <motion.button
              key={img.filename}
              type="button"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              onClick={() => setSelected(img)}
              className="group relative aspect-square rounded-lg overflow-hidden border border-border hover:border-accent transition-colors bg-card"
            >
              <img
                src={img.base64}
                alt={img.filename}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/60 to-transparent px-2 py-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                <p className="text-white text-xs truncate">{img.filename}</p>
              </div>
            </motion.button>
          ))}
        </div>
      )}

      {selected && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          onClick={() => setSelected(null)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-3xl w-full bg-card rounded-xl overflow-hidden shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <p className="text-sm font-medium truncate">{selected.filename}</p>
              <button
                type="button"
                onClick={() => setSelected(null)}
                className="text-muted hover:text-fg transition-colors text-lg leading-none"
              >
                ✕
              </button>
            </div>
            <img
              src={selected.base64}
              alt={selected.filename}
              className="w-full object-contain max-h-[70vh]"
            />
          </motion.div>
        </div>
      )}
    </main>
  );
}

export default MriViewerPage;
