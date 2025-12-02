import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
    return (
        <Html lang="fr">
            <Head>
                <meta charSet="utf-8" />
                <meta name="description" content="M365 License Optimizer - SaaS tool for Microsoft CSP/MPN partners" />
                <link rel="icon" href="/favicon.ico" />
            </Head>
            <body>
                <Main />
                <NextScript />
            </body>
        </Html>
    );
}
