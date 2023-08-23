---
title: ADR - Reading yaml and applying objects to Kubernetes using Golang
type: ADR
status: Draft
track: KaaS
---

# ADR - Reading yaml and applying objects to Kubernetes using Golang

## Overview

There are two steps that we have to follow in order to 1. read from a yaml file and 2. apply Kubernetes objects to the API. Both of these steps can be done in very different ways and there are many options to configure clients and to slightly alter the behavior of the code.

The two main strategies to approach both steps are 

a) doing everything in a generic way that can handle arbitrary CRDs, or

b) doing the steps in a way that they can be done only for specific CRDs.

The most common approach is b) and it is not too easy to find examples of option a) at all. One could easily think that there is no fully generic way for this task. However, after some trial and error as well as learning more about the different libraries that Kubernetes provides and uses, we found an approach that is actually generic and solves our purpose.

## Background

In the cluster stacks, we have two Helm charts with objects that we have to apply. As cluster stacks are a general concept, we don’t know a priori the objects that might be in there. It would not be good if there was any coupling between the generic cluster-stack-operator code and the individual cluster stacks, which might be implemented for any provider and with any content, e.g. with arbitrary and probably provider-specific cluster addons. 

In the code, the operator has to template the objects, read the yaml configuration of Kubernetes objects and apply these objects. 

This ADR is about defining the optimal way of tackling this problem. 

## Reading from yaml files and storing the information

