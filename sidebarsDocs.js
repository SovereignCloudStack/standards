// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebarsDocs = {
  docs: [
    'index',
    {
      type: 'category',
      label: 'K8s Cluster API Provider',
      link: {
        type: 'generated-index'
      },
      items: [
        'k8s-cluster-api-provider/doc/overview',
        'k8s-cluster-api-provider/doc/requirements',
        'k8s-cluster-api-provider/doc/quickstart',
        'k8s-cluster-api-provider/doc/getting-started',
        'k8s-cluster-api-provider/doc/application-credentials',
        'k8s-cluster-api-provider/doc/configuration',
        'k8s-cluster-api-provider/doc/Maintenance_and_Troubleshooting',
        'k8s-cluster-api-provider/doc/LoadBalancer-ExtTrafficLocal',
        'k8s-cluster-api-provider/doc/Upgrade-Guide',
        'k8s-cluster-api-provider/doc/teardown',
        {
          type: 'category',
          label: 'Usage',
          items: [
            'k8s-cluster-api-provider/doc/usage/usage',
            'k8s-cluster-api-provider/doc/usage/create-new-cluster',
            'k8s-cluster-api-provider/doc/usage/managing-many-clusters',
            'k8s-cluster-api-provider/doc/usage/cluster-mgmt-capi-mgmt-node',
            'k8s-cluster-api-provider/doc/usage/multi-az-and-multi-cloud-environments',
            'k8s-cluster-api-provider/doc/usage/testing'
          ]
        }
      ]
    },
    {
      type: 'category',
      label: 'OSISM Testbed',
      link: {
        type: 'generated-index'
      },
      items: [
        'testbed/doc/overview',
        'testbed/doc/requirements',
        'testbed/doc/preparations',
        'testbed/doc/getting_started',
        'testbed/doc/authentication',
        'testbed/doc/configuration',
        'testbed/doc/networking',
        'testbed/doc/usage',
        'testbed/doc/important_notes',
        'testbed/doc/contribute',
        'testbed/doc/license',
        {
          type: 'category',
          label: 'Cloud in a Box',
          items: ['testbed/cloud-in-a-box/doc/quickstart']
        }
      ]
    },
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
      label: 'Status Page',
      link: {
        type: 'generated-index'
      },
      items: [
        'status-page-openapi/docs/overview',
        'status-page-openapi/docs/components',
        'status-page-openapi/docs/levels_of_consensus'
      ]
    },
    {
      type: 'category',
      label: 'Release Notes',
      link: {
        type: 'generated-index'
      },
      items: [
        'release-notes/Release0',
        'release-notes/Release1',
        'release-notes/Release2',
        'release-notes/Release3',
        'release-notes/Release4'
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
