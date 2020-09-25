# Objective

The objective of this document is to define a basic set of roles and their identifiers / names in SCS. These roles can be used in the Identity and Access Management (IAM) of SCS itself and / or in services provided based on SCS. As Roles are often derived from Usecases which are derived from terms used in a project, the document starts with a definition of terms used in SCS and/or GAIA-X. These definitions should be moved into a separate document in the future.

# Principles used to create this document

Where possible the roles and names are derived from existing definitions or conventions used in the underlying software. As SCS is part of GAIA-X, the terms/definitions of GAIA-X are taken as a baseline and will be extended with additional roles needed in SCS. For reference, the current state of relevant GAIA-X definitions can be found at the end of this document.

# SCS terms and their definition

These terms were defined taking into account the GAIA-X definitions to ensure that the same terms are shared.

term               | definition 
-------------------|---------------
Provider           | Legal entity providing SCS to customers. The Provider is typically in control of physical infrastructure (Datacenter, Hosts, Storage, Network etc.) but also employs people who deploy and operate SCS.
Consumer           | Legal entity which can access and/or consume services hosted on SCS. Typically a Consumer is a customer of a Provider.
End User           | Person which accesses Services running on SCS. Typically a person knows about the Consumer entity and the services but not about SCS or the Provider. An End User might be an employee or customer of the Consumer.
Identity           | An Idenity is a technical unique representation of an entity (a Person, a legal entity like a Consumer, or an technical entity like a Service). An Identity might need to be trustworthy, so the technical representation has to include a trust relationship.
Identity System   | A technical solution that does authentication for Identities (i.e. checking a username, password and 2nd factor) and provides additional attributes to the identity.
Module             | Technical solution / Software which is part of a SCS deployment.
Access Rights      | Represent different capabilities an Identity might have while interacting with a Module. For example read or write access to a file system or access to functionality of an API.
Role               | A role is a group of Identities connected with a set of Access Rights for Modules of SCS. Authorization to access modules is done by checking whether the accessing Identity is member in a Role that has the needed Access Rights assigned.
Host               | A Host is a physical machine which is part of a Node. A Node consists of several Hosts.
Node               | A Node is a deployment of SCS which offers Services for Customers and/or Endusers. A Node typically is a group of physical Hosts.
Operator           | Person operating parts of SCS. Each Person is represented by an Identity. Access rights needed to operate are given by assigning an Identity to a Role.

# SCS modules / components

A module or component of SCS typically is a software stack deployed with a dedicated usecase. This list needs to be elaborated over time.

**this is a best guess example and needs review**

module                 | description
-----------------------|--------------------------
OpenStack_<submodule>  | TBD
Kubernetes_<submodule> | TBD
*to be continued*      |

# SCS Roles

Set of Roles which are initially part of SCS.

A Role should be defined as "<Module>_<Usecase>", where "<Module>" is the main module this role applies to and "<Usecase>" a short term to give context which kind of rights / options are given to an identity as member of this role.

**this is a best guess example and needs review**

Role                  | Description
----------------------|--------------------------
host_deployment       | Access to a Host by an identity used in automated deployment and maintenance. Typicall Identities used by Ansible to access Hosts.
host_operator         | Full Access to a Host. Typically there is one Host Operator Role for each physical Host, so the Role can be given temporary to a Person in case of an incident and removed afterwards.
OpenStack_Deployment  | TBD
OpenStack_Operator    | TBD
OpenStack_Customer    | TBD
Kubernetes_Deployment | TBD
Kubernetes_Operator   | TBD
Kubernetes_Customer   | TBD
*to be continued*      |



# Current definitions of GAIA-X

This is an excerpt if terms defined in the GAIA-X project. The definitions are work in progress and might change, so this document might be outdated.

