package scs_k8s_tests

import (
	"context"
	"fmt"
	"log"
	"os"
	"strings"
	"testing"

	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

// list of common harbor components.
var HarborComponentNames = []string{
	"harbor-core",
	"harbor-db",
	"harbor-jobservice",
	"harbor-portal",
	"harbor-registry",
	"nginx",
}

// other registries
var OtherRegistries = []string{
	"docker-registry",
	"quay",
	"jfrog",
	"artifacthub",
	"dragonfly",
	"keppel",
	"nexus",
	"kraken",
}

func Test_scs_0212_registry_standard_test(t *testing.T) {
	// set up the kubernetes client
	config, err := rest.InClusterConfig()
	if err != nil {
		log.Fatalf("Failed to create rest config: %v", err)
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		log.Fatalf("Failed to create Kubernetes client: %v", err)
	}

	harborComponentsFound := make(map[string]bool)
	otherRegistryFound := false

	fmt.Println("Checking for Harbor components in Deployments...")
	otherRegistryFound = checkHarborDeployments(clientset, harborComponentsFound) || otherRegistryFound

	fmt.Println("Checking for Harbor components in Services...")
	otherRegistryFound = checkHarborServices(clientset, harborComponentsFound) || otherRegistryFound

	if otherRegistryFound {
		log.Fatalf("Non-Harbor registry detected in the cluster. Failing test.")
	}

	// ensure all harbor components are found
	for _, component := range HarborComponentNames {
		if !harborComponentsFound[component] {
			fmt.Printf("Harbor component missing: %s\n", component)
			log.Fatalf("Harbor registry not fully deployed. Failing test.")
		}
	}

	fmt.Println("All Harbor components are deployed, and no other registries are found. Test passed.")
	os.Exit(0)
}


// checkHarborDeployments checks if required harbor components are present in deployments
// and ensures no other registries are found.
func checkHarborDeployments(clientset *kubernetes.Clientset, harborComponentsFound map[string]bool) bool {
	otherRegistryFound := false
	deployments, err := clientset.AppsV1().Deployments("").List(context.TODO(), v1.ListOptions{})
	if err != nil {
		log.Fatalf("Failed to list deployments: %v", err)
	}

	for _, deployment := range deployments.Items {
		// check for Harbor components
		for _, component := range HarborComponentNames {
			if strings.Contains(deployment.Name, component) {
				harborComponentsFound[component] = true
				fmt.Printf("Found Harbor deployment: %s in namespace: %s\n", deployment.Name, deployment.Namespace)
			}
		}

		// check for other registries
		for _, registry := range OtherRegistries {
			if strings.Contains(deployment.Name, registry) {
				otherRegistryFound = true
				fmt.Printf("Found non-Harbor registry deployment: %s in namespace: %s\n", deployment.Name, deployment.Namespace)
			}
		}
	}

	return otherRegistryFound
}

// checks if required harbor components are present in services
// and ensures no other registries are found.
func checkHarborServices(clientset *kubernetes.Clientset, harborComponentsFound map[string]bool) bool {
	otherRegistryFound := false
	services, err := clientset.CoreV1().Services("").List(context.TODO(), v1.ListOptions{})
	if err != nil {
		log.Fatalf("Failed to list services: %v", err)
	}

	for _, service := range services.Items {
		// check for harbor components
		for _, component := range HarborComponentNames {
			if strings.Contains(service.Name, component) {
				harborComponentsFound[component] = true
				fmt.Printf("Found Harbor service: %s in namespace: %s\n", service.Name, service.Namespace)
			}
		}

		// check for other registries
		for _, registry := range OtherRegistries {
			if strings.Contains(service.Name, registry) {
				otherRegistryFound = true
				fmt.Printf("Found non-Harbor registry service: %s in namespace: %s\n", service.Name, service.Namespace)
			}
		}
	}

	return otherRegistryFound
}
