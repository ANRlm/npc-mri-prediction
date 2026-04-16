import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import { useAuthStore } from '@/store/authStore';

export function LoginForm() {
  const navigate = useNavigate();
  const { login, isLoading, error } = useAuthStore();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    if (!username.trim() || !password) {
      setLocalError('请输入用户名和密码');
      return;
    }
    const ok = await login(username.trim(), password);
    if (ok) navigate('/predict');
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col gap-4"
    >
      <Input
        label="用户名"
        name="username"
        type="text"
        autoComplete="username"
        placeholder="输入您的用户名"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <Input
        label="密码"
        name="password"
        type="password"
        autoComplete="current-password"
        placeholder="输入您的密码"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      {(localError || error) && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-xs text-red-500"
        >
          {localError || error}
        </motion.p>
      )}
      <Button type="submit" loading={isLoading} fullWidth>
        登录
      </Button>
    </motion.form>
  );
}

export default LoginForm;
