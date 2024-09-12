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

	v1 "k8s.io/api/core/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

)

// getClusterSize estimates the cluster size by counting the number of nodes.
func getClusterSize(clientset *kubernetes.Clientset) int {
	nodes, err := clientset.CoreV1().Nodes().List(context.TODO(), metav1.ListOptions{})
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
			_, err := clientset.CoreV1().Pods("").List(ctx, metav1.ListOptions{})
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
    config.QPS = 10000    // Matches server-side QPS
    config.Burst = 40000 // Matches server-side Burst

    // Create the clientset from the config
    clientset, err := kubernetes.NewForConfig(config)
    if err != nil {
        log.Fatalf("Failed to create Kubernetes clientset: %v", err)
    }

    // Increase timeout to allow more time for requests to complete
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    // Example of using the clientset to list pods
    _, err = clientset.CoreV1().Pods("").List(ctx, metav1.ListOptions{})
    if err != nil {
        if isRateLimitError(err) {
            log.Printf("Rate limit error: %v", err)
        } else {
            log.Printf("Unexpected error: %v", err) // Log unexpected errors with details
        }
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

// Main test function for max-mutating-requests-inflight
func Test_scs_maxMutatingRequestsInflight(t *testing.T) {
    // Load in-cluster configuration
    config, err := rest.InClusterConfig()
    if err != nil {
        log.Fatalf("Failed to load in-cluster config: %v", err)
    }

    // Set higher QPS and burst limits to avoid client-side throttling
    config.QPS = 100
    config.Burst = 200

    clientset, err := kubernetes.NewForConfig(config)
    if err != nil {
        log.Fatalf("Failed to create Kubernetes client: %v", err)
    }

    clusterSize := detectClusterSize() // Detects the cluster size
    maxMutatingRequestsInflight := calculateMaxMutatingRequestsInflight(clusterSize)
    fmt.Printf("Detected cluster size: %d nodes\n", clusterSize)
    fmt.Printf("Using maxMutatingRequestsInflight = %d\n", maxMutatingRequestsInflight)

    // Positive Test Case: Requests within the allowed limit
    t.Run("Positive_Test_Case", func(t *testing.T) {
        fmt.Println("Running Positive Test Case")
        err := runMutatingTest(clientset, maxMutatingRequestsInflight) // Pass clientset here
        if err != nil {
            t.Fatalf("Test failed: encountered unexpected errors when requests were expected to succeed: %v", err)
        }
        fmt.Println("Positive test case passed successfully!")
    })

    // Negative Test Case: Exceeding the allowed limit
    t.Run("Negative_Test_Case", func(t *testing.T) {
        fmt.Println("Running Negative Test Case")
        err := runMutatingTest(clientset, maxMutatingRequestsInflight + 10) // Pass clientset here and exceed limit
        if err != nil && isRateLimitError(err) {
            fmt.Println("Negative test case passed as expected: rate limit exceeded.")
        } else {
            t.Fatalf("Test failed: expected rate limit errors, but requests succeeded or another error occurred: %v", err)
        }
    })
}


// Function to detect the size of the cluster (stubbed, adjust as needed)
func detectClusterSize() int {
    // Logic to detect cluster size (for example using kubectl)
    return 1 // Default for single-node kind cluster
}

// Function to calculate max-mutating-requests-inflight based on cluster size
func calculateMaxMutatingRequestsInflight(clusterSize int) int {
    // Adjust this formula based on your requirements
    return 100 * clusterSize // Example: 100 mutating requests per node
}

// Function to simulate sending mutating requests up to the given limit
func runMutatingTest(clientset *kubernetes.Clientset, limit int) error {
    var wg sync.WaitGroup
    errChan := make(chan error, limit)

    for i := 0; i < limit; i++ {
        wg.Add(1)
        go func(i int) {
            defer wg.Done()
            ctx, cancel := context.WithTimeout(context.TODO(), 20*time.Second)
            defer cancel()

            // Create a unique Pod name
            podName := fmt.Sprintf("test-pod-%d", i)

            // Create a Pod
            _, err := clientset.CoreV1().Pods("default").Create(ctx, &v1.Pod{
                ObjectMeta: metav1.ObjectMeta{
                    Name: podName,
                },
                Spec: v1.PodSpec{
                    Containers: []v1.Container{
                        {
                            Name:  "test-container",
                            Image: "busybox",
                        },
                    },
                },
            }, metav1.CreateOptions{})

            if err != nil {
                if isRateLimitError(err) {
                    errChan <- fmt.Errorf("rate limit reached")
                } else {
                    errChan <- fmt.Errorf("error creating pod: %v", err)
                }
                return
            }

            // Clean up by deleting the Pod
            err = clientset.CoreV1().Pods("default").Delete(ctx, podName, metav1.DeleteOptions{})
            if err != nil {
                if isRateLimitError(err) {
                    errChan <- fmt.Errorf("rate limit reached")
                } else {
                    errChan <- fmt.Errorf("error deleting pod: %v", err)
                }
                return
            }
        }(i)
    }

    wg.Wait()
    close(errChan)

    var rateLimitErrors, otherErrors int
    for err := range errChan {
        if err.Error() == "rate limit reached" {
            rateLimitErrors++
        } else {
            otherErrors++
        }
    }

    if otherErrors > 0 {
        return fmt.Errorf("encountered %d unexpected errors", otherErrors)
    }

    if rateLimitErrors > 0 {
        fmt.Printf("Rate limit errors encountered: %d\n", rateLimitErrors)
    }

    return nil
}

// Function to determine if an error is related to rate limiting
func isRateLimitError(err error) bool {
    if err == nil {
        return false
    }
    return err.Error() == "TooManyRequests" || err.Error() == "429"
}

// Main test function for min-request-timeout
func Test_scs_minRequestTimeout(t *testing.T) {
    // Load in-cluster configuration
    config, err := rest.InClusterConfig()
    if err != nil {
        log.Fatalf("Failed to load in-cluster config: %v", err)
    }

    // Set QPS and Burst to higher values to avoid throttling
    config.QPS = 100
    config.Burst = 200

    // Create a Kubernetes client
    clientset, err := kubernetes.NewForConfig(config)
    if err != nil {
        log.Fatalf("Failed to create Kubernetes client: %v", err)
    }

    // Test case: min-request-timeout enforced (timeout set to 5 seconds)
    t.Run("Test_minRequestTimeout", func(t *testing.T) {
        minRequestTimeout := 5 * time.Second
        fmt.Printf("Testing with min-request-timeout = %v\n", minRequestTimeout)

        ctx, cancel := context.WithTimeout(context.Background(), minRequestTimeout)
        defer cancel()

        // Send a request to the Kubernetes API (List Pods in a namespace)
        _, err := clientset.CoreV1().Pods("default").List(ctx, metav1.ListOptions{})

        // Check if the request failed due to timeout
        if err != nil && isTimeoutError(err) {
            fmt.Printf("Request failed as expected due to timeout: %v\n", err)
        } else if err != nil {
            t.Fatalf("Test failed: unexpected error occurred: %v\n", err)
        } else {
            t.Fatalf("Test failed: request succeeded but was expected to timeout")
        }
    })
}

// Helper function to check if an error is a timeout error
func isTimeoutError(err error) bool {
    if err == nil {
        return false
    }
    return err.Error() == "context deadline exceeded"
}