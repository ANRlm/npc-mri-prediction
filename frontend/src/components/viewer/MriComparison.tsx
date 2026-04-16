import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import api from '../../api/client';
import { Loading } from '../ui/Loading';

interface ImageData {
  filename: string;
  base64: string;
}

export const MriComparison = () => {
  const [images, setImages] = useState<ImageData[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchImages();
  }, []);

  const fetchImages = async () => {
    try {
      const response = await api.get('/images');
      if (response.data && response.data.images) {
        setImages(response.data.images);
      } else {
        // Fallback demo images
        setImages([
          { filename: '示例图像 1', base64: '/r_images/1.png' },
          { filename: '示例图像 2', base64: '/r_images/2.jpg' },
        ]);
      }
    } catch (error) {
      console.error('获取图片失败:', error);
      setImages([
        { filename: '示例图像 1', base64: '/r_images/1.png' },
        { filename: '示例图像 2', base64: '/r_images/2.jpg' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="w-screen h-screen bg-[#0f0f2d] flex items-center justify-center">
        <Loading />
      </div>
    );
  }

  return (
    <div className="w-screen h-screen flex bg-[#0f0f2d]">
      {/* Left side: Contour images */}
      <div className="w-[30%] h-full p-5 overflow-hidden text-white">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-[#00db95]">MRI轮廓图对比</h2>
          <motion.button
            onClick={() => navigate('/')}
            className="px-4 py-2 text-[#00db95] font-semibold text-lg bg-transparent border-none cursor-pointer"
            whileHover={{ color: '#1e90ff', scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            返回首页
          </motion.button>
        </div>

        <div className="h-[calc(100%-60px)] overflow-y-auto p-2 grid grid-cols-2 gap-4">
          {images.map((item, index) => (
            <motion.div
              key={index}
              className="bg-[rgba(16,31,63,0.5)] rounded p-2 text-center h-[200px]"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.05 }}
            >
              <div className="text-[#00db95] mb-2 text-sm">{item.filename}</div>
              <img
                src={item.base64}
                alt={item.filename}
                className="w-full h-full object-contain"
              />
            </motion.div>
          ))}
        </div>
      </div>

      {/* Right side: 3D MRI Viewer */}
      <div className="w-[68%] h-full relative">
        {/* Placeholder for MRI Viewer - will be integrated with actual viewer */}
        <div className="w-full h-full flex items-center justify-center text-white text-xl">
          <div className="text-center">
            <div className="text-[#00db95] mb-4">3D MRI 查看器</div>
            <div className="text-gray-400 text-sm">
              集成 Niivue 或其他 3D 医学影像查看器
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
