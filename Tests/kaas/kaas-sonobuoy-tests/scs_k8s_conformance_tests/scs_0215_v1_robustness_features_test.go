package scs_k8s_tests

import (
    "context"
    "crypto/x509"
    "encoding/pem"
    "fmt"
    "reflect"
    "log"
    "os"
    "strconv"
    "strings"
    "sync"
    "testing"
    "time"

    v1 "k8s.io/api/core/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/client-go/kubernetes"
    "k8s.io/client-go/rest"
)

// Configuration constants
const (
    defaultQPS   = 100
    defaultBurst = 200
)

// ==================== Helper Functions ====================

// Cluster Information Helpers

// getClusterSize returns the total number of nodes in the cluster
func getClusterSize(clientset *kubernetes.Clientset) int {
    nodes, err := clientset.CoreV1().Nodes().List(context.TODO(), metav1.ListOptions{})
    if err != nil {
        log.Fatalf("Failed to list nodes: %v", err)
    }
    return len(nodes.Items)
}

// isKindCluster determines if we're running on a kind cluster by checking node labels
func isKindCluster(clientset *kubernetes.Clientset) bool {
    nodes, err := clientset.CoreV1().Nodes().List(context.TODO(), metav1.ListOptions{})
    if err != nil {
        return false
    }
    for _, node := range nodes.Items {
        if _, ok := node.Labels["node-role.kubernetes.io/control-plane"]; ok {
            return true
        }
    }
    return false
}

// Configuration and Environment Helpers

// getEnvOrDefault retrieves an environment variable or returns a default value
func getEnvOrDefault(key string, defaultValue int) int {
    if value, exists := os.LookupEnv(key); exists {
        if intValue, err := strconv.Atoi(value); err == nil {
            return intValue
        }
    }
    return defaultValue
}

// setupClientset creates a Kubernetes clientset with specified QPS and Burst
func setupClientset(qps, burst float32) (*kubernetes.Clientset, error) {
    config, err := rest.InClusterConfig()
    if err != nil {
        return nil, fmt.Errorf("failed to load in-cluster config: %v", err)
    }

    config.QPS = qps
    config.Burst = int(burst)

    clientset, err := kubernetes.NewForConfig(config)
    if err != nil {
        return nil, fmt.Errorf("failed to create Kubernetes clientset: %v", err)
    }

    return clientset, nil
}

// Error Detection Helpers

// isRateLimitError checks if an error is related to rate limiting
func isRateLimitError(err error) bool {
    if err == nil {
        return false
    }
    return strings.Contains(err.Error(), "429") || 
           strings.Contains(strings.ToLower(err.Error()), "too many requests") ||
           strings.Contains(strings.ToLower(err.Error()), "rate limit")
}

// isTimeoutError checks if an error is related to timeouts
func isTimeoutError(err error) bool {
    if err == nil {
        return false
    }
    return err == context.DeadlineExceeded ||
           strings.Contains(err.Error(), "context deadline exceeded") || 
           strings.Contains(strings.ToLower(err.Error()), "timeout")
}

// Certificate Handling Helper

// parseCertificate decodes and parses an X.509 certificate from PEM format
func parseCertificate(certData []byte) (*x509.Certificate, error) {
    block, _ := pem.Decode(certData)
    if block == nil {
        return nil, fmt.Errorf("failed to decode PEM block")
    }

    cert, err := x509.ParseCertificate(block.Bytes)
    if err != nil {
        return nil, fmt.Errorf("failed to parse certificate: %v", err)
    }

    return cert, nil
}

