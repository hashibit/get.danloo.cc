import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { authService } from '../services/auth';
import Layout from '../components/Layout';
import { Card } from '../components/Card';
import { Button } from '../components/Button';

const VerifyEmailPage = () => {
  const router = useRouter();
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyEmail = async () => {
      const { token } = router.query;

      if (!token || typeof token !== 'string') {
        setStatus('error');
        setMessage('无效的验证链接');
        return;
      }

      try {
        const response = await authService.verifyEmail(token);

        if (response.success) {
          setStatus('success');
          setMessage('邮箱验证成功！');

          // Redirect to profile page after 3 seconds
          setTimeout(() => {
            router.push('/profile');
          }, 3000);
        } else {
          setStatus('error');
          setMessage(response.error?.message || '邮箱验证失败，请重试');
        }
      } catch (error) {
        console.error('Email verification error:', error);
        setStatus('error');
        setMessage('邮箱验证失败，请重试');
      }
    };

    if (router.isReady) {
      verifyEmail();
    }
  }, [router.isReady, router.query]);

  return (
    <Layout title="邮箱验证 - 丹炉 (Danloo)">
      <div className="flex items-center justify-center py-12">
        <div className="max-w-md w-full">
          <Card padding="lg">
            <div className="text-center">
              <h2 className="text-3xl font-semibold text-gray-900 mb-8">
                邮箱验证
              </h2>

              {status === 'verifying' && (
                <div>
                  <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-500 border-t-transparent mx-auto mb-4"></div>
                  <p className="text-gray-700">正在验证您的邮箱...</p>
                </div>
              )}

              {status === 'success' && (
                <div>
                  <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-50 mb-4">
                    <svg className="h-6 w-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">{message}</h3>
                  <p className="text-sm text-gray-500 mb-4">页面将在 3 秒后自动跳转到个人资料页面...</p>
                  <Button onClick={() => router.push('/profile')}>
                    立即前往个人资料
                  </Button>
                </div>
              )}

              {status === 'error' && (
                <div>
                  <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-50 mb-4">
                    <svg className="h-6 w-6 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">验证失败</h3>
                  <p className="text-sm text-gray-500 mb-4">{message}</p>
                  <div className="flex gap-3 justify-center">
                    <Button onClick={() => router.push('/profile')} variant="tertiary">
                      返回个人资料
                    </Button>
                    <Button onClick={() => router.push('/login')} variant="primary">
                      前往登录
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </Layout>
  );
};

export default VerifyEmailPage;