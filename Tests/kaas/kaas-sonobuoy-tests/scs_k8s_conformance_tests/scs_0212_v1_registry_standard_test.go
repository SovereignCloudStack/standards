package scs_k8s_tests

import (
	"context"
	"fmt"
	"log"
	"os"
	"testing"

	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

// list of common Harbor components.
var HarborComponentNames = []string{
	"harbor-core",
	"harbor-db",
	"harbor-jobservice",
	"harbor-portal",
	"harbor-registry",
	"nginx",
}

func Test_scs_0212_registry_standard_test(t *testing.T) {
	// Set up the Kubernetes client
	config, err := rest.InClusterConfig()
	// config, err := clientcmd.BuildConfigFromFlags("", filepath.Join(homeDir(), ".kube", "config"))
	if err != nil {
		log.Fatalf("Failed to create rest config: %v", err)
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		log.Fatalf("Failed to create Kubernetes client: %v", err)
	}

	fmt.Println("Checking for Harbor components in Deployments...")
	if err := checkDeployments(clientset); err != nil {
		log.Fatalf("Error checking deployments: %v", err)
	}

	fmt.Println("Checking for Harbor components in Services...")
	if err := checkServices(clientset); err != nil {
		log.Fatalf("Error checking services: %v", err)
	}

	fmt.Println("Harbor check completed.")
}

// check deployments for the registry
func checkDeployments(clientset *kubernetes.Clientset) error {
	deployments, err := clientset.AppsV1().Deployments("").List(context.TODO(), v1.ListOptions{})
	harborDeployments := 0
	if err != nil {
		return fmt.Errorf("failed to list deployments: %v", err)
	}

	for _, deployment := range deployments.Items {
		for _, componentName := range HarborComponentNames {
			if containsString(deployment.Name, componentName) {
				fmt.Printf("Found Harbor deployment: %s in namespace: %s\n", deployment.Name, deployment.Namespace)
				harborDeployments++
			}
		}
	}
	if harborDeployments > 0 {
		fmt.Printf("Harbor deployments found\n")
	} else {
		fmt.Printf("Harbor was not found in deployments\n")
	}
	return nil
}

// check services for the registry components
func checkServices(clientset *kubernetes.Clientset) error {
	services, err := clientset.CoreV1().Services("").List(context.TODO(), v1.ListOptions{})
	harborServices := 0
	if err != nil {
		return fmt.Errorf("failed to list services: %v", err)
	}

	for _, service := range services.Items {
		for _, componentName := range HarborComponentNames {
			if containsString(service.Name, componentName) {
				fmt.Printf("Found Harbor service: %s in namespace: %s\n", service.Name, service.Namespace)
				harborServices++
			}
		}
	}
	if harborServices > 0 {
		fmt.Printf("Harbor services found\n")
	} else {
		fmt.Printf("Harbor was not found services\n")
	}
	return nil
}

// containsString checks if a string is contained in another string (case-insensitive).
func containsString(str, substr string) bool {
	return len(str) > 0 && len(substr) > 0 && (str == substr || (len(str) > len(substr) && str[:len(substr)] == substr))
}

func homeDir() string {
	if h := os.Getenv("HOME"); h != "" {
		println(h)
		return h
	}
	return ""
}