There are two ways of reading data, as mentioned before. The generic approach uses the unstructured library (https://pkg.go.dev/k8s.io/apimachinery/pkg/apis/meta/v1/unstructured), where we have a generic type `unstructured.Unstructured` which solves our purpose. 

In the following, we describe the two approaches as well as their advantages which can be taken in order to read from yaml (here as `[]byte`).

### Unstructured vs structured objects

#### Unstructured Approach:

`unstructured.Unstructured` and `unstructured.UnstructuredList` are types provided by Kubernetes' `client-go` library. These types are used to represent and operate on generic Kubernetes resources without knowing the exact Go type ahead of time.

**Advantages:**

1. **Flexibility**: You can handle any Kubernetes resource without having to predefine its structure or having its Go struct type available. This is useful for tools or applications that need to process a diverse range of resources.
2. **Version Agnosticism**: With the unstructured approach, you're not tied to a specific version of the Kubernetes API or any Custom Resource Definitions (CRDs). If the schema changes, your code can still handle it.
3. **Generic Handling**: If you're building a tool or system that needs to interact with unknown or dynamic resources (e.g., a Kubernetes dashboard or a generic controller), using `unstructured` makes the task feasible.

##### **Code Examples:**

Decoding yaml:

```go
import (
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"sigs.k8s.io/yaml"
)

func DecodeYAMLToUnstructured(data []byte) (*unstructured.Unstructured, error) {
	obj := &unstructured.Unstructured{}
	jsonData, err := yaml.YAMLToJSON(data)
	if err != nil {
		return nil, err
	}
	if err := obj.UnmarshalJSON(jsonData); err != nil {
		return nil, err
	}
	return obj, nil
}

```

Extracting data from an unstructured object:

```go
for _, cr := range customResources.Items {
	name := cr.GetName()
	spec, exists, _ := unstructured.NestedMap(cr.Object, "spec")
	if exists {
		fmt.Printf("Resource Name: %s, Spec: %v\\n", name, spec)
	}
}

```

In the above example, we use `unstructured.NestedMap` to extract the "spec" field from the custom resource. There are various other helper functions (`unstructured.NestedString`, `unstructured.NestedInt64`, etc.) to fetch nested fields of different types.

#### Structured Approach:

Using specific Go structs to represent Kubernetes resources is the structured approach. These types are auto-generated from the Kubernetes API definition.

**Advantages:**

1. **Type Safety**: Your code gets compile-time checks. This can prevent many runtime errors that might arise from the use of a wrong field name or a wrong type.
2. Auto-completion **& Documentation**: Modern IDEs can provide auto-completions and inline documentation when using strongly typed objects, which is immensely beneficial for development.
3. **Explicitness**: Your code is more explicit about which resources and versions it can handle. It's clear from the types which parts of the Kubernetes API you're using.

##### **Code Example:**

```go
import (
	"k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/serializer"
	"k8s.io/client-go/kubernetes/scheme"
)

func DecodeYAMLToPod(data []byte) (*v1.Pod, error) {
	decoder := serializer.NewCodecFactory(scheme.Scheme).UniversalDeserializer()
	obj, _, err := decoder.Decode(data, nil, nil)
	if err != nil {
		return nil, err
	}

	pod, ok := obj.(*v1.Pod)
	if !ok {
		return nil, fmt.Errorf("provided YAML was not a Pod")
	}
	return pod, nil
}

```

#### Summary:

1. **Unstructured**: Use when you want flexibility and a generic way to handle any Kubernetes resource without predefining its Go type.
2. **Structured**: Use when you know the exact resources you'll be dealing with, and you want the benefits of type-safety, auto-completions, and more explicit code.

Coming back to our specific problem: in terms of using them with the Kubernetes API, an unstructured approach allows us to read yaml in a very dynamic way, without needing to know the exact resources in advance. 

On the other hand, even though a structured approach would be more robust and would give us better error checking, it would make it necessary to know the CRDs in advance. Therefore, it would require coupling between the cluster stacks that the SCS community defines as well as the operator.

### Generic vs. specific schemes

In Kubernetes and its client libraries for Go, a `Scheme` (https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/scheme, https://pkg.go.dev/k8s.io/apimachinery/pkg/runtime#Scheme) plays a crucial role in serialization and deserialization of API objects. It's deeply tied to the intricacies of how Kubernetes represents and manipulates resources.

#### Scheme in Kubernetes and Go:

1. **What is it?**: A `Scheme` in Kubernetes is an object that knows about the Go types (like `Pod`, `Service`, etc.) that correspond to Kubernetes API resources. It maintains a mapping between Go types, GroupVersionKinds, and interfaces for converting between different versions of the same object.
2. **Role**: Whenever Kubernetes or a client interacts with API resources, the objects are serialized to or deserialized from a wire format (typically JSON). This conversion requires knowledge about what Go struct to populate for a given API resource kind and version, and that's where the `Scheme` comes into play. With the help of functions like AddToScheme (https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/scheme#Builder.AddToScheme), certain CRDs can be added to a specific scheme that will thus contain this specific piece of knowledge.

#### Advantages of `unstructured.UnstructuredJSONScheme`:

`unstructured.UnstructuredJSONScheme` is a special kind of scheme that can decode any JSON or YAML into a map-based object (`unstructured.Unstructured`).

1. **Generality**: It doesn't require prior knowledge of the specific API types. This is particularly useful when working with unknown or dynamic resources such as CRDs in a generic tool.
2. **Simplicity**: You don't need to register types beforehand. This can simplify the setup and initialization code, especially when the exact set of resource types isn't known in advance.
3. **Dynamic Operations**: Since everything is a map, you can explore or manipulate the data without needing to define specific structs.

#### Advantages of Defining Specific Schemes for CRDs:

1. **Type Safety**: By working with strong Go types, you benefit from compile-time checks, better auto-completion, and generally safer code. This can lead to fewer runtime errors.
2. **Clarity**: Handling objects with their concrete types can lead to more readable and self-documenting code. Someone reading the code can immediately understand which Kubernetes resources are being managed.
3. **Rich Features**: With a defined Scheme, you can use more advanced Kubernetes client features like defaulting, conversion between versions, deep copy, and more.
4. **Performance**: Working with static Go types might be more efficient than dynamic map-based operations, especially for frequently-accessed resources.

#### Summary:

The choice between `unstructured.UnstructuredJSONScheme` and defining specific schemes for CRDs boils down to the requirements and nature of the application:

- **Use `unstructured.UnstructuredJSONScheme`** when you are building tools that should operate on a dynamic or unknown set of Kubernetes resources. It's perfect for generic tools, controllers that need to handle arbitrary CRDs, or when introspecting resources.
- **Define Specific Schemes for CRDs** when you know the exact set of resources your application will interact with and you want the advantages of type-safety, clarity, and potential performance benefits. This approach is commonly seen in controllers and operators tailored for specific tasks or CRDs.

## Applying generic objects to Kubernetes

In the following, we will explain when to use the static versus the dynamic Kubernetes Go client, as well as their advantages and disadvantages, especially in the context of the `unstructured.Unstructured` object in the dynamic case.

### Static Client:

**When to use**:

1. **Well-Defined Resources**: When working with core Kubernetes resources like Pods, Services, Deployments, etc., whose structures are known during compile time.
2. **Type Safety**: When you prefer strong type guarantees in your code, which can catch errors during compile-time.
3. **Clear API Versioning**: When working with specific versions of the Kubernetes API and you want your code to be explicit about the versions.

**Advantages**:

1. **Type Safety**: Helps catch errors during compile time rather than runtime.
2. **Intuitive and Strongly-typed API**: It offers an intuitive interface with Go types for each resource.
3. **Autocompletion**: IDEs can provide autocompletion due to static types.

**Disadvantages**:

1. **Less Flexibility**: Any change in resource schema or introduction of new custom resources requires code changes.
2. **More Dependencies**: Might require multiple versions or importing a lot of client-go libraries to support various types.
3. **Tight Coupling**: It is coupled to specific API versions, so any change in the Kubernetes API or introduction of new resources might need code adjustments.

#### Code example:

Using a static client to get a list of Pods:

```go
package main

import (
	"context"
	"fmt"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

func main() {
	kubeconfig := "/path/to/kubeconfig"
	config, _ := clientcmd.BuildConfigFromFlags("", kubeconfig)

	clientset, _ := kubernetes.NewForConfig(config)
	pods, _ := clientset.CoreV1().Pods("default").List(context.TODO(), metav1.ListOptions{})

	for _, pod := range pods.Items {
		fmt.Println(pod.Name)
	}
}
```

### Dynamic Client:

**When to use**:

1. **Custom Resources or CRDs**: Especially useful when the Go type may not be known or available during compile time.
2. **Generic Operations**: For operations that need to be performed on multiple kinds of resources, especially in tools designed to work across various Kubernetes resources.
3. **Version Agnostic Operations**: When you want operations to work regardless of the specific API version.

**Advantages**:

1. **Flexibility**: Can interact with any Kubernetes resource without needing its Go type definition, including custom resources.
2. **Version Independence**: Can potentially reduce tight coupling between your application and specific Kubernetes API versions.
3. **Reduces Dependencies**: Don’t need to import client libraries for each kind of resource.

**Disadvantages**:

1. **Lack of Type Safety**: Mistakes with resource structures might only be caught at runtime.
2. **Verbose API Interaction**: Operations can be more verbose because you need to specify the Group, Version, and Resource for every operation.
3. **Reliance on `unstructured.Unstructured`**: The returned objects are of type `unstructured.Unstructured`, which might be less intuitive to work with compared to strongly typed objects.
    
    ### Code example
    
    Using a dynamic client to get a list of custom resources:
    
    ```go
    package main
    
    import (
    	"context"
    	"fmt"
    	"k8s.io/apimachinery/pkg/runtime/schema"
    	"k8s.io/client-go/dynamic"
    	"k8s.io/client-go/tools/clientcmd"
    	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    )
    
    func main() {
    	kubeconfig := "/path/to/kubeconfig"
    	config, _ := clientcmd.BuildConfigFromFlags("", kubeconfig)
    
    	dynamicClient, _ := dynamic.NewForConfig(config)
    	gvr := schema.GroupVersionResource{
    		Group:    "customgroup.k8s.io",
    		Version:  "v1",
    		Resource: "customresources",
    	}
    	customResources, _ := dynamicClient.Resource(gvr).Namespace("default").List(context.TODO(), metav1.ListOptions{})
    
    	for _, cr := range customResources.Items {
    		fmt.Println(cr.GetName())
    	}
    }
    
    ```
    

#### Summary:

In summary, if you're dealing with well-known, core Kubernetes resources and prioritize type safety and explicit versioning, the static client is suitable. On the other hand, if you want flexibility, particularly when dealing with a wide array of resources or custom resources, and you are okay with sacrificing some type safety, the dynamic client becomes more appealing.

## Conclusion

In both cases of reading yaml code and in applying objects to Kubernetes, there are generic and non-generic ways. We have discussed the advantages and disadvantages of both ways. It is clear that we should go with the generic approaches, as they decouple the cluster-stack-operator from the cluster stacks. 

Therefore, we decided to use the `unstructured.Unstructured` objects, read them with the `unstructured.UnstructuredJSONScheme` and use the dynamic client to deal with the Kubernetes API.