// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const darkCodeTheme = require('prism-react-renderer/themes/dracula')

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Sovereign Cloud Stack Documentation',
  tagline: 'One platform - standardized, built and operated by many.',
  url: 'https://docs.scs.community',
  baseUrl: '/',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'SovereignCloudStack', // Usually your GitHub org/user name.
  projectName: 'docs-page', // Usually your repo name.

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en']
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: { sidebarPath: require.resolve('./sidebarsDocs.js') },
        blog: {
          showReadingTime: true,
          editUrl:
                        'https://github.com/SovereignCloudStack/docs-page/tree/main/'
        },
        theme: {
          customCss: [require.resolve('./src/css/custom.css')]
        }
      })
    ]
  ],
  plugins: [
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'community',
        path: 'community',
        routeBasePath: 'community',
        sidebarPath: require.resolve('./sidebarsCommunity.js')
        // ... other options
      }
    ],
    './src/plugins/docusaurus-plugin-matomo-analytics/index.js'
  ],

  themeConfig:
        /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
        ({
          navbar: {
            title: '',
            logo: {
              alt: 'My Site Logo',
              src: 'img/logo.svg'
            },
            items: [
              {
                type: 'doc',
                docId: 'intro',
                position: 'left',
                label: 'Docs'
              },
              //   { to: '/blog', label: 'Blog', position: 'left' },
              { to: '/community', label: 'Community', position: 'left' },
              {
                href: 'https://github.com/SovereignCloudStack/docs-page',
                label: 'GitHub',
                position: 'right'
              }
            ]
          },
          footer: {
            style: 'light',
            links: [
              {
                title: 'Docs',
                items: [
                  {
                    label: 'Contribute',
                    to: '/docs/intro'
                  }
                ]
              },
              {
                title: 'Community',
                items: [
                  {
                    label: 'Matrix',
                    href: 'https://matrix.to/#/!TiDqlLmEUaXqTemaLc:matrix.org?via=matrix.org'
                  },
                  {
                    label: 'Twitter',
                    href: 'https://twitter.com/scs_osballiance'
                  },
                  {
                    label: 'Mastodon',
                    href: 'https://fosstodon.org/@sovereigncloudstack'
                  }
                ]
              },
              {
                title: 'More',
                items: [
                  // {
                  //   label: 'Blog',
                  //   to: '/blog'
                  // },
                  {
                    label: 'GitHub',
                    href: 'https://github.com/SovereignCloudStack/docs-page'
                  }
                ]
              }
            ],
            copyright:
                    'Sovereign Cloud Stack, SCS and the logo are registered trademarks of the Open Source Business Alliance e.V. — Other trademarks are property of their respective owners.'
          },
          prism: {
            theme: darkCodeTheme,
            darkTheme: darkCodeTheme,
            additionalLanguages: ['powershell', 'ruby']
          },
          matomoAnalytics: {
            matomoUrl:
              'matomo.scs.community',
            siteId: '2',
            phpLoader: 'matomo.php',
            jsLoader: 'matomo.js',
            disableCookies: true
          }
        }),

  themes: [
    [
      // @ts-ignore
      '@easyops-cn/docusaurus-search-local',
      /** @type {import('@easyops-cn/docusaurus-search-local').PluginOptions} */
      // @ts-ignore
      ({
        hashed: true,
        docsDir: ['docs', 'community'],
        docsRouteBasePath: ['/docs', 'community']
      })
    ]
  ]
}

module.exports = config