term   | definition                         | relevance in SCS | source / link
-------|------------------------------------|------------------|---------------
GAIA-X Participant | A GAIA-X Participant is a entity/legal person that can take on one or multiple of the following roles: Provider, Consumer | yes, see Provider / Consumer / Principal | [source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_1_Terms_and_Definitions-Participant)
Gaia-X Consumer    | A role of a GAIA-X Participant with user & devices, searching/ordering services and maintaining a business relationship to Providers. Consumer consume Service Instances but can also provide them to their End-Users. | Access to services hosted on SCS | [source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_2_Terms_and_Definitions-Consumer.rst)
Gaia-X Visitor     | Anonymous, non-registered entity (natural person, bot, ...) browsing a GAIA-X Catalogue. | not directly | [source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_3_Terms_and_Definitions-Visitor.rst)
Federated Identity Component |Component, which ensures trust and trustworthiness between GAIA-X, the interacting Identity System and all GAIA-X Participants, which automatically includes the GAIA-X Participant. Process to be guaranteed to ensure the trust, involved during the Onboarding Process. This component guarantees identity proofing of the involved Participants to make sure that GAIA-X Participants are who they claim to be. | Access to Services provided by or hosted on SCS need to be available for Identities confirmed by the component. |[source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_4_Terms_and_Definitions-FederatedIdentityComponent.rst)
Principal          | Natural person or technical system who act on behalf of a GAIA-X Participant.| yes, see below | [source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_5_Terms_and_Definitions-Principal.rst)
Principal@Provider | Person/Technical System of a GAIA-X Participant in the context of the Provider role.| A Principal ("person") of a Provider will interact in various roles with the SCS deployment | [source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_5_Terms_and_Definitions-Principal.rst)
Principal@Consumer | Person/Technical System of a GAIA-X Participant in the context of the Consumer role.| A Principal ("person") of a Consumer will access services provided by or hosted on SCS. | [source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_5_Terms_and_Definitions-Principal.rst)
GAIA-X AM          | GAIA-X internal Access Management component | | [source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_6_Terms_and_Definitions-GAIA-X_AM.rst)
GAIA-X Asset       | In GAIA-X, an Asset is either of Node, Service, Service Instance or Data Asset. | SCS deployments are Nodes which can provide all other assets. | [source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_7_Terms_and_Definitions-GAIA-X_Asset.rst)
Self-Description   | GAIA-X Self-Descriptions express characteristics of Assets and Participants. A GAIA-X Self-Description describes properties and claims of an Asset or Participant. Self-Descriptions are tied to the Identifier of the respective Asset or Participant. | SCS nodes have to deliver a self description. | [source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_8_Terms_and_Definitions-Self-Description.rst)
Federated Catalogue| The Federated Catalogue is a logical combination of a Self-Description repository and search algorithms so that Self-Description-based attribute searches can be processed | Self descriptions delivered by SCS will be available in the Catalogue. | [source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_9_Terms_and_Definitions-Federated_Catalogue.rst)
Identity           | Identity is composed of an unique identifier and an attribute or set of attributes that uniquely describe a entity (Participant/Asset) within a given context. An Identity should be secure and trustworthy.| Is fully applicable to SCS | [source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_10_Terms_and_Definitions-Identity.rst)
Identity System    | Identity system that does authenticate/provides additional attributes to the identity of the GAIA-X Principal and forward this identity to the requestor. | SCS deployments needs a Identity System. Assets provided by SCS need to trust other Identity Systems which are approved by the Federated Identity Component | [source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_11_Terms_and_Definitions-IdentitySystem.rst)
End-User           | A entity outside GAIA-X context, using GAIA-X Service Instances from a Consumer Organization. End-Users authorization responsibility is within the Consumer Organization, which is acting as a secure proxy in between. | Relevant for services hosted on SCS. | [source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_12_Terms_and_Definitions-End-User.rst)
Service Provider AM| The Service Ordering Process will involve the Consumer and the Service Provider. The Service Provider will create the Service Instance and will grant access for the Consumer by this component. | | [source](https://gitlab.com/gaia-x/gaia-x-core/gaia-x-core-document-technical-concept-architecture/-/blob/master/architecture_decision_records/draft-ADR-004_13_Terms_and_Definitions-Service_Provider_AM.rst)
GAIA-X Provider           | A Provider is a legal entity which operates one or more Nodes | Entity running SCS | [Gaia-X terms](https://gaia.coyocloud.com/pages/wiki-fuer-alle/apps/wiki/wiki/list/view/857dfdc2-ab58-4f50-b200-6f6efd0caad9) |
GAIA-X Node               | A Node is the physical environment where a Provider provides Services to Consumers. A Node consists of several Hosts. | | [Gaia-X terms](https://gaia.coyocloud.com/pages/wiki-fuer-alle/apps/wiki/wiki/list/view/f944755e-0301-4e46-a5a5-a890aa5f2b5f)|
