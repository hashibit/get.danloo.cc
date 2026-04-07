import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { authService } from "../../../services/auth";
import { useAuth } from "../../../contexts/AuthContext";

export default function WeChatCallback() {
  const router = useRouter();
  const { login } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const handleWeChatCallback = async () => {
      const { code, state } = router.query;

      if (!code) {
        setError("授权失败：缺少授权码");
        setLoading(false);
        return;
      }

      try {
        const response = await authService.loginWithWeChat({
          code: code as string,
          state: state as string
        });

        if (response.success && response.data) {
          login(response.data.user, response.data.access_token);

          // 如果是新用户，可能需要引导完善信息
          if (response.data.is_new_user) {
            router.push("/my-dashboard");
          } else {
            router.push("/my-dashboard");
          }
        } else {
          setError(response.error?.message || "微信登录失败");
        }
      } catch (err) {
        console.error("WeChat callback error:", err);
        setError("微信登录失败，请重试");
      } finally {
        setLoading(false);
      }
    };

    if (router.isReady) {
      handleWeChatCallback();
    }
  }, [router, login]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
      <Head>
        <title>微信登录回调 - 丹炉</title>
      </Head>

      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
        {loading ? (
          <div>
            <div className="mb-4">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">正在处理微信登录...</h2>
            <p className="text-gray-600">请稍候，我们正在验证您的微信身份</p>
          </div>
        ) : error ? (
          <div>
            <div className="mb-4">
              <svg className="mx-auto h-12 w-12 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">登录失败</h2>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={() => router.push("/login")}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              返回登录页
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}