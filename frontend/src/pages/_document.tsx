import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="en">
      <Head />
      <body>
        {/* Anti-FOUC: apply saved theme before page renders, default light */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('theme');var resolved=(t==='dark')?'dark':'light';document.documentElement.setAttribute('data-theme',resolved);}catch(e){document.documentElement.setAttribute('data-theme','light');}})();`,
          }}
        />
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
