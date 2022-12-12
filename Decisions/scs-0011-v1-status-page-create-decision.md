---
title: Status Page create decision
type: Decision Record
status: Draft
track: IaaS
enhances: status-page-comparison.md
---

# Introduction

Creating and maintaining IaaS is a complex task. Operators can
be supported by presenting the status of all possible parts of the
serving infrastructure. Whether a service is not reachable or
the used hardware is having an outage we want operators to be easily informed
by using a "Status Page" application. The need for a "Status Page"
came up early in Team OPS and the requirements a "Status Page" application 
has to fulfill were defined and written down on 2022-06-02 [see](https://github.com/SovereignCloudStack/issues/issues/123).
The upcoming research on existing solutions came to the conclusion that we want to
create a new "Status Page" application.

# Existing Applications

Since we want to use as much as possible from existing projects and contribute to
upstream projects to support the community with our efforts, it was a hard
decision to create a new "Status Page" application.

Before the decision was made some existing and known applications were tested
and analyzed if they would fit to our use case. An overview of this
comparsion can be found [here](https://github.com/SovereignCloudStack/Docs/blob/main/Decisions/status-page-comparison.md)
This is most likely not a complete list of all existing applications but it
was used as a basis to decide whether to create a new application, that
will indeed consume development resources, or to contribute to another project.

As you may notice the list contains projects that do not fit in a meaningful manner
and potential candidates we could contribute to. But in these cases where
contribution seems possible the candidates looked abandoned
and long existing CVEs weren't worked on.

# Decision

Based on the results the decision was made, that the effort is likely to be the same if
we pick up an existing project and try to get it in shape for our use case. It was not
100% clear if this would even be possible or if we still would have to maintain our
own additional patches.

So there will be a reference implementation that will match the requirements we have.
In addition there will be an architecture design documentation. So if the reference
implementation may not fit to you, it will be possible to create your own application.

# Related Documents

[Requirement discussion results](https://github.com/SovereignCloudStack/issues/files/8822531/20220602-status-page-scs-session.pdf)
[Status Page comparison](https://github.com/SovereignCloudStack/Docs/blob/main/Decisions/status-page-comparison.md)
[Architecture design documentation](https://github.com/joshmue/scs-docs/tree/statuspage-design/Design-Docs/statuspage)

# Conformance Tests

TODO: Conformance Tests for ADRs?