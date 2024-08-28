package scs_k8s_tests

import (
	"context"
	"fmt"
	"log"
	"os"
	"strconv"
	"sync"
	"testing"
	"time"

	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

// getClusterSize estimates the cluster size by counting the number of nodes.
func getClusterSize(clientset *kubernetes.Clientset) int {
	nodes, err := clientset.CoreV1().Nodes().List(context.TODO(), v1.ListOptions{})
	if err != nil {
		log.Fatalf("Failed to list nodes: %v", err)
	}
	return len(nodes.Items)
}

// runConcurrentRequests sends concurrent API requests and returns the number of errors encountered.
func runConcurrentRequests(clientset *kubernetes.Clientset, maxRequestsInflight int) int {
	var wg sync.WaitGroup
	errChan := make(chan error, maxRequestsInflight)

	for i := 0; i < maxRequestsInflight; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			ctx, cancel := context.WithTimeout(context.TODO(), 2*time.Second)
			defer cancel()
			_, err := clientset.CoreV1().Pods("").List(ctx, v1.ListOptions{})
			if err != nil {
				errChan <- err
			}
		}()
	}

	wg.Wait()
	close(errChan)
	return len(errChan) // Return the number of errors encountered
}

// testPositiveCase handles the positive scenario where requests should succeed.
func testPositiveCase(t *testing.T, clientset *kubernetes.Clientset, maxRequestsInflight int) {
	fmt.Println("Running Positive Test Case")
	// Reduce the load even further for the positive test (e.g., 25% of maxRequestsInflight)
	safeRequests := maxRequestsInflight / 4
	errors := runConcurrentRequests(clientset, safeRequests)
	if errors > 0 {
		t.Errorf("Test failed: encountered %d unexpected errors when requests were expected to succeed.", errors)
	} else {
		fmt.Println("Positive test case passed successfully!")
	}
}

// testNegativeCase handles the negative scenario where requests should be throttled.
func testNegativeCase(t *testing.T, clientset *kubernetes.Clientset, maxRequestsInflight int) {
	fmt.Println("Running Negative Test Case")
	// Increase the load significantly above the maxRequestsInflight to trigger rate limiting
	overloadRequests := maxRequestsInflight * 2
	errors := runConcurrentRequests(clientset, overloadRequests)

	// Expect at least some errors due to rate limiting
	if errors == 0 {
		t.Errorf("Test failed: expected rate limit errors, but all requests succeeded.")
	} else {
		fmt.Println("Negative test case passed as expected: rate limit exceeded.")
	}
}

// Test_scs_maxRequestInflight is the main entry point that runs both positive and negative test cases.
func Test_scs_0215_maxRequestInflight(t *testing.T) {
	// Load in-cluster configuration
	config, err := rest.InClusterConfig()
	if err != nil {
		log.Fatalf("Failed to load in-cluster config: %v", err)
	}
	
	// Adjust client rate limits
	config.QPS = 50    // Queries Per Second
	config.Burst = 100 // Allowed burst (concurrent requests above QPS)
	
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		log.Fatalf("Failed to create Kubernetes client: %v", err)
	}
	

	// Get cluster size (number of nodes)
	clusterSize := getClusterSize(clientset)
	fmt.Printf("Detected cluster size: %d nodes\n", clusterSize)

	// Determine maxRequestsInflight based on cluster size and environment variable
	maxRequestsInflightStr := os.Getenv("MAX_REQUESTS_INFLIGHT")
	maxRequestsInflight, err := strconv.Atoi(maxRequestsInflightStr)
	if err != nil || maxRequestsInflight <= 0 {
		maxRequestsInflight = clusterSize * 250 // Example scaling logic: 100 requests per node
	}

	fmt.Printf("Using maxRequestsInflight = %d\n", maxRequestsInflight)

	// Run the positive test case
	t.Run("Positive Test Case", func(t *testing.T) {
		testPositiveCase(t, clientset, maxRequestsInflight)
	})

	// Run the negative test case
	t.Run("Negative Test Case", func(t *testing.T) {
		testNegativeCase(t, clientset, maxRequestsInflight)
	})
}
