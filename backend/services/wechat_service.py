import hashlib
import json
import time
from typing import Dict, Any, Optional
from urllib.parse import urlencode, parse_qs
import httpx

from common.logging_config import get_logger

logger = get_logger(__name__)


class WeChatService:
    def __init__(self):
        self.app_id = None
        self.app_secret = None
        self.redirect_uri = None
        self._load_config()

    def _load_config(self):
        """加载微信配置"""
        import os
        self.app_id = os.getenv('WECHAT_APP_ID')
        self.app_secret = os.getenv('WECHAT_APP_SECRET')
        self.redirect_uri = os.getenv('WECHAT_REDIRECT_URI', 'http://localhost:3000/auth/wechat/callback')

        if not self.app_id or not self.app_secret:
            logger.warning("微信配置未设置，微信登录功能将不可用")

    def generate_auth_url(self, state: Optional[str] = None, scope: str = 'snsapi_login') -> str:
        """
        生成微信授权URL

        Args:
            state: 防CSRF攻击的随机字符串
            scope: 授权作用域，snsapi_login 或 snsapi_userinfo

        Returns:
            str: 微信授权URL
        """
        if not self.app_id:
            raise ValueError("微信APP_ID未配置")

        # 生成随机state（如果未提供）
        if not state:
            import random
            import string
            state = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

        params = {
            'appid': self.app_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': scope,
            'state': state
        }

        auth_url = 'https://open.weixin.qq.com/connect/qrconnect?' + urlencode(params)
        return auth_url

    async def get_access_token(self, code: str) -> Dict[str, Any]:
        """
        通过授权码获取access_token

        Args:
            code: 授权码

        Returns:
            Dict: access_token信息
        """
        if not self.app_id or not self.app_secret:
            raise ValueError("微信配置未设置")

        params = {
            'appid': self.app_id,
            'secret': self.app_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get('https://api.weixin.qq.com/sns/oauth2/access_token', params=params)
                response.raise_for_status()
                data = response.json()

                if 'errcode' in data:
                    logger.error(f"微信获取access_token失败: {data}")
                    raise ValueError(f"微信API错误: {data.get('errmsg', '未知错误')}")

                return data

        except httpx.HTTPError as e:
            logger.error(f"微信API请求失败: {str(e)}")
            raise ValueError(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"微信API响应解析失败: {str(e)}")
            raise ValueError(f"响应解析失败: {str(e)}")

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新access_token

        Args:
            refresh_token: 刷新令牌

        Returns:
            Dict: 新的access_token信息
        """
        if not self.app_id or not self.app_secret:
            raise ValueError("微信配置未设置")

        params = {
            'appid': self.app_id,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get('https://api.weixin.qq.com/sns/oauth2/refresh_token', params=params)
                response.raise_for_status()
                data = response.json()

                if 'errcode' in data:
                    logger.error(f"微信刷新access_token失败: {data}")
                    raise ValueError(f"微信API错误: {data.get('errmsg', '未知错误')}")

                return data

        except httpx.HTTPError as e:
            logger.error(f"微信API请求失败: {str(e)}")
            raise ValueError(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"微信API响应解析失败: {str(e)}")
            raise ValueError(f"响应解析失败: {str(e)}")

    async def get_user_info(self, access_token: str, openid: str) -> Dict[str, Any]:
        """
        获取用户信息

        Args:
            access_token: 访问令牌
            openid: 用户标识

        Returns:
            Dict: 用户信息
        """
        params = {
            'access_token': access_token,
            'openid': openid
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get('https://api.weixin.qq.com/sns/userinfo', params=params)
                response.raise_for_status()
                data = response.json()

                if 'errcode' in data:
                    logger.error(f"微信获取用户信息失败: {data}")
                    raise ValueError(f"微信API错误: {data.get('errmsg', '未知错误')}")

                return data

        except httpx.HTTPError as e:
            logger.error(f"微信API请求失败: {str(e)}")
            raise ValueError(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"微信API响应解析失败: {str(e)}")
            raise ValueError(f"响应解析失败: {str(e)}")

    async def validate_access_token(self, access_token: str, openid: str) -> bool:
        """
        验证access_token是否有效

        Args:
            access_token: 访问令牌
            openid: 用户标识

        Returns:
            bool: 是否有效
        """
        params = {
            'access_token': access_token,
            'openid': openid
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get('https://api.weixin.qq.com/sns/auth', params=params)
                response.raise_for_status()
                data = response.json()

                return data.get('errcode') == 0

        except Exception as e:
            logger.error(f"验证access_token失败: {str(e)}")
            return False

    def decrypt_user_info(self, encrypted_data: str, iv: str, session_key: str) -> Dict[str, Any]:
        """
        解密微信用户信息（小程序）

        Args:
            encrypted_data: 加密数据
            iv: 初始向量
            session_key: 会话密钥

        Returns:
            Dict: 解密后的用户信息
        """
        try:
            import base64
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import unpad

            # Base64解码
            encrypted_data = base64.b64decode(encrypted_data)
            iv = base64.b64decode(iv)
            session_key = base64.b64decode(session_key)

            # AES解密
            cipher = AES.new(session_key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)

            # 解析JSON
            user_info = json.loads(decrypted.decode('utf-8'))
            return user_info

        except Exception as e:
            logger.error(f"解密用户信息失败: {str(e)}")
            raise ValueError(f"解密失败: {str(e)}")

    async def handle_wechat_login(self, code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """
        处理微信登录流程

        Args:
            code: 授权码
            state: 状态字符串

        Returns:
            Dict: 登录结果
        """
        try:
            # 1. 获取access_token
            token_data = await self.get_access_token(code)
            access_token = token_data['access_token']
            openid = token_data['openid']
            refresh_token = token_data.get('refresh_token')
            unionid = token_data.get('unionid')

            # 2. 获取用户信息
            user_info = await self.get_user_info(access_token, openid)

            # 3. 验证access_token
            is_valid = await self.validate_access_token(access_token, openid)
            if not is_valid:
                raise ValueError("access_token无效")

            logger.info(f"微信登录成功: openid={openid}, nickname={user_info.get('nickname')}")

            return {
                'success': True,
                'data': {
                    'openid': openid,
                    'unionid': unionid,
                    'nickname': user_info.get('nickname'),
                    'headimgurl': user_info.get('headimgurl'),
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user_info': user_info
                }
            }

        except Exception as e:
            logger.error(f"微信登录失败: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }

    def generate_jsapi_signature(self, url: str) -> Dict[str, str]:
        """
        生成JS-SDK签名（用于网页分享等功能）

        Args:
            url: 当前页面URL

        Returns:
            Dict: 签名信息
        """
        try:
            import time
            import random
            import string

            # 1. 获取access_token
            # 这里需要先实现获取jsapi_ticket的逻辑
            jsapi_ticket = self._get_jsapi_ticket()

            # 2. 生成签名参数
            timestamp = int(time.time())
            noncestr = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

            # 3. 按字典序排序参数
            params = {
                'jsapi_ticket': jsapi_ticket,
                'noncestr': noncestr,
                'timestamp': timestamp,
                'url': url
            }

            # 4. 生成签名
            string = '&'.join([f'{k}={v}' for k, v in sorted(params.items())])
            signature = hashlib.sha1(string.encode('utf-8')).hexdigest()

            return {
                'appId': self.app_id,
                'timestamp': timestamp,
                'nonceStr': noncestr,
                'signature': signature
            }

        except Exception as e:
            logger.error(f"生成JSAPI签名失败: {str(e)}")
            raise ValueError(f"生成签名失败: {str(e)}")

    def _get_jsapi_ticket(self) -> str:
        """
        获取jsapi_ticket（需要实现缓存逻辑）

        Returns:
            str: jsapi_ticket
        """
        # TODO: 实现获取和缓存jsapi_ticket的逻辑
        # 1. 先从缓存获取
        # 2. 如果缓存不存在，调用微信API获取
        # 3. 缓存结果（7200秒有效期）
        raise NotImplementedError("jsapi_ticket功能尚未实现")


def get_wechat_service() -> WeChatService:
    """获取微信服务实例"""
    return WeChatService()
