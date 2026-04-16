import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import { useAuthStore } from '@/store/authStore';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function RegisterForm() {
  const navigate = useNavigate();
  const { register, isLoading, error } = useAuthStore();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const generateCode = () => {
    const randomCode = Math.floor(100000 + Math.random() * 900000).toString();
    setCode(randomCode);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    if (!username.trim() || !email.trim() || !password || !code) {
      setLocalError('请填写所有字段');
      return;
    }
    if (!EMAIL_RE.test(email)) {
      setLocalError('邮箱格式不正确');
      return;
    }
    if (password.length < 6) {
      setLocalError('密码至少需要 6 个字符');
      return;
    }
    const ok = await register(username.trim(), email.trim(), password, code.trim());
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
        placeholder="设置用户名"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <Input
        label="邮箱"
        name="email"
        type="email"
        autoComplete="email"
        placeholder="your@email.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <Input
        label="密码"
        name="password"
        type="password"
        autoComplete="new-password"
        placeholder="至少 6 个字符"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <div className="flex flex-col gap-2">
        <Input
          label="验证码"
          name="code"
          type="text"
          placeholder="点击按钮获取验证码"
          value={code}
          onChange={(e) => setCode(e.target.value)}
        />
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={generateCode}
          disabled={!email.trim() || !EMAIL_RE.test(email)}
        >
          获取验证码
        </Button>
      </div>
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
        创建账户
      </Button>
    </motion.form>
  );
}

export default RegisterForm;
