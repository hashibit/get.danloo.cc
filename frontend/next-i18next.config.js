const { i18n } = require('./next.config.js');

module.exports = {
  i18n,
  localePath: require('path').resolve('./public/locales'),
  defaultNS: 'common',
  fallbackNS: 'common',
  reloadOnPrerender: process.env.NODE_ENV === 'development',
  keySeparator: '.',
  nsSeparator: false,
  interpolation: {
    escapeValue: false,
  },
  debug: false,
};