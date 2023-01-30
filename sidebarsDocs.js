// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebarsDocs = {
  docs: [
    'intro',
    {
      type: 'category',
      label: 'Release Notes',
      items: [
        'release-notes/Release1',
        'release-notes/Release2',
        'release-notes/Release3',
        'release-notes/Release4',
        'release-notes/ReleaseX'
      ]
    },
    {
      type: 'category',
      label: 'Standards',
      items: [
        'standards/scs-0001-v1-sovereign-cloud-standards',
        'standards/scs-xxxx-v1-sovereign-cloud-standards-yaml'
      ]
    }
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
    // {
    //   type: 'category',
    //   label: 'Openstack Image Manager',
    //   items: [
    //     'openstack-image-manager/configuration',
    //     'openstack-image-manager/contribute',
    //     'openstack-image-manager/overview',
    //     'openstack-image-manager/quickstart',
    //     'openstack-image-manager/requirements'
    //   ]
    // }
  ]
}

module.exports = sidebarsDocs
