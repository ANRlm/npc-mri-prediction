import { motion } from 'framer-motion';

interface LoadingProps {
  marginTop?: string;
}

export const Loading = ({ marginTop = '50%' }: LoadingProps) => {
  const dotPositions = [
    { left: '0', top: '50%', marginTop: '-10px' },
    { left: '14px', top: '14px' },
    { left: '50%', top: '0', marginLeft: '-10px' },
    { top: '14px', right: '14px' },
    { right: '0', top: '50%', marginTop: '-10px' },
    { right: '14px', bottom: '14px' },
    { bottom: '0', left: '50%', marginLeft: '-10px' },
    { bottom: '14px', left: '14px' },
  ];

  return (
    <div
      className="relative w-[100px] h-[100px] mx-auto -top-[50px] scale-50"
      style={{ marginTop }}
    >
      {dotPositions.map((position, index) => (
        <motion.span
          key={index}
          className="absolute w-5 h-5 rounded-full bg-[#67e7d5]"
          style={position}
          animate={{
            scale: [1.2, 0.3],
            opacity: [1, 0.5],
          }}
          transition={{
            duration: 1.04,
            repeat: Infinity,
            ease: 'easeInOut',
            delay: index * 0.13,
          }}
        />
      ))}
    </div>
  );
};
