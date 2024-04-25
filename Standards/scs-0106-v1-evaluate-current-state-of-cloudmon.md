---
title: Evaluate current state of CloudMon
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

## Decision

By opting for [Gherkin](https://cucumber.io/docs/gherkin/) test scenarios with Python mapping API calls to OpenStack,
we aim to address the complexities and shortcomings of the Cloudmon project while ensuring our monitoring and testing
processes remain efficient, reliable, and aligned with our organizational goals. To connect both technologies we use as
well [Behave](https://behave.readthedocs.io/en/latest/) framework. This decision represents a strategic move towards
enhancing our cloud infrastructure management capabilities and maximizing operational effectiveness.
