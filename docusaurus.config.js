// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const darkCodeTheme = require('prism-react-renderer/themes/dracula')

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'One platform — standardized, built and operated by many.',
  tagline: 'Documentation and Community Platform for the Sovereign Cloud Stack',
  url: 'https://docs.scs.community',
  baseUrl: '/',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',
  markdown: {
    mermaid: true
  },
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
          editUrl: 'https://github.com/SovereignCloudStack/docs-page/tree/main/'
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
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'standards',
        path: 'standards',
        routeBasePath: 'standards',
        sidebarPath: require.resolve('./sidebarsStandards.js')
      }
    ],
    './src/plugins/docusaurus-plugin-matomo-analytics/index.js'
  ],

  themeConfig:
        /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
        ({
          metadata: [{ title: 'One platform — standardized, built and operated by many.', description: 'Documentation and Community Platform for the Sovereign Cloud Stack' }],
          image: 'img/summit-social.png',
          announcementBar: {
            id: 'scs_summit',
            content: '<a target="_blank" rel="noopener noreferrer" href="https://scs.community/summit" style="text-decoration: none"><b>Join us for our first SCS Summit on 23rd and 24th of May 2023 in Berlin. </b></a>',
            backgroundColor: '#ffb729',
            textColor: '#000',
            isCloseable: true
          },
          navbar: {
            title: '',
            logo: {
              alt: 'SCS',
              src: 'img/logo.svg'
            },
            items: [
              //   { to: '/blog', label: 'Blog', position: 'left' },
              { to: '/docs', label: 'Docs', position: 'left' },
              { to: '/standards', label: 'Standards', position: 'left' },
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
                    to: '/docs'
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
            copyright: 'Sovereign Cloud Stack, SCS and the logo are registered trademarks of the Open Source Business Alliance e.V. — Other trademarks are property of their respective owners.'
          },
          prism: {
            theme: darkCodeTheme,
            darkTheme: darkCodeTheme,
            additionalLanguages: ['powershell', 'ruby']
          },
          matomoAnalytics: {
            matomoUrl: 'https://matomo.scs.community/',
            siteId: '2',
            phpLoader: 'matomo.php',
            jsLoader: 'matomo.js',
            disableCookies: true
          }
        }),

  themes: [
    '@docusaurus/theme-mermaid',
    [
      // @ts-ignore
      '@easyops-cn/docusaurus-search-local',
      /** @type {import('@easyops-cn/docusaurus-search-local').PluginOptions} */
      // @ts-ignore
      ({
        hashed: true,
        docsDir: ['docs', 'community', 'standards'],
        docsRouteBasePath: ['docs', 'community', 'standards']
      })
    ]
  ]
}

module.exports = config
