# Collaboration

## Collaborating with issues and pull requests

We use the GitHub flow to track and discuss changes in issues, then propose and
review changes in pull requests. See the
[GitHub documentation](https://docs.github.com/en/free-pro-team@latest/github/collaborating-with-issues-and-pull-requests)
for more details.

## Meetings

### Project updates

- Weekly with all teams on Thursday at 1505 CEST (45 mins)

### Sprint review/Backlog refinement/Sprint planning meetings

- Weekly with Team IaaS on Wednesdays at 1005 CEST (1 hour)
- Weekly with Team Container on Mondays at 1005 CEST (1 hour)
- Weekly with Team OPS & IAM on Thursdays at 1005 CEST (1 hour)

### Special interest groups (SIGs)

- Identity & Access Management (IAM): Bi-Weekly on Friday at 1005 CEST (1 hour)
- Monitoring & Logging: Weekly on Friday at 1205 CEST (1 hour)

## Videoconference

We use a self-hosted [Jitsi Meet](https://jitsi.org) instance for video conferencing.

The server uses an automated deployment based on the
[heat-docker-jitsi-meet](https://github.com/garloff/heat-docker-jitsi-meet) project.

Configuration is such everyone who knows the room can connect, unless the moderator
sets a password/PIN. Opening a new room requires authentication. (Contact Kurt if
you need a password.)

### Usage

Connect with a desktop browser (Chrome/Chromium or other blink based browser
recommended due to superior WebRTC implementation with SimulCast/SVC for VP8/VP9 --
Safari & Firefox work, but cause higher data traffic). For mobile devices use
the Jitsi Meet App.

Use the little arrows in the control bar at the bottom to select speaker, microphone
and camera in case you lack audio/video. Occasionally, you can not hear all but
one participant; in this case reconnecting typically helps.

We have an asterisk connected to some conference rooms to provide dial-in capabilities
for folks that lack internet connectivity (but have a working phone connection).

## Nextcloud

We have a [Nextcloud](https://nextcloud.com)
[instance](https://scs.sovereignit.de) for sharing files, calendar, contacts, ...
setup for things that are not public.

We are also using it for our taskboards currently, though we are looking at
options to do this in the open.

If you want to contribute, we'll do an onboarding call and add you to nextcloud.
This will also add you to the `scs-member@lists.scs.community` mailing list.

We have an announcements mailing list there `announce@lists.scs.community` and you
can subscribe via the [mailman3 frontend](https://scs.sovereignit.de/mailman3/postorius/lists/)

## Zuul CI/CD pipelines and project gating

Since we are expecting a lot of pipelines beeing created and used GitHub actions won't keep up
well. We also expect cross-repository and even cross-project dependencies. Therefore we decided to
use Zuul as our main pipeline solution.

### How to make a repo use Zuul

- Make Zuul aware of your repository in this [repo](https://github.com/SovereignCloudStack/zuul_deployment)
- Create a file *.zuul.yaml*
  - An example can be found [here](https://github.com/SovereignCloudStack/zuul-sandbox/blob/main/.zuul.yaml)
  - You can have a job section containing *self-defined* jobs which you need to write on your own
  - You have to have a project section containing
    - the default-branch name
    - the merge-mode which should be used to auto-merge
    - the jobs to run in each pipeline (gh_check, gh_gate, gh_post, gh_tag)
    - these pipelines are triggered by events which can be looked up [here](https://github.com/SovereignCloudStack/zuul_config/blob/main/zuul.d/gh_pipelines.yaml)
    - some default jobs can be found [here](https://opendev.org/zuul/zuul-jobs/src/branch/master/playbooks)
- If you have *self-defined* jobs, you need to create a folder *.playbooks*
  - this folder containers ansible playbooks which will be triggered

### General information about Zuul

Zuul does not take anything for granted. If you need to have something installed,
you should install it via ansible. Our test-machines are basically pimped
docker-containers, so we might run into issues some time. But for now, things work pretty good.
