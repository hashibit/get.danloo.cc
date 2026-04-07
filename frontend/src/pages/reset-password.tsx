import React, { useState, useEffect } from "react";
import Head from "next/head";
import { useRouter } from "next/router";
import { useTranslation } from "next-i18next";
import { GetStaticProps } from "next";
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import { authService } from "../services/auth";
import Layout from "../components/Layout";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { Input } from "../components/Input";

interface ResetPasswordRequest {
  token: string;
  new_password: string;
  confirm_password: string;
}

export default function ResetPassword() {
  const { t } = useTranslation("common");
  const router = useRouter();
  const { token } = router.query;

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [tokenValid, setTokenValid] = useState(true);

  // Check token validity on component mount
  useEffect(() => {
    if (token) {
      checkTokenValidity(token as string);
    }
  }, [token]);

  const checkTokenValidity = async (resetToken: string) => {
    try {
      setTokenValid(true);
    } catch (err) {
      setTokenValid(false);
      setError("密码重置链接无效或已过期");
    }
  };

  const validatePassword = (password: string) => {
    const errors = [];

    if (password.length < 8) {
      errors.push("密码长度至少8个字符");
    }

    if (password.length > 128) {
      errors.push("密码长度不能超过128个字符");
    }

    if (!/[A-Z]/.test(password)) {
      errors.push("密码必须包含至少一个大写字母");
    }

    if (!/[a-z]/.test(password)) {
      errors.push("密码必须包含至少一个小写字母");
    }

    if (!/[0-9]/.test(password)) {
      errors.push("密码必须包含至少一个数字");
    }

    if (!/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)) {
      errors.push("密码必须包含至少一个特殊字符");
    }

    return errors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!token) {
      setError("密码重置链接无效");
      return;
    }

    // Check if passwords match
    if (newPassword !== confirmPassword) {
      setError("新密码和确认密码不匹配");
      return;
    }

    // Validate password strength
    const passwordErrors = validatePassword(newPassword);
    if (passwordErrors.length > 0) {
      setError(passwordErrors.join("; "));
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await authService.resetPassword(token as string, newPassword);

      if (response.success) {
        setSuccess(true);
      } else {
        setError(response.error?.message || "密码重置失败");
      }
    } catch (err) {
      setError("密码重置失败，请重试");
    } finally {
      setLoading(false);
    }
  };

  if (!tokenValid) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="max-w-md w-full">
          <Card padding="lg">
            <div className="text-center">
              <div className="mx-auto h-20 w-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-button flex items-center justify-center shadow-card mb-4">
                <span className="text-3xl font-semibold text-white">丹</span>
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">密码重置链接无效</h2>
              <p className="text-gray-600 mb-6">该链接可能已过期或已被使用。</p>
              <Button onClick={() => router.push("/login")} variant="primary" fullWidth>
                返回登录页面
              </Button>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="max-w-md w-full">
          <Card padding="lg">
            <div className="text-center">
              <div className="mx-auto h-20 w-20 bg-gradient-to-r from-green-500 to-teal-600 rounded-button flex items-center justify-center shadow-card mb-4">
                <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">密码重置成功</h2>
              <p className="text-gray-600 mb-6">您的密码已成功更新。</p>
              <Button onClick={() => router.push("/login")} variant="primary" fullWidth>
                返回登录页面
              </Button>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <Head>
        <title>
          {t("auth.resetPassword")} - {t("brand.name")}
        </title>
        <meta
          name="description"
          content={`${t("auth.resetPassword")} on ${t("brand.name")} platform`}
        />
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
      </Head>

      <div className="min-h-screen flex items-center justify-center px-4 py-12">
        <div className="max-w-md w-full">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="mx-auto h-20 w-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-button flex items-center justify-center shadow-card mb-4">
              <span className="text-3xl font-semibold text-white">丹</span>
            </div>
            <h2 className="text-3xl font-semibold text-gray-900">重置密码</h2>
            <p className="mt-2 text-sm text-gray-600">请设置您的新密码</p>
          </div>

          <Card padding="lg">
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-100 rounded-input text-sm text-danger">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <Input
                id="new-password"
                type="password"
                label="新密码"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="请输入新密码"
                required
                fullWidth
                helperText="密码必须包含至少8个字符，包括大写字母、小写字母、数字和特殊字符"
              />

              <Input
                id="confirm-password"
                type="password"
                label="确认新密码"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="请再次输入新密码"
                required
                fullWidth
              />

              <Button
                type="submit"
                loading={loading}
                variant="primary"
                size="lg"
                fullWidth
              >
                重置密码
              </Button>
            </form>
          </Card>

          <p className="text-center text-xs text-gray-400 mt-8">
            © 2025 丹炉. 保留所有权利.
          </p>
        </div>
      </div>
    </div>
  );
}

export const getStaticProps: GetStaticProps = async ({ locale = 'en' }) => {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common"])),
    },
  };
};