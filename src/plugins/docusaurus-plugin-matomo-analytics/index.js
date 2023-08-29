const path = require('path')

// based on https://github.com/karser/docusaurus-plugin-matomo with extended parameters

function matomoAnalytics (context, options) {
  const { siteConfig } = context
  const { themeConfig } = siteConfig
  const { matomoAnalytics } = themeConfig || {}

  if (!matomoAnalytics) {
    throw new Error(
      'Please specify \'matomo\' object in \'themeConfig\' with \'matomoUrl\' and \'siteId\' fields in it to use docusaurus-plugin-matomo'
    )
  }

  const { matomoUrl, siteId } = matomoAnalytics

  if (!matomoUrl) {
    throw new Error(
      'Please specify the `matomoUrl` field in the `themeConfig.matomo`'
    )
  }
  if (!siteId) {
    throw new Error(
      'Please specify the `siteId` field in the `themeConfig.matomo`'
    )
  }

  const isProd = process.env.NODE_ENV === 'production'
  return {
    name: 'docusaurus-plugin-matomo-analytics',

    getClientModules () {
      return isProd ? [path.resolve(__dirname, './track')] : []
    },

    injectHtmlTags () {
      return {
        headTags: [
          {
            tagName: 'link',
            attributes: {
              rel: 'preconnect',
              href: `${matomoAnalytics.matomoUrl}`
            }
          },
          {
            tagName: 'script',
            innerHTML: `
                var _paq = window._paq = window._paq || [];
                _paq.push(["setDocumentTitle", document.domain + "/" + document.title]);
                ${matomoAnalytics.cookieDomain ? `_paq.push(["setCookieDomain", "${matomoAnalytics.cookieDomain}"]);` : ''}
                ${matomoAnalytics.domains ? `_paq.push(["setDomains", ["${matomoAnalytics.domains}"]])` : ''}
                ${matomoAnalytics.campaignNameKey ? `_paq.push(["setCampaignNameKey", "${matomoAnalytics.campaignNameKey}"]);` : ''}
                ${matomoAnalytics.campaignKeywordKey ? `_paq.push(["setCampaignKeywordKey", "${matomoAnalytics.campaignKeywordKey}"]);` : ''}
                ${matomoAnalytics.doNotTrack ? `_paq.push(["setDoNotTrack", ${matomoAnalytics.doNotTrack}]);` : ''}
                ${matomoAnalytics.disableCookies ? '_paq.push(["disableCookies"]);' : ''}
                _paq.push(['trackPageView']);
                _paq.push(['enableLinkTracking']);
                    (function() {
                        var u="${matomoAnalytics.matomoUrl}";
                        _paq.push(['setTrackerUrl', u+'${matomoAnalytics.phpLoader}']);
                        _paq.push(['setSiteId', '${matomoAnalytics.siteId}']);
                        var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
                        g.async=true; g.src=u+'${
                            matomoAnalytics.jsLoader
                        }'; s.parentNode.insertBefore(g,s);
                    })();

            `
          }
        ]
      }
    }
  }
}

module.exports = matomoAnalytics
