---
title: Requirements for testing cluster-stacks
type: Decision Record
status: Draft
track: KaaS
---

## Introduction

In this proposal, we discuss the necessity and design considerations of a lightweight solution for testing cluster-stacks. The purpose is to address the challenges associated with testing on an Infrastructure as a Service (IaaS) provider and the limitations of using Docker as the primary containerization tool for testing. This proposal will elaborate on why we need to test in a local environment, specifically a laptop, and the benefits and drawbacks associated with it. We aim to make an informed decision for testing cluster stacks to cater to both the organizational and technical perspectives of our stakeholders.

## Motivation

From an organization's point of view, it is crucial to lower the entry barrier for testing. This action will make it possible for anyone, including external contributors, to easily participate in the testing process without needing an account with the IaaS provider. It is also necessary to overcome the hurdles associated with maintaining a balance in the provider account and managing sponsorships to fund the testing.

From a technical standpoint, there are multiple reasons to favor a local environment for testing. Among them is the ability to test without internet, finish tests in a shorter timeframe, and incur no cost. The provider independence of Cluster Stacks makes it nonsensical to test with a specific provider due to the varied behaviors of different providers. There are also challenges in monitoring and debugging tests run on IaaS providers and dealing with their downtime and limitations on concurrent testing.

## Design Considerations

1. **Lightweight Solution**
The testing solution should be lightweight and easy to use in a local environment, such as a laptop. This lightweight solution should minimize dependencies and resource usage while maximizing speed and efficiency of the tests. It should be capable of handling the cluster-stack testing requirements without necessitating a bulky or resource-intensive setup.

2. **Independence from Specific Providers**
The solution should be generalized and not bound to any specific provider. This consideration ensures that the solution can be applied to any provider, guaranteeing its versatility and broad applicability.

3. **Offline Testing**
The testing solution should support testing without internet connection, which will enable more robust and flexible testing scenarios. It should be possible to run the tests even in cases of limited or disrupted internet access.

4. **Fast Execution Time**
The tests should execute within a reasonably short amount of time. The solution must be optimized to ensure quick testing cycles, which can help increase productivity and shorten development cycles.

5. **No-Cost Solution**
The solution should not impose any additional costs on the organization or individual testers. This characteristic is crucial to enable widespread adoption of the testing process and to lower the entry barrier for contributors.

6. **Easy Monitoring and Debugging**
The solution should provide easy monitoring and debugging capabilities. It should allow developers to quickly identify, diagnose, and fix issues that arise during testing, without requiring access to any external logs or monitoring tools.

7. **Concurrent Testing**
The solution should support the ability to run concurrent tests without causing any disruption or downtime. This ability can improve the efficiency and speed of the testing process.

## Required Features

The proposed solution should meet the following feature requirements:

1. Local Environment: The solution should support a local testing environment that allows developers to test cluster stacks on their local machines, reducing dependencies on external providers.
1. Compatibility: The solution should be compatible with various operating systems and platforms, ensuring its usability across diverse environments.
1. Performance: The solution should offer high-performance testing capabilities, allowing fast execution of tests.
1. Offline Support: The solution should allow testing in offline mode, ensuring tests can be performed even without an internet connection.
1. Concurrency: The solution should support running multiple tests concurrently without causing disruptions or conflicts.
1. Monitoring & Debugging: The solution should provide easy-to-use tools for monitoring test progress and debugging issues.
1. Cost-effectiveness: The solution should not require any financial investment from the testers or the organization, promoting broad accessibility and usage.

## Pros and Cons of Different Approaches

Two potential approaches for testing cluster stacks are the use of an IaaS provider and the use of a local environment. Here we discuss the pros and cons of these two approaches.

### IaaS Provider (OpenStack, Hetzner, AWS)

#### Pros

- Comprehensive testing environment with advanced capabilities.
- Possibility to mimic real-world production environments closely.

#### Cons

- Requires signing up and account management, which can be a barrier for some testers.
- Requires maintaining a balance in the provider account, which can pose financial burdens.
- Internet dependency for testing.
- Potential for prolonged testing time due to various dependencies.
- Challenges with monitoring and debugging.
- Potential downtime and difficulty in running concurrent tests.

### Local Environment (Docker, KubeVirt)

