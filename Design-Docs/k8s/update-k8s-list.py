from github import Github
import jinja2

repos = Github().get_organization('SovereignCloudStack').get_repos()


def looks_like_k8s_repo(repo):
    return repo.name.startswith('k8s-')


repos = filter(looks_like_k8s_repo, repos)

loader = jinja2.FileSystemLoader(searchpath="")
environment = jinja2.Environment(loader=loader, keep_trailing_newline=True)

template = environment.get_template('README.md.tmpl')
result = template.render({
    'repos': repos
})

with open('README.md', "w") as fp:
    fp.write(result)