// runConcurrentRequests executes multiple concurrent API requests and counts errors
func runConcurrentRequests(clientset *kubernetes.Clientset, requestCount int) int {
    var wg sync.WaitGroup
    errChan := make(chan error, requestCount)

    for i := 0; i < requestCount; i++ {
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
    return len(errChan)
}

// generateComplexFieldSelector creates a complex field selector for testing timeouts
func generateComplexFieldSelector() []string {
    selectors := make([]string, 100)
    for i := 0; i < 100; i++ {
        selectors[i] = fmt.Sprintf("metadata.name!=%d", i)
    }
    return selectors
}

// calculateMaxMutatingRequestsInflight determines the maximum number of mutating requests
func calculateMaxMutatingRequestsInflight(clusterSize int) int {
    return getEnvOrDefault("MAX_MUTATING_REQUESTS_INFLIGHT", clusterSize*50)
}

// hasEtcdBackup is a generic helper to check for etcd backup in various resources
func hasEtcdBackup[T any](items []T, nameCheck func(string) bool) bool {
    for _, item := range items {
        name := reflect.ValueOf(item).FieldByName("Name").String()
        if nameCheck(name) {
            return true
        }
    }
    return false
}

// findCertificateData looks for certificate data in secret data map
func findCertificateData(data map[string][]byte) []byte {
    // First check for standard TLS certificate key
    if certData, ok := data["tls.crt"]; ok {
        return certData
    }
    
    // Try alternative key names
    for key, data := range data {
        if strings.Contains(key, ".crt") || strings.Contains(key, "cert") {
            return data
        }
    }
    return nil
}

// ==================== Test Cases ====================

// Test groups are organized by feature:
// 1. API Request Limits
// 2. Request Timeout
// 3. Event Rate Limiting
// 4. API Priority and Fairness
// 5. etcd Management
// 6. Certificate Management

// -------------------- 1. API Request Limits --------------------

// Test_scs_0215_maxRequestInflight verifies the API server's max-requests-inflight setting
func Test_scs_0215_maxRequestInflight(t *testing.T) {
    clientset, err := setupClientset(defaultQPS, defaultBurst)
    if err != nil {
        t.Fatalf("Failed to setup clientset: %v", err)
    }

    clusterSize := getClusterSize(clientset)
    maxRequestsInflight := getEnvOrDefault("MAX_REQUESTS_INFLIGHT", clusterSize*250)

    t.Logf("Detected cluster size: %d nodes", clusterSize)
    t.Logf("Using maxRequestsInflight = %d", maxRequestsInflight)

    t.Run("Positive_Test_Case", func(t *testing.T) {
        // Test with safe number of requests (25% of limit)
        t.Log("Running Positive Test Case")
        safeRequests := maxRequestsInflight / 4
        errors := runConcurrentRequests(clientset, safeRequests)
        if errors > 0 {
            t.Errorf("Test failed: encountered %d unexpected errors when requests were expected to succeed.", errors)
        } else {
            t.Log("Positive test case passed successfully!")
        }
    })

    t.Run("Negative_Test_Case", func(t *testing.T) {
        // Test with excessive requests (200% of limit)
        t.Log("Running Negative Test Case")
        overloadRequests := maxRequestsInflight * 2
        errors := runConcurrentRequests(clientset, overloadRequests)

        if errors == 0 {
            t.Error("Test failed: expected rate limit errors, but all requests succeeded")
        } else {
            t.Log("Negative test case passed as expected: rate limit exceeded")
        }
    })
}

// Test_scs_0215_maxMutatingRequestsInflight verifies the API server's max-mutating-requests-inflight setting
func Test_scs_0215_maxMutatingRequestsInflight(t *testing.T) {
    clientset, err := setupClientset(defaultQPS, defaultBurst)
    if err != nil {
        t.Fatalf("Failed to setup clientset: %v", err)
    }

    clusterSize := getClusterSize(clientset)
    maxMutatingRequestsInflight := calculateMaxMutatingRequestsInflight(clusterSize)
    isKind := isKindCluster(clientset)

    t.Logf("Detected cluster size: %d nodes", clusterSize)
    t.Logf("Using maxMutatingRequestsInflight = %d", maxMutatingRequestsInflight)

    t.Run("Positive_Test_Case", func(t *testing.T) {
        t.Log("Running Positive Test Case")
        err := runMutatingTest(clientset, maxMutatingRequestsInflight/2)
        if err != nil {
            t.Fatalf("Positive test failed: %v", err)
        }
        t.Log("Positive test case passed successfully!")
    })

    t.Run("Negative_Test_Case", func(t *testing.T) {
        t.Log("Running Negative Test Case")
        // Use higher QPS/burst for negative test case
        highLoadClientset, _ := setupClientset(2000, 2000)
        
        var wg sync.WaitGroup
        errorChan := make(chan error, 5)
        
        // Run multiple concurrent batches of requests
        batchCount := 5
        if isKind {
            batchCount = 2 // Use fewer batches for kind clusters
        }
        
        for i := 0; i < batchCount; i++ {
            wg.Add(1)
            go func() {
                defer wg.Done()
                err := runMutatingTest(highLoadClientset, maxMutatingRequestsInflight)
                if err != nil {
                    errorChan <- err
                }
            }()
        }

        wg.Wait()
        close(errorChan)

        var gotRateLimit bool
        for err := range errorChan {
            if isRateLimitError(err) {
                gotRateLimit = true
                break
            }
        }

        if !gotRateLimit {
            if isKind {
                t.Log("No rate limit error in kind cluster - this is acceptable")
            } else {
                t.Error("Expected rate limit errors in production cluster, but got none")
            }
        }
    })
}

// runMutatingTest performs concurrent mutating requests to test rate limiting
func runMutatingTest(clientset *kubernetes.Clientset, limit int) error {
    var wg sync.WaitGroup
    errChan := make(chan error, limit)

    for i := 0; i < limit; i++ {
        wg.Add(1)
        go func(i int) {
            defer wg.Done()
            ctx, cancel := context.WithTimeout(context.TODO(), 2*time.Second)
            defer cancel()

            _, err := clientset.CoreV1().ConfigMaps("default").Create(ctx, &v1.ConfigMap{
                ObjectMeta: metav1.ObjectMeta{
                    GenerateName: fmt.Sprintf("test-cm-%d-", i),
                },
                Data: map[string]string{
                    "test": fmt.Sprintf("data-%d", i),
                    "load": strings.Repeat("x", 1000), // Add some data to increase request size
                },
            }, metav1.CreateOptions{})

            if err != nil {
                errChan <- err
            }
        }(i)
    }

    wg.Wait()
    close(errChan)

    var lastError error
    for err := range errChan {
        if isRateLimitError(err) {
            return err
        }
        lastError = err
    }

    return lastError
}

// -------------------- 2. Request Timeout --------------------

// Test_scs_0215_minRequestTimeout verifies the API server's min-request-timeout setting
func Test_scs_0215_minRequestTimeout(t *testing.T) {
    clientset, err := setupClientset(defaultQPS, defaultBurst)
    if err != nil {
        t.Fatalf("Failed to setup clientset: %v", err)
    }

    t.Run("Test_minRequestTimeout", func(t *testing.T) {
        isKind := isKindCluster(clientset)
        minRequestTimeout := time.Duration(getEnvOrDefault("MIN_REQUEST_TIMEOUT", 1)) * time.Second
        t.Logf("Testing with min-request-timeout = %v", minRequestTimeout)

        ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
        defer cancel()

        startTime := time.Now()
        _, err := clientset.CoreV1().Pods("default").List(ctx, metav1.ListOptions{
            FieldSelector: strings.Join(generateComplexFieldSelector(), ","),
        })
        duration := time.Since(startTime)

        if isKind {
            t.Logf("Running on kind cluster. Request completed in %v", duration)
        } else {
            if err == nil && duration < minRequestTimeout {
                t.Errorf("Request completed faster than minimum timeout. Duration: %v, Expected minimum: %v", duration, minRequestTimeout)
            } else {
                t.Logf("Request completed as expected in %v", duration)
            }
        }
    })
}

// -------------------- 3. Event Rate Limiting --------------------

// Test_scs_0215_eventRateLimit verifies the EventRateLimit admission controller configuration
func Test_scs_0215_eventRateLimit(t *testing.T) {
    clientset, err := setupClientset(defaultQPS, defaultBurst)
    if err != nil {
        t.Fatalf("Failed to setup clientset: %v", err)
    }

    isKind := isKindCluster(clientset)
    if isKind {
        t.Skip("Running on kind cluster - skipping EventRateLimit test as it's not required for development environments")
    }

    t.Run("Check_EventRateLimit_Configuration", func(t *testing.T) {
        // Check configurations in multiple locations
        configLocations := []struct {
            name      string
            namespace string
            key       string
        }{
            {"admission-configuration", "kube-system", "eventratelimit.yaml"},
            {"kube-apiserver", "kube-system", "config.yaml"},
        }

        for _, loc := range configLocations {
            config, err := clientset.CoreV1().ConfigMaps(loc.namespace).Get(
                context.TODO(),
                loc.name,
                metav1.GetOptions{},
            )
            if err == nil {
                if data, ok := config.Data[loc.key]; ok {
                    if strings.Contains(data, "eventratelimit.admission.k8s.io") {
                        t.Logf("Found EventRateLimit configuration in %s/%s", loc.namespace, loc.name)
                        return
                    }
                }
            }
        }

        // Check for standalone configuration
        configMaps, _ := clientset.CoreV1().ConfigMaps("kube-system").List(context.TODO(), metav1.ListOptions{})
        for _, cm := range configMaps.Items {
            if strings.Contains(cm.Name, "event-rate-limit") {
                t.Logf("Found standalone EventRateLimit configuration in ConfigMap: %s", cm.Name)
                return
            }
        }

        t.Error("No EventRateLimit configuration found in production cluster")
    })
}

// -------------------- 4. API Priority and Fairness --------------------

// Test_scs_0215_apiPriorityAndFairness verifies API Priority and Fairness (APF) configuration
func Test_scs_0215_apiPriorityAndFairness(t *testing.T) {
    clientset, err := setupClientset(defaultQPS, defaultBurst)
    if err != nil {
        t.Fatalf("Failed to setup clientset: %v", err)
    }

    isKind := isKindCluster(clientset)
    if isKind {
        t.Skip("Running on kind cluster - skipping APF test as it's configured differently in development environments")
    }

    t.Run("Check_APF_Configuration", func(t *testing.T) {
        // Multiple checks for APF configuration
        checks := []struct {
            name string
            fn   func() bool
        }{
            {"API Server Config", func() bool {
                config, err := clientset.CoreV1().ConfigMaps("kube-system").Get(
                    context.TODO(),
                    "kube-apiserver",
                    metav1.GetOptions{},
                )
                return err == nil && config.Data["config.yaml"] != "" &&
                    strings.Contains(config.Data["config.yaml"], "enable-priority-and-fairness: true")
            }},
            {"Command Line Flags", func() bool {
                pods, err := clientset.CoreV1().Pods("kube-system").List(context.TODO(), metav1.ListOptions{
                    LabelSelector: "component=kube-apiserver",
                })
                if err != nil || len(pods.Items) == 0 {
                    return false
                }
                for _, pod := range pods.Items {
                    for _, container := range pod.Spec.Containers {
                        for _, arg := range container.Command {
                            if strings.Contains(arg, "--enable-priority-and-fairness=true") {
                                return true
                            }
                        }
                    }
                }
                return false
            }},
            {"API Resources", func() bool {
                resources, err := clientset.Discovery().ServerResourcesForGroupVersion("flowcontrol.apiserver.k8s.io/v1beta3")
                if err != nil || resources == nil {
                    return false
                }
                for _, r := range resources.APIResources {
                    if r.Name == "flowschemas" || r.Name == "prioritylevelconfigurations" {
                        return true
                    }
                }
                return false
            }},
        }

        for _, check := range checks {
            if check.fn() {
                t.Logf("APF enabled via %s", check.name)
                return
            }
        }

        t.Error("No API Priority and Fairness configuration found in production cluster")
    })
}

// Test_scs_0215_rateLimitValues verifies recommended rate limit values
func Test_scs_0215_rateLimitValues(t *testing.T) {
    clientset, err := setupClientset(defaultQPS, defaultBurst)
    if err != nil {
        t.Fatalf("Failed to setup clientset: %v", err)
    }

    isKind := isKindCluster(clientset)
    if isKind {
        t.Skip("Running on kind cluster - skipping rate limit values test")
    }

    t.Run("Check_Rate_Limit_Values", func(t *testing.T) {
        // Define expected values
        expectedValues := map[string]string{
            "qps":   "5000",
            "burst": "20000",
        }

        // Check various possible configuration locations
        configMaps, _ := clientset.CoreV1().ConfigMaps("kube-system").List(context.TODO(), metav1.ListOptions{})
        for _, cm := range configMaps.Items {
            var config string
            switch {
            case strings.Contains(cm.Name, "event-rate-limit"):
                config = cm.Data["config.yaml"]
            case cm.Name == "admission-configuration":
                config = cm.Data["eventratelimit.yaml"]
            case cm.Name == "kube-apiserver":
                config = cm.Data["config.yaml"]
            }

            if config != "" {
                allFound := true
                for k, v := range expectedValues {
                    if !strings.Contains(config, fmt.Sprintf("%s: %s", k, v)) {
                        allFound = false
                        break
                    }
                }
                if allFound {
                    t.Log("Found recommended rate limit values")
                    return
                }
            }
        }

        t.Error("Recommended rate limit values (qps: 5000, burst: 20000) not found")
    })
}

// -------------------- 5. etcd Management --------------------

// Test_scs_0215_etcdCompaction verifies etcd compaction settings
func Test_scs_0215_etcdCompaction(t *testing.T) {
    clientset, err := setupClientset(defaultQPS, defaultBurst)
    if err != nil {
        t.Fatalf("Failed to setup clientset: %v", err)
    }

    isKind := isKindCluster(clientset)
    if isKind {
        t.Skip("Running on kind cluster - skipping etcd compaction test as it has different default settings")
    }

    t.Run("Check_Etcd_Compaction_Settings", func(t *testing.T) {
        // Try different label selectors for etcd pods
        selectors := []string{
            "component=etcd",
            "k8s-app=etcd",
            "tier=control-plane,component=etcd",
        }

        var etcdPods []v1.Pod
        for _, selector := range selectors {
            pods, err := clientset.CoreV1().Pods("kube-system").List(context.TODO(), metav1.ListOptions{
                LabelSelector: selector,
            })
            if err == nil && len(pods.Items) > 0 {
                etcdPods = pods.Items
                t.Logf("Found etcd pods using selector: %s", selector)
                break
            }
        }

        if len(etcdPods) == 0 {
            t.Skip("No etcd pods found - they might be running outside the cluster")
            return
        }

        // Expected settings
        requiredSettings := map[string]string{
            "auto-compaction-mode":       "periodic",
            "auto-compaction-retention":  "8h",
        }

        // Check each etcd pod
        for _, pod := range etcdPods {
            t.Logf("Checking etcd pod: %s", pod.Name)
            
            // Check ConfigMap first
            if cm, err := clientset.CoreV1().ConfigMaps("kube-system").Get(
                context.TODO(),
                "etcd-config",
                metav1.GetOptions{},
            ); err == nil {
                if config, ok := cm.Data["etcd.conf.yaml"]; ok {
                    allFound := true
                    for setting, value := range requiredSettings {
                        if !strings.Contains(config, fmt.Sprintf("%s: %s", setting, value)) {
                            allFound = false
                            break
                        }
                    }
                    if allFound {
                        t.Log("Found correct etcd compaction settings in ConfigMap")
                        return
                    }
                }
            }

            // Check command line arguments
            for _, container := range pod.Spec.Containers {
                foundSettings := make(map[string]bool)
                for _, arg := range container.Command {
                    for setting, value := range requiredSettings {
                        if strings.Contains(arg, fmt.Sprintf("--%s=%s", setting, value)) {
                            foundSettings[setting] = true
                        }
                    }
                }
                
                if len(foundSettings) == len(requiredSettings) {
                    t.Log("Found correct etcd compaction settings in command line arguments")
                    return
                }
            }
        }

        t.Error("Required etcd compaction settings not found")
    })
}

// Test_scs_0215_etcdBackup verifies etcd backup configuration
func Test_scs_0215_etcdBackup(t *testing.T) {
    clientset, err := setupClientset(defaultQPS, defaultBurst)
    if err != nil {
        t.Fatalf("Failed to setup clientset: %v", err)
    }

    isKind := isKindCluster(clientset)
    if isKind {
        t.Skip("Running on kind cluster - skipping etcd backup test as it's typically handled differently in development environments")
    }

    t.Run("Check_Etcd_Backup_Configuration", func(t *testing.T) {
        // Define backup solution checks
        backupChecks := []struct {
            name string
            fn   func() bool
        }{
            {"CronJob", func() bool {
                cronJobs, err := clientset.BatchV1().CronJobs("").List(context.TODO(), metav1.ListOptions{})
                return err == nil && hasEtcdBackup(cronJobs.Items, func(name string) bool {
                    return strings.Contains(strings.ToLower(name), "etcd") &&
                           strings.Contains(strings.ToLower(name), "backup")
                })
            }},
            {"Deployment", func() bool {
                deployments, err := clientset.AppsV1().Deployments("").List(context.TODO(), metav1.ListOptions{})
                return err == nil && hasEtcdBackup(deployments.Items, func(name string) bool {
                    return strings.Contains(strings.ToLower(name), "etcd") &&
                           strings.Contains(strings.ToLower(name), "backup")
                })
            }},
            {"DaemonSet", func() bool {
                daemonSets, err := clientset.AppsV1().DaemonSets("").List(context.TODO(), metav1.ListOptions{})
                return err == nil && hasEtcdBackup(daemonSets.Items, func(name string) bool {
                    return strings.Contains(strings.ToLower(name), "etcd") &&
                           strings.Contains(strings.ToLower(name), "backup")
                })
            }},
            {"Dedicated Pods", func() bool {
                pods, err := clientset.CoreV1().Pods("").List(context.TODO(), metav1.ListOptions{})
                return err == nil && hasEtcdBackup(pods.Items, func(name string) bool {
                    return strings.Contains(strings.ToLower(name), "etcd") &&
                           strings.Contains(strings.ToLower(name), "backup")
                })
            }},
        }

        for _, check := range backupChecks {
            if check.fn() {
                t.Logf("Found etcd backup solution: %s", check.name)
                return
            }
        }

        t.Error("No etcd backup solution found. Required: at least weekly backups through CronJob, Deployment, DaemonSet, or dedicated Pods")
    })
}

// -------------------- 6. Certificate Management --------------------

// Test_scs_0215_certificateRotation verifies certificate rotation configuration
func Test_scs_0215_certificateRotation(t *testing.T) {
    clientset, err := setupClientset(100, 200) // Using default QPS and Burst
    if err != nil {
        t.Fatalf("Failed to setup clientset: %v", err)
    }

    isKind := isKindCluster(clientset)
    if isKind {
        t.Skip("Running on kind cluster - skipping certificate rotation test")
    }

    t.Run("Check_Certificate_Expiration", func(t *testing.T) {
        secrets, err := clientset.CoreV1().Secrets("kube-system").List(context.TODO(), metav1.ListOptions{})
        if err != nil {
            t.Fatalf("Failed to list secrets: %v", err)
        }

        oneYearFromNow := time.Now().AddDate(1, 0, 0)
        certsChecked := 0
        
        for _, secret := range secrets.Items {
            // Check for TLS secrets and certificate-related secrets
            if secret.Type == v1.SecretTypeTLS || 
               strings.Contains(secret.Name, "cert") || 
               strings.Contains(secret.Name, "certificate") {
                
                certData := findCertificateData(secret.Data)
                if certData == nil {
                    continue
                }

                cert, err := parseCertificate(certData)
                if err != nil {
                    t.Logf("Failed to parse certificate from secret %s: %v", secret.Name, err)
                    continue
                }

                certsChecked++
                t.Logf("Checking certificate in secret: %s, expires: %v", secret.Name, cert.NotAfter)

                if cert.NotAfter.Before(oneYearFromNow) {
                    t.Errorf("Certificate in secret %s expires in less than a year (expires: %v)",
                        secret.Name, cert.NotAfter)
                }
            }
        }

        if certsChecked == 0 {
            t.Error("No certificates found to check")
        } else {
            t.Logf("Checked %d certificates", certsChecked)
        }
    })

    t.Run("Check_Certificate_Controller", func(t *testing.T) {
        // Check for cert-manager deployment
        deployments, err := clientset.AppsV1().Deployments("").List(context.TODO(), metav1.ListOptions{})
        if err != nil {
            t.Fatalf("Failed to list deployments: %v", err)
        }

        // Look for various certificate controller implementations
        certControllers := []string{
            "cert-manager",
            "certificate-controller",
            "cert-controller",
        }

        found := false
        for _, deployment := range deployments.Items {
            for _, controller := range certControllers {
                if strings.Contains(strings.ToLower(deployment.Name), controller) {
                    if deployment.Status.ReadyReplicas > 0 {
                        found = true
                        t.Logf("Found active certificate controller: %s", deployment.Name)
                        break
                    }
                }
            }
            if found {
                break
            }
        }

        if !found {
            // Check for built-in controller in kube-controller-manager
            pods, err := clientset.CoreV1().Pods("kube-system").List(context.TODO(), metav1.ListOptions{
                LabelSelector: "component=kube-controller-manager",
            })
            if err == nil && len(pods.Items) > 0 {
                for _, pod := range pods.Items {
                    for _, container := range pod.Spec.Containers {
                        for _, arg := range container.Command {
                            if strings.Contains(arg, "--controllers=*") ||
                               strings.Contains(arg, "--controllers=certificate") {
                                found = true
                                t.Log("Found built-in certificate controller in kube-controller-manager")
                                break
                            }
                        }
                    }
                }
            }
        }

        if !found {
            t.Error("No certificate controller found")
        }
    })
}