#### Pros

- Faster test execution with no downtime.
- Ability to test without internet.
- Independent of any provider knowledge.
- Cost-free testing.
- Easier integration into CI/CD.
- Simplified monitoring and debugging.

#### Cons

- Limited systemd support and containerd support for kubeadm in Docker.
- Inability to mimic the exact real-world production environments.

## Beyond Docker: Virtual Machine based Approach

While Docker provides significant benefits for local environment testing, it's important to recognize its limitations. Docker containers, by design, are lightweight and don't contain a full operating system which can lead to challenges when trying to mimic real-world production environments. Also, Docker containers lack some necessary features like systemd which is used in many production environments for initializing and managing services.

One major aspect that Docker lacks is the ability to mimic real-world production environments effectively. This is primarily due to its nature as a containerization tool, operating within the host OS, and sharing resources among its containers. This might create disparities in behavior when comparing to deployments on real, isolated systems, which could be problematic in some scenarios.

Furthermore, Docker utilizes a Union File System for its images, leading to the creation of layers. This approach can lead to some complexities when dealing with node-images which comprise a significant chunk of our layers. Handling such situations might require workarounds that could add additional complexity and potential points of failure. This creates a blind spot, as real providers won't require these workarounds, which might lead to disparities in results when comparing testing in local and actual production environments.

Therefore, to achieve a more accurate representation of real-world environments, we propose a solution that utilizes a virtual machine based approach for local testing. This approach could leverage tools like KubeVirt, Vagrant, or VirtualBox to create and manage virtual machines on the local environment. This strategy would provide a more robust and realistic environment for testing, as it can better emulate the behavior of a full-fledged operating system and thereby more closely mimic a real-world production environment.

### Virtual Machine Based Approach

#### Pros

- Provides a more accurate representation of real-world production environments.
- Allows for full operating system emulation, including features like systemd.
- Can create isolated environments, thereby mimicking actual deployments better than containers.

#### Cons

- Potentially more resource-intensive than container-based solutions.
- Increased complexity due to the need for managing full virtual machines rather than lightweight containers.
- Initial setup might be more complicated compared to a Docker-based solution.

## Proposed Path Forward

Given the limitations of Docker and the potential advantages of a virtual machine based approach, we propose to investigate further into this strategy. The exact tool or set of tools used can be determined based on a thorough evaluation of the available options.

Although there might be some initial complexity and potentially higher resource usage compared to Docker, we believe that the benefits of more accurate testing and better emulation of real-world environments outweigh these potential disadvantages.

The proposed solution should meet all the requirements mentioned in the previous sections of the proposal, in addition to providing the benefits of a virtual machine based approach. By doing so, we aim to establish a robust, reliable, and realistic testing environment for cluster stacks that mimics real-world production environments as closely as possible.

## Conclusion

After thoroughly examining the organizational needs, technical requirements, and potential testing approaches, it is evident that testing cluster stacks in a local environment provides significant advantages over using an Infrastructure as a Service (IaaS) provider. A local environment minimizes financial constraints, reduces testing time, offers offline capabilities, and enables greater tester participation without the need for specialized IaaS knowledge.

While Docker stands out for its broad adoption, cost-effectiveness, and impressive containerization benefits, it also presents some limitations that cannot be overlooked. The lack of full operating system emulation and certain system features like systemd pose challenges to mimic real-world production environments accurately.

Given Docker's limitations and the need to reproduce realistic testing scenarios, we propose moving beyond Docker to a virtual machine-based approach. Even though this approach may introduce initial complexity and potentially higher resource usage, it promises a more accurate representation of real-world environments, thereby ensuring more reliable and robust test results.

Tools such as KubeVirt, Vagrant, or VirtualBox could potentially fulfill our requirements, offering benefits such as full operating system emulation and isolated environments. However, an in-depth evaluation of these and possibly other tools is necessary to determine the best path forward.

In conclusion, our goal is to design a robust, reliable, and realistic testing environment for cluster stacks that closely mimics real-world production environments, aligns with our organizational and technical perspectives, and ensures a low entry barrier for all testers. Embracing a virtual machine-based approach for local environment testing represents a promising strategy to achieve this objective, paving the way for more efficient and reliable cluster stack testing.
