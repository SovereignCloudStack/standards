---
sidebar_position: 1
---

# SCS Documentation Collection

[![Creative Commons Attribution-ShareAlike 4.0 International](https://licensebuttons.net/l/by-sa/4.0/88x31.png)](http://creativecommons.org/licenses/by-sa/4.0/)

## About

SCS is made up of different and optional modules, services and repositories. These building blocks are not developed by the SCS Project Team. It is a carefully curated and supported collection of repositories, forming all together the Sovereign Cloud Stack. Therefore individual documentations reside in their owner organisations.

The aim of this documentation is to give operators, cloud service provides and others an easy overview and entry into a common collection of documentation, without the need of searching individual projects doc pages.

![Repositories](overview.svg)

## Structure

### Conceptual Structure

We follow the [Diataxis Framework](https://diataxis.fr/) to structure our documentation, in order respond best to our users needs.

### Directory Structure

In order to get all the different docs into one place and to render a comprehensive static page for best Developer Epxerience, the subprojects need to be consumed by this main docs repository. This is will be managed by git's subtree feature and not as submodule.

As the final output in this repository will be a statically generated website, the subtree docs repositories should only contain markdown and static files. If a sub repository should reside within a repository which code it is documenting, it should also be imported as subtree or submodule. This is a bit more management overhead, but also enbables the freedom of choice for rendering the content in another output repository as a static page with any docs renderer. But furthermore this enables this SCS Docs repository to inherit all the different docs rendered into one page for the best user experience.

#### SCS project repo strucutre

```jsx
project
├── static  // static content
├── blog    // optional blog
├── src     // source files
├── docs    // the folder where all individual docs reside as subtree modules
│   └── @osism/openstack-image-manager-docs
│       ├── overiew.md
│       ├── usage.md
│       ├── requirements.md
│       ├── images
│       │   ├── logo.png
│       │   └── image.svg
│       └── support
│           ├── index.js
│           └── styles.module.css
│   └── @scs/Docs
│       ├── overview.md
│       ├── standards.md
│       ├── requirements.md
│       ├── images
│       │   ├── logo.png
│       │   └── image.svg
│       └── Design Docs
│           ├── lorem.md
│           └── ipsum.md
.   └── @abc/xyz
.       .
.          .
```

```jsx
@osism/openstack-image-manager
├── code  // static content
├── blog    // optional blog
├── src     // source files
├── docs    // the folder where all individual docs reside as subtree modules
│   └── @osism/openstack-image-manager-docs
│       ├── overiew.md
│       ├── usage.md
│       ├── requirements.md
│       ├── images
│       │   ├── logo.png
│       │   └── image.svg
│       └── support
│           ├── index.js
│           └── styles.module.css
```

### Git subtree

[The Power of Git Subtree by Nicola Paolucci](https://blog.developer.atlassian.com/the-power-of-git-subtree/?_ga=2-71978451-1385799339-1568044055-1068396449-1567112770)

[Git Subtree Basics Gist](https://gist.github.com/SKempin/b7857a6ff6bddb05717cc17a44091202)

In order to add a docs repository we use the following git commmand:

```bash
git subtree add --prefix /docs/{repo name} {remote repo URL} {remote branch} --squash
```

For updating the repo we use the following git commmand:

```bash
git subtree pull --prefix /docs/{repo name} {remote repo URL} {remote branch} --squash
```
