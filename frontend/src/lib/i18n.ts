import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import { UserConfig } from 'next-i18next';

// 创建符合 next-i18next 要求的配置对象
const i18nConfig: UserConfig = {
  i18n: {
    locales: ['en', 'zh'],
    defaultLocale: process.env.DEFAULT_LOCALE || 'zh',
    localeDetection: false as const, // 使用 as const 确保类型是字面量类型
  },
  localePath: './public/locales',
  defaultNS: 'common',
  fallbackNS: 'common',
  reloadOnPrerender: process.env.NODE_ENV === 'development',
  keySeparator: '.',
  nsSeparator: false as const, // 使用 as const 确保类型是字面量类型
  interpolation: {
    escapeValue: false,
  },
};

export const getStaticProps = async (locale: string) => ({
  props: {
    ...(await serverSideTranslations(locale, ['common'], i18nConfig)),
  },
});

export const getServerSideProps = async (context: { locale: string }) => ({
  props: {
    ...(await serverSideTranslations(context.locale, ['common'], i18nConfig)),
  },
});
