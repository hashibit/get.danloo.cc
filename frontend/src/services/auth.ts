import { apiRequest, setAuthToken, removeAuthToken } from './api';

export interface User {
  id: string;
  email?: string;
  username: string;
  alchemyLevel: string;
  email_verified?: boolean;
  social_accounts?: {
    provider: 'wechat' | 'google' | 'github';
    account_id: string;
    nickname?: string;
    avatar?: string;
    linked_at: string;
  }[];
  phone_number?: string;
  phone_verified: boolean;
  wechat_nickname?: string;
  wechat_avatar?: string;
  createdAt: string;
  updatedAt?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface PhoneLoginRequest {
  phone_number: string;
  verification_code: string;
}

export interface PhoneRegisterRequest {
  phone_number: string;
  username: string;
  verification_code: string;
  password?: string;
}

export interface WeChatLoginRequest {
  code: string;
  state?: string;
}

export interface SendVerificationCodeRequest {
  phone_number: string;
  type?: 'phone_verification' | 'login' | 'register' | 'email_verification';
}

export interface VerifyCodeRequest {
  phone_number: string;
  code: string;
  type?: 'phone_verification' | 'login' | 'register';
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface WeChatAuthResponse {
  access_token: string;
  token_type: string;
  user: User;
  is_new_user: boolean;
}

export const authService = {
  // User registration
  register: async (data: RegisterRequest) => {
    const response = await apiRequest<AuthResponse>('/users/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }, false);

    if (response.success && response.data) {
      setAuthToken(response.data.token);
    }

    return response;
  },

  // User login
  login: async (data: LoginRequest) => {
    const response = await apiRequest<LoginResponse>('/users/login', {
      method: 'POST',
      body: JSON.stringify(data),
    }, false);

    if (response.success && response.data) {
      setAuthToken(response.data.access_token);
    }

    return response;
  },

  // Phone registration
  registerWithPhone: async (data: PhoneRegisterRequest) => {
    const response = await apiRequest<User>('/users/register-phone', {
      method: 'POST',
      body: JSON.stringify(data),
    }, false);

    return response;
  },

  // Phone login
  loginWithPhone: async (data: PhoneLoginRequest) => {
    const response = await apiRequest<LoginResponse>('/users/login-phone', {
      method: 'POST',
      body: JSON.stringify(data),
    }, false);

    if (response.success && response.data) {
      setAuthToken(response.data.access_token);
    }

    return response;
  },

  // WeChat login
  loginWithWeChat: async (data: WeChatLoginRequest) => {
    const response = await apiRequest<WeChatAuthResponse>('/users/login-wechat', {
      method: 'POST',
      body: JSON.stringify(data),
    }, false);

    if (response.success && response.data) {
      setAuthToken(response.data.access_token);
    }

    return response;
  },

  // Send verification code
  sendVerificationCode: async (data: SendVerificationCodeRequest) => {
    const response = await apiRequest<{ verification_id: string }>('/users/send-verification-code', {
      method: 'POST',
      body: JSON.stringify(data),
    }, false);

    return response;
  },

  // Verify code
  verifyCode: async (data: VerifyCodeRequest) => {
    const response = await apiRequest<{ message: string }>('/users/verify-code', {
      method: 'POST',
      body: JSON.stringify(data),
    }, false);

    return response;
  },

  // Get WeChat authorization URL
  getWeChatAuthUrl: async (redirectUri: string, state?: string) => {
    const params = new URLSearchParams({
      redirect_uri: redirectUri,
      ...(state && { state })
    });

    const response = await apiRequest<{ auth_url: string }>(`/users/wechat-auth-url?${params}`, {
      method: 'GET',
    }, false);

    return response;
  },

  // Link phone to user
  linkPhoneToUser: async (phoneNumber: string, verificationCode: string) => {
    const response = await apiRequest<{ message: string }>('/users/me/link-phone', {
      method: 'POST',
      body: JSON.stringify({
        phone_number: phoneNumber,
        verification_code: verificationCode
      }),
    });

    return response;
  },

  // Get current user profile
  getProfile: async () => {
    return apiRequest<User>('/users/profile', {
      method: 'GET',
    });
  },

  // Request password reset
  requestPasswordReset: async (email: string) => {
    const response = await apiRequest<{ message: string }>('/users/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }, false);

    return response;
  },

  // Reset password
  resetPassword: async (token: string, newPassword: string) => {
    const response = await apiRequest<{ message: string }>('/users/reset-password', {
      method: 'POST',
      body: JSON.stringify({
        token: token,
        new_password: newPassword
      }),
    }, false);

    return response;
  },

  // Send email verification
  sendEmailVerification: async () => {
    const response = await apiRequest<{ message: string }>('/users/me/send-email-verification', {
      method: 'POST',
    });

    return response;
  },

  // Verify email
  verifyEmail: async (token: string) => {
    const response = await apiRequest<{ message: string }>('/users/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token }),
    }, false);

    return response;
  },

  // Logout
  logout: () => {
    removeAuthToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }
};
