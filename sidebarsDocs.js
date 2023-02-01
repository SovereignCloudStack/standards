// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebarsDocs = {
  docs: [
    'intro',
    {
      type: 'category',
      label: 'Openstack Image Manager',
      link: {
        type: 'generated-index'
      },
      items: [
        'openstack-image-manager/overview',
        'openstack-image-manager/requirements',
        'openstack-image-manager/quickstart',
        'openstack-image-manager/configuration',
        'openstack-image-manager/contribute'
      ]
    },
    {
      type: 'category',
      label: 'Release Notes',
      link: {
        type: 'generated-index'
      },
      items: [
        'release-notes/Release1',
        'release-notes/Release2',
        'release-notes/Release3',
        'release-notes/Release4',
        'release-notes/ReleaseX'
      ]
    },
    'glossary'
    /* No documents available yet in https://github.com/SovereignCloudStack/docs/tree/main/operations
    {
      type: 'category',
      label: 'Operating SCS',
      items: [
        'operations/iaas/',
        'operations/iam/',
        'operations/kaas/',
        'operations/operations/'
      ]
    },
    */
  ]
}

module.exports = sidebarsDocs
