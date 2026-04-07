# Internationalization (i18n) Deployment Guide

## Overview

The Danloo frontend now supports both Chinese (zh) and English (en) languages with full internationalization using next-i18next.

## Environment Configuration

Set the default language using the `DEFAULT_LOCALE` environment variable:

### Chinese (Default)
```bash
export DEFAULT_LOCALE=zh
```

### English
```bash
export DEFAULT_LOCALE=en
```

## Development Scripts

### Run development server with specific language:
```bash
# Chinese (default)
npm run dev
# or explicitly
npm run dev:zh

# English
npm run dev:en
```

## Build Scripts

### Build for production with specific language:
```bash
# Chinese (default)
npm run build
# or explicitly
npm run build:zh

# English
npm run build:en
```

## Docker Deployment

### Chinese Version
```dockerfile
FROM node:18-alpine
# ... other instructions
ENV DEFAULT_LOCALE=zh
CMD ["npm", "start"]
```

### English Version
```dockerfile
FROM node:18-alpine
# ... other instructions
ENV DEFAULT_LOCALE=en
CMD ["npm", "start"]
```

## Docker Compose

```yaml
version: '3.8'
services:
  danloo-frontend-zh:
    build: .
    environment:
      - DEFAULT_LOCALE=zh
      - NEXT_PUBLIC_API_URL=http://api:8000/api/v1
    ports:
      - "3000:3000"
  
  danloo-frontend-en:
    build: .
    environment:
      - DEFAULT_LOCALE=en
      - NEXT_PUBLIC_API_URL=http://api:8000/api/v1
    ports:
      - "3001:3000"
```

## Vercel Deployment

### Multiple Deployments
Create separate Vercel projects:

1. **Chinese Version**: Set environment variable `DEFAULT_LOCALE=zh`
2. **English Version**: Set environment variable `DEFAULT_LOCALE=en`

### Single Deployment with Runtime Detection
The app can dynamically detect locale based on browser preferences or URL if `localeDetection` is enabled in `next.config.js`.

## Translation Files

Translation files are located in `/public/locales/`:
- `/public/locales/zh/common.json` - Chinese translations
- `/public/locales/en/common.json` - English translations

## Adding New Languages

1. Add locale to `next.config.js`:
```javascript
i18n: {
  locales: ['en', 'zh', 'ja'], // Add new locale
  defaultLocale: process.env.DEFAULT_LOCALE || 'zh',
}
```

2. Create translation file:
```
/public/locales/ja/common.json
```

3. Add build script to `package.json`:
```json
"build:ja": "DEFAULT_LOCALE=ja next build"
```

## Testing

Test both language versions:
```bash
# Test Chinese
DEFAULT_LOCALE=zh npm run dev

# Test English  
DEFAULT_LOCALE=en npm run dev
```

## Production Checklist

- [ ] Set `DEFAULT_LOCALE` environment variable
- [ ] Verify all translation keys are present in both language files
- [ ] Test UI layout with both languages (different text lengths)
- [ ] Verify date/time formatting for target locale
- [ ] Test form validation messages
- [ ] Verify error messages are translated