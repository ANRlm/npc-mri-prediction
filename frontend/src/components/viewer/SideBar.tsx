import { useState } from 'react';
import { motion } from 'framer-motion';
import { QuickSettingsIcon, ImagesMeshesIcon, AnnotationsIcon } from '../ui/icons';

type TabType = 'quickSet' | 'imageMeshes' | 'annotations';

interface SideBarProps {
  onTabChange?: (tab: TabType) => void;
}

export const SideBar = ({ onTabChange }: SideBarProps) => {
  const [currentTab, setCurrentTab] = useState<TabType>('imageMeshes');

  const handleTabClick = (tab: TabType) => {
    setCurrentTab(tab);
    onTabChange?.(tab);
  };

  const tabs = [
    { id: 'quickSet' as TabType, icon: QuickSettingsIcon, tooltip: 'Quick Settings' },
    { id: 'imageMeshes' as TabType, icon: ImagesMeshesIcon, tooltip: 'Images & Meshes' },
    { id: 'annotations' as TabType, icon: AnnotationsIcon, tooltip: 'Annotations' },
  ];

  return (
    <div className="absolute top-0 right-0 w-60 h-full flex flex-row overflow-visible text-white">
      {/* Tab buttons */}
      <div className="w-10 h-full flex flex-col bg-black">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isSelected = currentTab === tab.id;

          return (
            <motion.button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              className={`
                w-9 h-8 border-none font-xs cursor-pointer mt-1
                rounded-tl-lg rounded-bl-lg
                border-t border-l border-b border-[rgba(118,118,118,0.3)]
                ${
                  isSelected
                    ? 'bg-[rgb(216,181,237)] text-white scale-100'
                    : 'bg-gray-300 text-black scale-90 translate-x-[0.15rem]'
                }
              `}
              whileHover={{
                backgroundColor: 'rgba(216, 181, 237, 1)',
                scale: isSelected ? 1 : 0.85,
                translateX: isSelected ? 0 : '0.2rem',
              }}
              transition={{ duration: 0.2 }}
              title={tab.tooltip}
            >
              <Icon />
            </motion.button>
          );
        })}
      </div>

      {/* Content panel */}
      <div className="w-[13.5rem] h-full bg-[rgba(16,31,63,0.8)] p-4">
        {currentTab === 'quickSet' && (
          <div className="text-sm">
            <h3 className="text-[#00db95] mb-3 font-semibold">快速设置</h3>
            <div className="space-y-2 text-gray-300">
              <div>切片类型</div>
              <div>布局选项</div>
              <div>渲染比例</div>
              <div>颜色映射</div>
            </div>
          </div>
        )}

        {currentTab === 'imageMeshes' && (
          <div className="text-sm">
            <h3 className="text-[#00db95] mb-3 font-semibold">图像与网格</h3>
            <div className="space-y-2 text-gray-300">
              <div>加载的图像列表</div>
              <div>网格数据</div>
            </div>
          </div>
        )}

        {currentTab === 'annotations' && (
          <div className="text-sm">
            <h3 className="text-[#00db95] mb-3 font-semibold">标注</h3>
            <div className="space-y-2 text-gray-300">
              <div>标注点列表</div>
              <div>测量工具</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
