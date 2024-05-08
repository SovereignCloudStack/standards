---
title: Evaluating the deployment of CloudMon in SCS infrastructure
type: Decision Record
---

## Introduction

In the fast-paced environment of modern cloud computing, ensuring the reliability and performance
of cloud infrastructure is paramount for organizations. Effective monitoring and testing framework
are essential tools in this endeavor, enabling proactive identification and resolution of issues before
they impact critical operations. However, selecting the right monitoring solution can be a daunting task,
particularly when faced with options that are overly complex and lack essential documentation and working
scenarios.

## Motivation

One such solution, the [Cloudmon](https://stackmon.org/) project, presents challenges that may hinder its
suitability for organizations seeking efficient and reliable monitoring capabilities. This introduction
outlines the reasons why our organization opts against utilizing the Cloudmon project and instead embraces
a more streamlined and effective approach involving Gherkin test scenarios and mapping Python API calls to
interact with OpenStack resources. By addressing the complexities and shortcomings of the Cloudmon project,
SCS organization aims to adopt a monitoring solution that not only meets but exceeds our requirements for
simplicity, reliability, and ease of use.

## Design Considerations

Our approach was to base on a technical concept. This document serves as a proposal, with the final decision
subject to discussion with SCS team members. We propose a behavior-driven system based on solutions using Java framework
Cucumber, utilizing the Gherkin domain-specific language for defining executable specifications. This approach ensures
clear, human-readable test behavior definitions, facilitating participation from both developers and non-technical
contributors. Considering the team's proficiency in Python, the language's simplicity and clarity, alignment with
OpenStack's ecosystem, and the robust support from the Python community, it's evident that Python presents a superior
choice for implementing Gherkin-based testing over Java. By harnessing Python's strengths, we can maximize efficiency,
accelerate development, and ensure seamless integration with OpenStack, ultimately enhancing the effectiveness of our
testing processes.

## Challanges

During our assessment of the Cloudmon/Stackmon project, we encountered significant challenges related to documentation,
particularly regarding lack of examples for configuration setups and usage guidelines. The lack of comprehensive
documentation impeded our understanding of the project and hindered effective utilization. We understood that some
features implemented in the cloudmon/stackmon are not neccessary for the health monitor like running the tests from
different virtual locations because every network in the project is responsible for different AZ and on the other hand
with our tests approach we can just clone [shs-health-monitor](https://github.com/SovereignCloudStack/scs-health-monitor/tree/main)
to another physical location and run the same tests from physically different place on earth. Examples like that
confirmed our belief that atomic approach save us a lot of effort, time and costs.

## Decision

By opting for [Gherkin](https://cucumber.io/docs/gherkin/) test scenarios with Python mapping API calls to OpenStack,
we aim to address the complexities and shortcomings of the Cloudmon project while ensuring our monitoring and testing
processes remain efficient, reliable, and aligned with our organizational goals. To connect both technologies we use as
well [Behave](https://behave.readthedocs.io/en/latest/) framework. This decision represents a strategic move towards
enhancing our cloud infrastructure management capabilities and maximizing operational effectiveness.
