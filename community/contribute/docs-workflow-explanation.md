# Documentation workflow explanation

The aim within this documentation is to have a good developer experience and a low entry barrier to start with SCS. For this to achieve we think all docs that define the SCS stack and have been developed by the SCS community should be within this documentation framework.

## Information Architecture

* All general docs are located within the [SovereignCloudStack/docs](https://github.com/SovereignCloudStack/docs) repository.

* Docs that explain, guide or contextualize specific modules such as the openstack-image-manager or the k8s-cluster-api-provider reside within their repository in a seperate docs directory.

Both, the general docs and docs of the external repositories are combined into the one unified documentation collection that is being rendered in a static page on <https://docs.scs.community>. In order to make this work we have developed a workflow that syncs all doc repositories and distills only the relevant markdown files.

The script is called `getDocs`. It is a postinstall script and is executed after `npm install`. This has the advantage to have the docs – coming from the cloud – in your local docusaurus development environment as well as in the build process.

You'll find the script in the root directory of the [SovereignCloudStack/docs-page](https://github.com/SovereignCloudStack/docs-page) repository:

```js title="getDocs.js"
const fs = require('fs')
const { execSync } = require('child_process')

// Read the contents of the "docs.package.json" file and remove all whitespace
const reposJson = fs.readFileSync('./docs.package.json', 'utf8').replace(/\s/g, '')

// Parse the JSON and create an array of repositories
const repos = JSON.parse(reposJson)
const ghUrl = 'https://github.com/'

// Clone each repository, remove git folders and README files, and copy the docs to the target directory
repos.forEach((repo) => {
  const repoDir = `repo_to_be_edited/${repo.label}`

  // Clone the repository
  const cloneCommand = `git clone ${ghUrl + repo.repo} ${repoDir}`
  execSync(cloneCommand)

  // Remove git folders
  const removeGitCommand = `rm -rf ${repoDir}/.git`
  execSync(removeGitCommand)

  // Remove README files
  const removeReadmeCommand = `find ${repoDir} -name "README.md" | xargs rm -f`
  execSync(removeReadmeCommand)

  // Create the docusaurus subdirectory
  const subDirPath = `${repo.target}/${repo.label}`
  fs.mkdirSync(subDirPath, { recursive: true })

  // Copy docs content from A to B
  const copyDocsCommand = `cp -r ${repoDir}/${repo.source} ${subDirPath}`
  execSync(copyDocsCommand)

  // Remove the cloned repository
  const removeRepoCommand = 'rm -rf repo_to_be_edited'
  execSync(removeRepoCommand)
})
```
