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
