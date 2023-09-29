# Zuul users guide

## Prerequisites

1. Repository is known by [SCS Zuul](https://zuul.scs.community)
2. Basic ansible knowledge
3. Basic yaml knowledge
4. zuul-client installed (Only if you want to create secrets. [See also](#what-about-secrets))

Check [SCS Zuul projects](https://zuul.scs.community/t/SCS/projects) for your repository to
be available. If it is missing you need an administrator to get your repository
configured to Zuul.

## Who is it for?

You may have heard about Zuul and may ask yourself if it is capable to support you.
Basically everything you use ansible for can be done using Zuul. That is not always
a good thing since you may get careless and your workload will exceed the CI/CD concept.

If you find yourself doing things under the following list you are at the right place.

1. Code testing
2. Deployment tests using IaC

If you want to, let's say, monitor something using Zuul, that is possible but not the
intended use case.

## Where do I start?

Right in your project's repository! The only prerequisite is that
your repository you want Zuul to work on is known by Zuul. This is done by the Zuul's
tenant configuration. To update this configuration you need access to the Zuul instance
or ask an administrator for help.

We assume that Zuul knows about your repository so we can get started. There are three
topics that you should know about. To get jobs running you need the "job" itself. Jobs run
within a "pipeline". The third important thing is to provide a "project" definition.

## Where to save the Zuul relevant data?

Zuul will parse all branches of the untrusted repositories that Zuul knows about.
Your repository is most likely an untrusted one since only the configuration repositories should
have the "trusted" state.
So it doesn't matter whether you have just one branch containing Zuul files or all branches. Zuul
is looking for the following pathes on your repositories root.

```bash
./zuul.yaml # everything is in here

./.zuul.yaml # ... or here

./zuul.d/ # use directory style to get a bit of a structure
├── jobs.yaml
└── project.yaml

./.zuul.d/ # the same as before just hidden
├── jobs.yaml
└── project.yaml
```

Just use exactly one of the four possibilities.

If using the directory style configuration all `yaml` files within this directory will be
processed. If your projects configuration is small enough you may put all information in
a single file called `zuul.yaml`. It is also possible to create the file or the directory
with a leading dot to hide them for non zuul related work within the repository.

### Projects

If Zuul is configured to observe your repository it will have a look at your projects
definition. Minimal example:

```yaml
- project:
    name: my-org/my-repo
    default-branch: main
    merge-mode: "squash-merge"
    my_pipeline1:
      jobs:
        - my_job1
        - my_job2
        ......
    my_pipeline2:
      jobs:
        - my_jobs
    ...

```

By default Zuul will observe all branches for such files. We have to set the repository name
that have to match the exact value that was set for Zuul. Set a default-branch where actions
that don't match an explicit branch are executed on. Set the merge-mode that Zuul has to use.
But beware that not all issue tracker support all methods. For github squash-merge will work.

After these three properties add the pipelines you want to use to the project definition.
With the `jobs` list you define which jobs to run in which pipeline.

[See official documentation](https://zuul-ci.org/docs/zuul/latest/config/project.html)

### Pipelines

Every Zuul instance will have at least one repository that is used for configuration. There
you will find the available pipelines. Pipelines are used to run your jobs on a periodic or
event driven base. Pipelines can be used to run other pipelines and to keep your jobs in a
defined order if you need this.

Have a look at the configuration repository to utilize the pipelines for your repository.
See available [pipelines](https://github.com/SovereignCloudStack/zuul-config/blob/main/zuul.d/gh_pipelines.yaml) for SCS.
You are not able to define new pipelines outside of a so called "configuration" repository. Since,
by default your repo is considered "untrusted". So in the first place you don't need to
think about, how to create a pipeline. Just use one that fits your needs as close as possible. Next you will
find an enumeration and a small description about the available pipelines in SCS Zuul.

Pipelines available in SCS Zuul:

#### 1. check

- event driven pipeline
- runs if a pull request is created, changed or reopened
- re-runs if a comment contains `recheck`

#### 2. gate

- event driven pipeline
- trigger events: pull_request_review, pull_request, check_run

#### 3. post

- event driven pipeline
- trigger event: post

#### 4. tag

- event driven pipeline
- trigger event: push

#### 5. e2e-test

- event driven pipeline
- trigger event: pull_request

#### 6. e2e-quick-test

- event driven pipeline
- trigger event: pull_request

#### 7. unlabel-on-update-e2e-test

- event driven pipeline
- trigger event: pull_request

#### 8. unlabel-on-update-e2e-quick-test

- event driven pipeline
- trigger event: pull_request

#### 9. periodic-hourly

- time based pipeline that runs every hour

#### 10. periodic-daily

- time based pipeline that runs every day at 3 o'clock am.

#### 11. compliance_check

- time based pipeline that runs every 15 minutes

If you want to know more about pipelines: [See official documentation](https://zuul-ci.org/docs/zuul/latest/config/pipeline.html)

### Jobs

All jobs that your Zuul instances knows of can be used for your own purposes.
Call them directly or implement a job that uses an existing job as parent.
Didn't find the right job? Than we have to create a new one. Existing jobs
can be found in the web ui of your Zuul instance: [Example](https://zuul.scs.community/t/SCS/jobs)

First have a look on a basic job example:

```yaml
- job:
    name: base
    parent: null
    description: |
      The recommended base job.

      All jobs ultimately inherit from this.  It runs a pre-playbook
      which copies all of the job's prepared git repos on to all of
      the nodes in the nodeset.

      It also sets a default timeout value (which may be overidden).
    pre-run: playbooks/base/pre.yaml
    post-run:
      - playbooks/base/post.yaml
      - playbooks/base/post-logs.yaml
    roles:
      - zuul: zuul/zuul-jobs
    timeout: 1800
    nodeset:
      nodes:
        - name: ubuntu-jammy
          label: ubuntu-jammy
```

Each job needs a name that has to be unique within the whole tenant.
A useful convention to achieve this is to prepend the name of the repository.
Each job need to define whether there is parent job or not.
Jobs without a parent are called "base" jobs. Usually you don't want to implement base jobs since
there are already some base jobs that implement often used stuff. A description may not be mandatory
but is obviously useful.

Necessary for Zuul to do anything you just need to add a `run` or `roles` property. Within a job that is
like a `noop` job or just printing something to stdout that is everything you need to run your first job.
Since anything we want to do requires a little bit more you have to define a nodeset. The nodes
are used to run your playbooks on. In 99,9% you will need this too.

The properties `pre-run` and `post-run` are useful for bootstrap and cleanup. If your actual job wants to create
bootstrap some infrastructure you can to this in the `pre-run`. Using an cloud provider you want to release
no longer used resources. That can be done in the `post-run`. If you are using a parent job it is likely
that the parent job may has pre- and post-run playbooks. In this case your pre- and post-run playbooks are
"nested". Example:

1. pre-run parent
2. pre-run my job
3. post-run my job
4. post-run parent

If your job exceeds the defined timeout, the job is considered as failed.

[See official documentation](https://zuul-ci.org/docs/zuul/latest/config/job.html)

#### What about secrets?

Right now you should be able to run basic tasks. But what if you try to test something
that needs credentials to connect to an outside service? Or you have to address additional
ressources in an openstack environment and you have to use something like app credentials?

That is where job secrets are used. Example:

```yaml
- job:
    name: SOME_JOB
    parent: base
    description: |
      A job basic job used as example
    secrets:
      - name: clouds_conf
        secret: app_credential_cloud_conf
    run: playbooks/my-playbook.yaml
```

Secrets for a job are simply defined by the keyword `secrets`.
Each secret needs a name that can be used in your playbooks.
The property `secret` references the secret that is defined within your project.

**ATTENTION!** If your job is using a secret `job.post-review` is automatically
set to `true`. For untrusted projects, that means that your job is only called
in piplines that have the `pipeline.post-review` flag set to `true`. In SCS context
that means you may run these jobs only with the pipelines `tag` and `post`.

If you want to run jobs on pipelines that have `post-review` set to `false`, which
is default, and your job needs a secret, the secret may be defined in the zuul-config repository.

Example:

```yaml
- secret:
    name: app_credential_cloud_conf
    data:
      credentials: my-secret-value
```

Within `my-playbook.yaml` you can reference the secret value using `"{{ clouds_conf.credentials }}"`.
In this example `my-secret-value` is clear readable text. That is not something we want to keep
secrets. But how do you encrypt secrets in a way that they are secure and also can be decrypted by
Zuul?

For this purpose Zuul creates its own public/private key pair for each project. Everyone may use the
public key to create secrets. But only Zuul will be able to decrypt these values. To avoid the user
to be responsible for the correct encryption there is an zuul-client tool that will do this for you.

Example:

```bash
zuul-client --zuul-url ZUUL_URL  encrypt --tenant TENANT --project ORGANIZATION/PROJECT --infile creds.yaml --outfile clouds.yaml.enc
```

The content may look like this:

```yaml
- secret:
    name: <name>
    data:
      <fieldname>: !encrypted/pkcs1-oaep
        - IGZ2Wu47R9mEY4fjetbxSAUGNaz4HR1mjk9lCLq3HsUMjHGj9YPlb2MvnPQw1LCJSvpaK
          ogth7hi2zYwrs5tNAik/qlVSB7AM+LQRP7lmlM4JmD6WOyR7DisHu7oMD1Gqem2ZuMggA
          DIBn5+DeBIvnwihDOcS+BKPTVMEtXOJNkuObZHE8DweB/RQIGUvjyeq5yoAmz/y+qGVqe
          0Vk4pTYFIBgk5DMzwVnDzDkqs/QokoOupMUoBcpapmM11do4ymjbDpeINjayoro6VXTtX
          Mkk9fDv9wuJIQTuyHAOfMD+UYS/HqVSF/Hm9ScUvfhw02gTdzKCxliWhFHJOj7RbdUUMK
          OYYcUkNp5cXZUYFnflMhxVEnzREbdAIklNPfoHOizsxLPaUZ9yk6XcFRflFfMvqBtUS00
          LCx0Uh906NwdaEUrv2ZdrN123rwfwfw4333232rDFDFfsdfddsfdDFSFSdqrrtwms5Mi0
          szUBaM4j+Mayep+41vl0cpsLU91GzXEATWMaPIN8OnEHF6qQIv0wB6VaKd5aeAyERisb3
          wFdjEo4faLO70RWzR33k+4xqAYNIIFyTMpWJz21CUSfoYG8ygL6t7RJGgyjA+0KsVEyj+
          ewEtiaUOLYyD7pXtqdw1HgzjqiXnfxk+wSv/y5y/TGGYpQj8zU76jS7Zj0ft/0=
```

You may use this content or the file to provide it as a secret. You just have to update the `<name>` and the
`<fieldname>` part.

Official documentation:

1. [Secrets documentation](https://zuul-ci.org/docs/zuul/latest/config/secret.html#secret)
2. [Encryption documentation](https://zuul-ci.org/docs/zuul/latest/project-config.html#encryption)

#### Let's put it all together

For a basic but working example the following content may be written into a `zuul.yaml` file.

```yaml
# zuul.yaml content
---
- secret:
    name: mySecret
    data:
      secretValue: !encrypted/pkcs1-oaep
        - <ENCYPTED_DATA>

- job:
    name: myFirstTestJob
    parent: base
    secrets:
      - name: secretName # The name of the secret that is used within "playbooks/testPlaybook.yaml"
        secret: mySecret
    run: playbooks/testPlaybook.yaml

- project:
    check:
      jobs:
        - myFirstTestJob
```

This will run you job `myFirstTestJob` when ever the `check` pipeline is triggered.
Within SCS this pipeline is always triggered if you open, change or reopen a pull request.
The `check` pipeline can also be triggered manually if you write a comment on an already
existing pull request and place the string `recheck` in it.

The path to you playbook is always the full path within the repository. The playbook
contains the tasks you actually want to run on all or a specific subset of nodes.
Example playbook:

```yaml
# playbooks/testPlaybook.yaml content
---
- hosts: all
  tasks:
    - debug:
        msg: "Debug print my secrets! {{ secretName.secretValue }}" # do not do this as it will expose your secrets
```
