// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebarsDocs = {
  docs: [
    "index",
    {
      type: "category",
      label: "Getting Started",
      link: {
        type: "generated-index",
      },
      items: [
        // 'getting-started/overview',
        // 'getting-started/virtualization',
        // 'getting-started/containerization'
      ],
    },
    {
      type: "category",
      label: "IaaS Layer",
      link: {
        type: "generated-index",
      },
      items: [
        {
          type: "category",
          label: "Overview",
          link: {
            type: "generated-index",
          },
          items: [
            // 'iaas/overview/architecture',
            // 'iaas/overview/compute',
            // 'iaas/overview/storage',
            // 'iaas/overview/network',
            // 'iaas/overview/knowledge'
          ],
        },
        {
          type: "category",
          label: "Deployment Examples",
          link: {
            type: "generated-index",
          },
          items: [
            {
              type: "category",
              label: "Deployment A",
              link: {
                type: "generated-index",
              },
              items: [
                // 'iaas/deployment-examples/a/index',
                // 'iaas/deployment-examples/a/hardware',
                // 'iaas/deployment-examples/a/software'
              ],
            },
          ],
        },
        {
          type: "category",
          label: "Guides",
          link: {
            type: "generated-index",
          },
          items: [
            // 'iaas/guides/guide1'
          ],
        },
        {
          type: "category",
          label: "Components",
          link: {
            type: "generated-index",
          },
          items: [
            {
              type: "category",
              label: "Openstack Image Manager",
              link: {
                type: "generated-index",
              },
              items: [
                "iaas/components/openstack-image-manager/overview",
                "iaas/components/openstack-image-manager/requirements",
                "iaas/components/openstack-image-manager/quickstart",
                "iaas/components/openstack-image-manager/configuration",
                "iaas/components/openstack-image-manager/contribute",
              ],
            },
          ],
        },
      ],
    },
    {
      type: "category",
      label: "Container Layer",
      link: {
        type: "generated-index",
      },
      items: [
        {
          type: "category",
          label: "Overview",
          link: {
            type: "generated-index",
          },
          items: [
            // 'container/overview/architecture',
            // 'container/overview/knowledge'
          ],
        },
        {
          type: "category",
          label: "Deployment Examples",
          link: {
            type: "generated-index",
          },
          items: [
            {
              type: "category",
              label: "Deployment A",
              link: {
                type: "generated-index",
              },
              items: [
                // 'container/deployment-examples/a/index',
                // 'container/deployment-examples/a/hardware',
                // 'container/deployment-examples/a/software'
              ],
            },
          ],
        },
        {
          type: "category",
          label: "Guides",
          link: {
            type: "generated-index",
          },
          items: [
            // 'container/guides/guide1'
          ],
        },
        {
          type: "category",
          label: "Components",
          link: {
            type: "generated-index",
          },
          items: [
            {
              type: "category",
              label: "K8s Cluster API Provider",
              link: {
                type: "generated-index",
              },
              items: [
                "container/components/k8s-cluster-api-provider/doc/overview",
                "container/components/k8s-cluster-api-provider/doc/requirements",
                "container/components/k8s-cluster-api-provider/doc/quickstart",
                "container/components/k8s-cluster-api-provider/doc/make-reference",
                "container/components/k8s-cluster-api-provider/doc/application-credentials",
                "container/components/k8s-cluster-api-provider/doc/configuration",
                "container/components/k8s-cluster-api-provider/doc/Maintenance_and_Troubleshooting",
                "container/components/k8s-cluster-api-provider/doc/LoadBalancer-ExtTrafficLocal",
                "container/components/k8s-cluster-api-provider/doc/Upgrade-Guide",
                "container/components/k8s-cluster-api-provider/doc/roadmap",
                {
                  type: "category",
                  label: "Usage",
                  items: [
                    "container/components/k8s-cluster-api-provider/doc/usage/usage",
                    "container/components/k8s-cluster-api-provider/doc/usage/create-new-cluster",
                    "container/components/k8s-cluster-api-provider/doc/usage/managing-many-clusters",
                    "container/components/k8s-cluster-api-provider/doc/usage/cluster-mgmt-capi-mgmt-node",
                    "container/components/k8s-cluster-api-provider/doc/usage/multi-az-and-multi-cloud-environments",
                    "container/components/k8s-cluster-api-provider/doc/usage/testing",
                  ],
                },
              ],
            },
          ],
        },
      ],
    },
    {
      type: "category",
      label: "Operating SCS",
      link: {
        type: "generated-index",
      },
      items: [
        // 'operating-scs/overview',
        // {
        //   type: 'category',
        //   label: 'Guides',
        //   link: {
        //     type: 'generated-index'
        //   },
        //   items: [
        //     'operating-scs/guides/guide-1'
        //   ]
        // },
        // {
        //   type: 'category',
        //   label: 'Monitoring',
        //   link: {
        //     type: 'generated-index'
        //   },
        //   items: [
        //     'operating-scs/monitoring/index'
        //   ]
        // },
        // {
        //   type: 'category',
        //   label: 'Incident Management',
        //   link: {
        //     type: 'generated-index'
        //   },
        //   items: [
        //     'operating-scs/incident-management/index'
        //   ]
        // },
        // {
        //   type: 'category',
        //   label: 'Audits',
        //   link: {
        //     type: 'generated-index'
        //   },
        //   items: [
        //     'operating-scs/audits/index'
        //   ]
        // },
        // {
        //   type: 'category',
        //   label: 'Lifecycle Management',
        //   link: {
        //     type: 'generated-index'
        //   },
        //   items: [
        //     'operating-scs/lifecycle-management/index'
        //   ]
        // },
        // {
        //   type: 'category',
        //   label: 'Logging',
        //   link: {
        //     type: 'generated-index'
        //   },
        //   items: [
        //     'operating-scs/logging/index'
        //   ]
        // },
        {
          type: "category",
          label: "Metering",
          link: {
            type: "generated-index",
          },
          items: ["operating-scs/metering/meter-configuration"],
        },
      ],
    },
    // {
    //   type: 'category',
    //   label: 'Identity and Access Management (IAM)',
    //   link: {
    //     type: 'generated-index'
    //   },
    //   items: [
    //     'iam/index'
    //   ]
    // },
    {
      type: "category",
      label: "Releases",
      link: {
        type: "generated-index",
      },
      items: [
        "releases/Release0",
        "releases/Release1",
        "releases/Release2",
        "releases/Release3",
        "releases/Release4",
      ],
    },
    // {
    //   type: 'category',
    //   label: 'Standards',
    //   link: {
    //     type: 'generated-index'
    //   },
    //   items: [
    //     'standards/index'
    //   ]
    // },
    {
      type: "doc",
      id: "faq/index",
      label: "FAQ",
    },
    "glossary",
  ],
};

module.exports = sidebarsDocs;
