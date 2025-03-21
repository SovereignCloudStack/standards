package scs_k8s_tests

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"os"
	"path"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/sirupsen/logrus"
	corev1 "k8s.io/api/core/v1"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"sigs.k8s.io/e2e-framework/klient/k8s/resources"
	"sigs.k8s.io/e2e-framework/pkg/envconf"
	"sigs.k8s.io/e2e-framework/pkg/features"
)

const (
	apiServerPort         = "6443"
	controllerManagerPort = "10257"
	schedulerPort         = "10259"
	etcdPortRangeStart    = 2379
	etcdPortRangeEnd      = 2380
	kubeletApiPort        = "10250"
	kubeletReadOnlyPort   = 10255
	connectionTimeout     = 5 * time.Second
	sonobuoyResultsDir    = "/tmp/sonobuoy/results"
)

type KubeletConfig struct {
	KubeletConfig struct {
		ReadOnlyPort   int `json:"readOnlyPort"`
		Authentication struct {
			Anonymous struct {
				Enabled bool `json:"enabled"`
			} `json:"anonymous"`
		} `json:"authentication"`
		Authorization struct {
			Mode string `json:"mode"`
		} `json:"authorization"`
	} `json:"kubeletconfig"`
}

// ==================== Helper Functions ====================

// getNodeEndpoint returns the response from pinging a node endpoint.
func getNodeEndpoint(client rest.Interface, nodeName, endpoint string) (rest.Result, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	req := client.Get().
		Resource("nodes").
		Name(nodeName).
		SubResource("proxy").
		Suffix(endpoint)

	result := req.Do(ctx)
	if result.Error() != nil {
		logrus.Warningf("Could not get %v endpoint for node %v: %v", endpoint, nodeName, result.Error())
	}
	return result, result.Error()
}

// fetchAndSaveEndpointData fetches data from a node endpoint and saves it to a file.
func fetchAndSaveEndpointData(client rest.Interface, nodeName, endpoint, filePath string) error {
	result, err := getNodeEndpoint(client, nodeName, endpoint)
	if err != nil {
		return err
	}

	resultBytes, err := result.Raw()
	if err != nil {
		return err
	}

	if err := os.WriteFile(filePath, resultBytes, 0644); err != nil {
		return err
	}

	return nil
}

// gatherNodeData collects non-resource information about a node.
func gatherNodeData(nodeNames []string, restclient rest.Interface, outputDir string) error {
	for _, name := range nodeNames {
		out := path.Join(outputDir, name)
		logrus.Infof("Creating host results for %v under %v\n", name, out)
		if err := os.MkdirAll(out, 0755); err != nil {
			return err
		}

		configzPath := path.Join(out, "configz.json")
		if err := fetchAndSaveEndpointData(restclient, name, "configz", configzPath); err != nil {
			return err
		}
	}

	return nil
}

// readKubeletConfigFromFile reads and parses the Kubelet configuration from a file.
func readKubeletConfigFromFile(path string) (*KubeletConfig, error) {
	fmt.Printf("Reading Kubelet config from file: %s\n", path)
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("failed to open Kubelet config file: %w", err)
	}
	defer file.Close()

	bytes, err := io.ReadAll(file)
	if err != nil {
		return nil, fmt.Errorf("failed to read Kubelet config file: %w", err)
	}

	var kubeletConfig KubeletConfig
	if err := json.Unmarshal(bytes, &kubeletConfig); err != nil {
		return nil, fmt.Errorf("failed to parse Kubelet config file: %w", err)
	}

	return &kubeletConfig, nil
}

// checkPortOpen tries to establish a TCP connection to the given IP and port.
// It returns true if the port is open and false if the connection is refused or times out.
func checkPortOpen(ip, port string, timeout time.Duration) bool {
	address := net.JoinHostPort(ip, port)
	conn, err := net.DialTimeout("tcp", address, timeout)
	if err != nil {
		// Connection failed, the port is likely closed
		return false
	}
	// Connection succeeded, the port is open
	conn.Close()
	return true
}

// checkPortAccessibility verifies if a port is accessible or not, logging the result.
func checkPortAccessibility(t *testing.T, ip, port string, shouldBeAccessible bool) {
	isOpen := checkPortOpen(ip, port, connectionTimeout)
	if isOpen && !shouldBeAccessible {
		t.Errorf("Error: port %s on node %s should not be accessible, but it is open", port, ip)
	} else if !isOpen && shouldBeAccessible {
		t.Errorf("Error: port %s on node %s should be accessible, but it is not", port, ip)
	} else if isOpen && shouldBeAccessible {
		t.Logf("Port %s on node %s is accessible as expected", port, ip)
	} else {
		t.Logf("Port %s on node %s is correctly restricted", port, ip)
	}
}

// isPortSecuredWithHTTPS checks if a specific IP and port combination is secured via HTTPS.
func isPortSecuredWithHTTPS(ip string, port int32, timeout time.Duration) bool {
	address := net.JoinHostPort(ip, fmt.Sprintf("%d", port))

	conn, err := tls.DialWithDialer(
		&net.Dialer{Timeout: timeout},
		"tcp",
		address,
		&tls.Config{InsecureSkipVerify: true},
	)
	if err != nil {
		return false
	}
	defer conn.Close()

	return true
}

// checkPodSecurityAdmissionControllerEnabled checks if the PodSecurity admission controller is enabled in kube-apiserver pods
func checkPodSecurityAdmissionControllerEnabled(t *testing.T, kubeClient *kubernetes.Clientset) {
	// List all pods in the kube-system namespace with label "component=kube-apiserver"
	podList, err := kubeClient.CoreV1().Pods("kube-system").List(context.Background(), v1.ListOptions{
		LabelSelector: "component=kube-apiserver",
	})
	if err != nil {
		t.Fatal("failed to list kube-apiserver pods:", err)
	}

	// Check each kube-apiserver pod
	for _, pod := range podList.Items {
		t.Logf("Checking pod: %s for PodSecurity admission controller", pod.Name)
		for _, container := range pod.Spec.Containers {
			admissionPluginsFound := false
			// Look for the enable-admission-plugins flag in container command
			for _, cmd := range container.Command {
				if strings.Contains(cmd, "--enable-admission-plugins=") {
					admissionPluginsFound = true

					// Extract the plugins list and check if PodSecurity is one of them
					plugins := strings.Split(cmd, "=")[1]
					if strings.Contains(plugins, "PodSecurity") {
						t.Logf("PodSecurity admission plugin is enabled in container: %s of pod: %s", container.Name, pod.Name)
					} else {
						t.Errorf("Error: PodSecurity admission plugin is not enabled in container: %s of pod: %s", container.Name, pod.Name)
					}
					break
				}
			}

			if !admissionPluginsFound {
				t.Errorf("Error: --enable-admission-plugins flag not found in container: %s of pod: %s", container.Name, pod.Name)
			}
		}
	}
}

// checkPodSecurityPoliciesEnforced checks if Baseline and Restricted policies are enforced on namespaces
func checkPodSecurityPoliciesEnforced(t *testing.T, kubeClient *kubernetes.Clientset) {
	// List all namespaces
	namespaceList, err := kubeClient.CoreV1().Namespaces().List(context.Background(), v1.ListOptions{})
	if err != nil {
		t.Fatal("failed to list namespaces:", err)
	}

	// Check for the "pod-security.kubernetes.io/enforce" annotation in each namespace
	for _, namespace := range namespaceList.Items {
		annotations := namespace.Annotations
		enforcePolicy, ok := annotations["pod-security.kubernetes.io/enforce"]
		if !ok {
			t.Logf("Warning: Namespace %s does not have an enforce policy annotation", namespace.Name)
			continue
		}

		// Check if the policy is either Baseline or Restricted
		if enforcePolicy == "baseline" || enforcePolicy == "restricted" {
			t.Logf("Namespace %s enforces the %s policy", namespace.Name, enforcePolicy)
		} else {
			t.Errorf("Error: Namespace %s does not enforce Baseline or Restricted policy, but has %s", namespace.Name, enforcePolicy)
		}
	}
}

// checkAuthorizationmethods checks if authorization methods are correctly sets in k8s cluster based on standard
func checkAuthorizationmethods(t *testing.T, kubeClient *kubernetes.Clientset) {
	podList, err := kubeClient.CoreV1().Pods("kube-system").List(context.Background(), v1.ListOptions{
		LabelSelector: "component=kube-apiserver",
	})
	if err != nil {
		t.Fatal("failed to list kube-apiserver pods:", err)
	}

	// Check each kube-apiserver pod
	for _, pod := range podList.Items {
		t.Logf("Checking pod: %s for authorization modes", pod.Name)
		for _, container := range pod.Spec.Containers {
			authModeFound := false
			// Look for the --authorization-mode flag in container command
			for _, cmd := range container.Command {
				if strings.Contains(cmd, "--authorization-mode=") {
					authModeFound = true

					modes := strings.Split(cmd, "=")[1]
					authModes := strings.Split(modes, ",")

					nodeAuthEnabled := false
					otherAuthEnabled := false

					for _, mode := range authModes {
						mode = strings.TrimSpace(mode)
						if mode == "Node" {
							nodeAuthEnabled = true
						}
						if mode == "ABAC" || mode == "RBAC" || mode == "Webhook" {
							otherAuthEnabled = true
						}
					}

					// Validate the presence of required authorization methods
					if nodeAuthEnabled && otherAuthEnabled {
						t.Logf("Node authorization is enabled and at least one method (ABAC, RBAC or Webhook) is enabled.")
					} else if !nodeAuthEnabled {
						t.Errorf("Error: Node authorization is not enabled in api-server pod: %s", pod.Name)
					} else if !otherAuthEnabled {
						t.Errorf("Error: None of ABAC, RBAC, or Webhook authorization methods are enabled in api-server pod: %s", pod.Name)
					}
					break
				}
			}

			// If the --authorization-mode flag is not found
			if !authModeFound {
				t.Errorf("Error: --authorization-mode flag not found in api-server pod: %s", pod.Name)
			}
		}
	}
}

// checkKubeAPIServerETCDTLS checks whether the kube-apiserver communicates with etcd over TLS.
func checkKubeAPIServerETCDTLS(t *testing.T, kubeClient *kubernetes.Clientset) {
	// List kube-apiserver pods
	podList, err := kubeClient.CoreV1().Pods("kube-system").List(context.Background(), v1.ListOptions{
		LabelSelector: "component=kube-apiserver",
	})
	if err != nil {
		t.Fatal("failed to list kube-apiserver pods:", err)
	}

	// Expected etcd TLS flags
	requiredFlags := []string{
		"--etcd-certfile=",
		"--etcd-keyfile=",
		"--etcd-cafile=",
	}

	// Check each kube-apiserver pod
	for _, pod := range podList.Items {
		for _, container := range pod.Spec.Containers {
			// Gather all the commands into a single string for easier matching
			cmdLine := strings.Join(container.Command, " ")
			t.Logf("TEST: Checking container: %s of pod: %s", container.Name, pod.Name)

			// Check if all required etcd TLS flags are present
			allFlagsPresent := true
			for _, flag := range requiredFlags {
				if !strings.Contains(cmdLine, flag) {
					t.Errorf("Missing flag %s in container: %s of pod: %s", flag, container.Name, pod.Name)
					allFlagsPresent = false
				}
			}

			if allFlagsPresent {
				t.Logf("kube-apiserver communicates with etcd using TLS in container: %s of pod: %s", container.Name, pod.Name)
			} else {
				t.Errorf("Error: kube-apiserver does not use all required TLS flags for etcd communication in container: %s of pod: %s", container.Name, pod.Name)
			}
		}
	}
}

// checkIsolationETCD checks whether the etcd is isolated from k8s cluster.
func checkIsolationETCD(t *testing.T, kubeClient *kubernetes.Clientset) {
	// List kube-apiserver pods
	podList, err := kubeClient.CoreV1().Pods("kube-system").List(context.Background(), v1.ListOptions{
		LabelSelector: "component=kube-apiserver",
	})
	if err != nil {
		t.Fatal("failed to list kube-apiserver pods:", err)
	}

	// Check each kube-apiserver pod
	for _, pod := range podList.Items {
		for _, container := range pod.Spec.Containers {
			etcdServersFound := false
			for _, cmd := range container.Command {
				if strings.Contains(cmd, "--etcd-servers=") {
					etcdServersFound = true
					etcdServers := strings.Split(cmd, "--etcd-servers=")[1]
					etcdEndpoints := strings.Split(etcdServers, ",")

					// Verify that etcd is not running on localhost
					for _, endpoint := range etcdEndpoints {
						if strings.Contains(endpoint, "localhost") || strings.Contains(endpoint, "127.0.0.1") {
							t.Logf("Warning: etcd should be isolated from k8s cluster, currently it is running on localhost: %s", endpoint)
						} else {
							t.Logf("ETCD is isolated at endpoint: %s", endpoint)
						}
					}
				}
			}

			if !etcdServersFound {
				t.Errorf("Error: --etcd-servers flag is missing in kube-apiserver pod: %s", pod.Name)
			}
		}
	}
}

// ==================== Test Cases ====================

// Test_scs_0217_sonobuoy_Kubelet_ReadOnly_Port_Disabled checks
// if the Kubelet's read-only port (10255) is disabled on all nodes.
// If the port is open, it will log a warning.
func Test_scs_0217_sonobuoy_Kubelet_ReadOnly_Port_Disabled(t *testing.T) {
	f := features.New("kubelet security").Assess(
		"Kubelet read-only port (10255) should be disabled",
		func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			restConf, err := rest.InClusterConfig()
			if err != nil {
				t.Fatal("failed to create rest config:", err)
			}

			kubeClient, err := kubernetes.NewForConfig(restConf)
			if err != nil {
				t.Fatal("failed to create Kubernetes client:", err)
			}

			nodeList, err := kubeClient.CoreV1().Nodes().List(context.Background(), v1.ListOptions{})
			if err != nil {
				t.Fatal("failed to get node list:", err)
			}

			nodeNames := make([]string, len(nodeList.Items))
			for i, node := range nodeList.Items {
				nodeNames[i] = node.Name
			}

			if err := gatherNodeData(nodeNames, kubeClient.CoreV1().RESTClient(), sonobuoyResultsDir); err != nil {
				t.Fatal("failed to gather node data:", err)
			}

			// Get kubelets configz file from each node
			for _, nodeName := range nodeNames {
				configzPath := path.Join(sonobuoyResultsDir, nodeName, "configz.json")
				kubeletConfig, err := readKubeletConfigFromFile(configzPath)
				if err != nil {
					t.Errorf("Failed to read Kubelet config from file %s: %v", configzPath, err)
					continue
				}

				// Check if readonly port is enabled
				if kubeletConfig.KubeletConfig.ReadOnlyPort == kubeletReadOnlyPort {
					t.Logf("Warning: kubelet read-only port 10255 is open on node %s", nodeName)
				} else {
					t.Logf("Kubelet read-only port 10255 is correctly disabled on node %s", nodeName)
				}
			}
			return ctx
		})

	testenv.Test(t, f.Feature())
}

// Test_Control_Plane_Ports_Security checks if the control plane ports (other than API server and NodePorts)
// are not accessible from outside the internal network.
func Test_scs_0217_sonobuoy_Control_Plane_Ports_Security(t *testing.T) {
	f := features.New("control plane security").Assess(
		"Control plane ports (other than API server and NodePorts) should not be accessible externally",
		func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			nodes := &corev1.NodeList{}
			labelSelector := labels.Set{
				"node-role.kubernetes.io/control-plane": "",
			}.AsSelector().String()

			err := cfg.Client().Resources().List(context.Background(), nodes, resources.WithLabelSelector(labelSelector))
			if err != nil {
				t.Fatal("failed to list control plane nodes:", err)
			}

			for _, node := range nodes.Items {
				nodeIP := node.Status.Addresses[0].Address

				// Check that the API server port (6443) is accessible
				checkPortAccessibility(t, nodeIP, apiServerPort, true)

				// Check that the control plane ports (other than API server) are not accessible
				checkPortAccessibility(t, nodeIP, controllerManagerPort, false)
				checkPortAccessibility(t, nodeIP, schedulerPort, false)
				checkPortAccessibility(t, nodeIP, kubeletApiPort, false)

				// Check the etcd ports (2379-2380) are not accessible
				for port := etcdPortRangeStart; port <= etcdPortRangeEnd; port++ {
					checkPortAccessibility(t, nodeIP, fmt.Sprintf("%d", port), false)
				}
			}
			return ctx
		})

	testenv.Test(t, f.Feature())
}

// Test_K8s_Endpoints_HTTPS checks if all Kubernetes endpoints are secured via HTTPS.
func Test_scs_0217_sonobuoy_K8s_Endpoints_HTTPS(t *testing.T) {
	f := features.New("Kubernetes endpoint security").Assess(
		"All Kubernetes endpoints should be secured via HTTPS",
		func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			requiredHTTPSPorts := map[string]bool{
				apiServerPort:         true,
				controllerManagerPort: true,
				schedulerPort:         true,
				kubeletApiPort:        true,
			}

			// Add etcd ports
			for port := etcdPortRangeStart; port <= etcdPortRangeEnd; port++ {
				requiredHTTPSPorts[strconv.Itoa(port)] = true
			}

			endpoints := &corev1.EndpointsList{}
			if err := cfg.Client().Resources().List(context.Background(), endpoints); err != nil {
				t.Fatal("failed to list endpoints:", err)
			}

			for _, ep := range endpoints.Items {
				for _, subset := range ep.Subsets {
					for _, addr := range subset.Addresses {
						for _, port := range subset.Ports {
							portStr := strconv.Itoa(int(port.Port))
							if requiredHTTPSPorts[portStr] {
								if isPortSecuredWithHTTPS(addr.IP, port.Port, connectionTimeout) {
									t.Logf("Endpoint %s:%d (%s) is secured via HTTPS", addr.IP, port.Port, port.Name)
								} else {
									t.Errorf("Error: Endpoint %s:%d (%s) is not secured via HTTPS", addr.IP, port.Port, port.Name)
								}
							}
						}
					}
				}
			}
			return ctx
		})

	testenv.Test(t, f.Feature())
}

// Test_scs_0217_sonobuoy_Kubelet_HTTPS_Anonymous_Auth_Disabled checks
// if the Kubelet's anonymous access is disabled based on the configz file.
func Test_scs_0217_sonobuoy_Kubelet_HTTPS_Anonymous_Auth_Disabled(t *testing.T) {
	f := features.New("kubelet security").Assess(
		"Kubelet HTTPS anonymous access should be disabled based on the configz",
		func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			restConf, err := rest.InClusterConfig()
			if err != nil {
				t.Fatal("failed to create rest config:", err)
			}

			kubeClient, err := kubernetes.NewForConfig(restConf)
			if err != nil {
				t.Fatal("failed to create Kubernetes client:", err)
			}

			nodeList, err := kubeClient.CoreV1().Nodes().List(context.Background(), v1.ListOptions{})
			if err != nil {
				t.Fatal("failed to get node list:", err)
			}

			nodeNames := make([]string, len(nodeList.Items))
			for i, node := range nodeList.Items {
				nodeNames[i] = node.Name
			}

			if err := gatherNodeData(nodeNames, kubeClient.CoreV1().RESTClient(), sonobuoyResultsDir); err != nil {
				t.Fatal("failed to gather node data:", err)
			}

			// Get kubelets configz file from each node
			for _, nodeName := range nodeNames {
				configzPath := path.Join(sonobuoyResultsDir, nodeName, "configz.json")
				kubeletConfig, err := readKubeletConfigFromFile(configzPath)
				if err != nil {
					t.Errorf("Failed to read Kubelet config from file %s: %v", configzPath, err)
					continue
				}

				// Check if anonymous authentication is enabled
				if kubeletConfig.KubeletConfig.Authentication.Anonymous.Enabled {
					t.Errorf("ERROR: Kubelet anonymous authentication is enabled at %s", nodeName)
				} else {
					t.Logf("Kubelet anonymous authentication is correctly disabled at %s", nodeName)
				}
			}

			return ctx
		})

	testenv.Test(t, f.Feature())
}

// Test_scs_0217_sonobuoy_Kubelet_Webhook_Authorization_Enabled checks
// if the Kubelet's authorization mode is Webhook by accessing the Kubelet's /configz endpoint.
func Test_scs_0217_sonobuoy_Kubelet_Webhook_Authorization_Enabled(t *testing.T) {
	f := features.New("kubelet security").Assess(
		"Kubelet authorization mode should be Webhook from Sonobuoy results",
		func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			restConf, err := rest.InClusterConfig()
			if err != nil {
				t.Fatal("failed to create rest config:", err)
			}

			kubeClient, err := kubernetes.NewForConfig(restConf)
			if err != nil {
				t.Fatal("failed to create Kubernetes client:", err)
			}

			nodeList, err := kubeClient.CoreV1().Nodes().List(context.Background(), v1.ListOptions{})
			if err != nil {
				t.Fatal("failed to get node list:", err)
			}

			nodeNames := make([]string, len(nodeList.Items))
			for i, node := range nodeList.Items {
				nodeNames[i] = node.Name
			}

			if err := gatherNodeData(nodeNames, kubeClient.CoreV1().RESTClient(), sonobuoyResultsDir); err != nil {
				t.Fatal("failed to gather node data:", err)
			}

			// Get kubelets configz file from each node
			for _, nodeName := range nodeNames {
				configzPath := path.Join(sonobuoyResultsDir, nodeName, "configz.json")
				kubeletConfig, err := readKubeletConfigFromFile(configzPath)
				if err != nil {
					t.Errorf("failed to read Kubelet config from file %s: %v", configzPath, err)
					continue
				}

				// Check if the authorization mode is set to Webhook
				if kubeletConfig.KubeletConfig.Authorization.Mode != "Webhook" {
					t.Errorf("Error: Kubelet authorization mode is not webhook, got %s", kubeletConfig.KubeletConfig.Authorization.Mode)
				} else {
					t.Logf("kubelet authorization mode is correctly set to Webhook")
				}
			}

			return ctx
		})

	testenv.Test(t, f.Feature())
}

// Test_scs_0217_sonobuoy_NodeRestriction_Admission_Controller_Enabled_in_KubeAPIServer
// checks if the NodeRestriction admission controller is enabled.
func Test_scs_0217_sonobuoy_NodeRestriction_Admission_Controller_Enabled_in_KubeAPIServer(t *testing.T) {
	f := features.New("kube-apiserver admission plugins").Assess(
		"Check if NodeRestriction admission plugin is enabled in kube-apiserver pods",
		func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			restConf, err := rest.InClusterConfig()
			if err != nil {
				t.Fatal("failed to create rest config:", err)
			}

			// Create a Kubernetes client
			kubeClient, err := kubernetes.NewForConfig(restConf)
			if err != nil {
				t.Fatal("failed to create Kubernetes client:", err)
			}

			// List all pods in the kube-system namespace with label "component=kube-apiserver"
			podList, err := kubeClient.CoreV1().Pods("kube-system").List(context.Background(), v1.ListOptions{
				LabelSelector: "component=kube-apiserver",
			})
			if err != nil {
				t.Fatal("failed to list kube-apiserver pods:", err)
			}

			// Check each kube-apiserver pod
			for _, pod := range podList.Items {
				for _, container := range pod.Spec.Containers {
					cmdFound := false
					for _, cmd := range container.Command {
						if strings.Contains(cmd, "--enable-admission-plugins=NodeRestriction") {
							t.Logf("NodeRestriction admission plugin is enabled in pod: %s", pod.Name)
							cmdFound = true
							break
						}
					}

					if !cmdFound {
						t.Errorf("Error: NodeRestriction admission plugin is not enabled in pod: %s", pod.Name)
					}
				}
			}

			return ctx
		})

	testenv.Test(t, f.Feature())
}

// Test_scs_0217_sonobuoy_PodSecurity_Standards_And_Admission_Controller_Enabled
// checks if the PodSecurity admission controller is enabled and
// verify that if Pod Security Standards (Baseline/Restricted) are enforced on namespaces.
func Test_scs_0217_sonobuoy_PodSecurity_Standards_And_Admission_Controller_Enabled(t *testing.T) {
	f := features.New("pod security standards").Assess(
		"Pod security admission controller should be enabled and enforce Baseline/Restricted policies",
		func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			restConf, err := rest.InClusterConfig()
			if err != nil {
				t.Fatal("failed to create rest config:", err)
			}

			// Create a Kubernetes client
			kubeClient, err := kubernetes.NewForConfig(restConf)
			if err != nil {
				t.Fatal("failed to create Kubernetes client:", err)
			}

			// Check that the PodSecurity admission controller is enabled in the kube-apiserver pods
			checkPodSecurityAdmissionControllerEnabled(t, kubeClient)

			// Verify that Pod Security Standards (Baseline/Restricted) are enforced on namespaces
			checkPodSecurityPoliciesEnforced(t, kubeClient)

			return ctx
		})

	testenv.Test(t, f.Feature())
}

// Test_scs_0217_sonobuoy_Authorization_Methods checks whether at least two authorization methods are sets in k8s cluster,
// one of which MUST be Node authorization and another one consisting of either ABAC, RBAC or Webhook authorization.
func Test_scs_0217_sonobuoy_Authorization_Methods(t *testing.T) {
	f := features.New("authorization methods").Assess(
		"At least two authorization methods must be set, one of which must be Node authorization "+
			"and another one consisting of either ABAC, RBAC, or Webhook authorization",
		func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			restConf, err := rest.InClusterConfig()
			if err != nil {
				t.Fatal("failed to create rest config:", err)
			}

			// Create a Kubernetes client
			kubeClient, err := kubernetes.NewForConfig(restConf)
			if err != nil {
				t.Fatal("failed to create Kubernetes client:", err)
			}

			// Check authorization methods in the kube-apiserver
			checkAuthorizationmethods(t, kubeClient)

			return ctx
		})

	testenv.Test(t, f.Feature())
}

// Test_scs_0217_sonobuoy_Authentication_Methods checks if at least two authentication methods are enabled in the cluster,
// one of which MUST be Service Account Tokens, to provide full functionality to Pods.
func Test_scs_0217_sonobuoy_Authentication_Methods(t *testing.T) {
	f := features.New("authentication methods").Assess(
		"At least two authentication methods must be enabled, one of which MUST be Service Account Tokens",
		func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			restConf, err := rest.InClusterConfig()
			if err != nil {
				t.Fatal("failed to create rest config:", err)
			}

			kubeClient, err := kubernetes.NewForConfig(restConf)
			if err != nil {
				t.Fatal("failed to create Kubernetes client:", err)
			}

			podList, err := kubeClient.CoreV1().Pods("kube-system").List(context.Background(), v1.ListOptions{
				LabelSelector: "component=kube-apiserver",
			})
			if err != nil {
				t.Fatal("failed to list kube-apiserver pods:", err)
			}

			// Check each kube-apiserver pod for authentication modes
			for _, pod := range podList.Items {
				t.Logf("Checking pod: %s for authentication methods", pod.Name)

				for _, container := range pod.Spec.Containers {
					// Check for the --authentication-token-webhook and --service-account-issuer flags in the container's command
					authMethodsFound := map[string]bool{
						"ServiceAccountTokens": false,
						"OtherAuthMethod":      false,
					}

					for _, cmd := range container.Command {
						// Check for Service Account Tokens (--service-account-issuer)
						if strings.Contains(cmd, "--service-account-issuer=") {
							authMethodsFound["ServiceAccountTokens"] = true
						}
						// Check for other authentication methods like --authentication-token-webhook-config-file or --oidc-issuer-url
						if strings.Contains(cmd, "--authentication-token-webhook-config-file=") || strings.Contains(cmd, "--oidc-issuer-url=") {
							authMethodsFound["OtherAuthMethod"] = true
						}
					}

					// Check if both authentication methods are present
					if authMethodsFound["ServiceAccountTokens"] && authMethodsFound["OtherAuthMethod"] {
						t.Logf("Both authentication methods (Service Account Tokens and another method) are enabled")
					} else {
						if !authMethodsFound["ServiceAccountTokens"] {
							t.Errorf("Error: Service Account Tokens are not enabled")
						}
						if !authMethodsFound["OtherAuthMethod"] {
							t.Errorf("Error: No other authentication method (Token Webhook or OIDC) is enabled")
						}
					}
				}
			}

			return ctx
		})

	testenv.Test(t, f.Feature())
}

// Test_scs_0217_etcd_tls checks if communication with etcd is secured with TLS for both peer- and cluster-communication.
func Test_scs_0217_etcd_tls_communication(t *testing.T) {
	f := features.New("etcd security").Assess(
		"Communication with etcd MUST be secured with TLS for both peer- and cluster-communication",
		func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			restConf, err := rest.InClusterConfig()
			if err != nil {
				t.Fatal("failed to create rest config:", err)
			}

			kubeClient, err := kubernetes.NewForConfig(restConf)
			if err != nil {
				t.Fatal("failed to create Kubernetes client:", err)
			}

			// Check kube-apiserver communication with etcd
			checkKubeAPIServerETCDTLS(t, kubeClient)

			return ctx
		})

	testenv.Test(t, f.Feature())
}

// Test_scs_0217_etcd_isolation checks ETCD is isolated from k8s cluster by checking the etcd server endpoints.
func Test_scs_0217_etcd_isolation(t *testing.T) {
	f := features.New("etcd security").Assess(
		"ETCD should be isolated from the Kubernetes cluster",
		func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			restConf, err := rest.InClusterConfig()
			if err != nil {
				t.Fatal("failed to create rest config:", err)
			}

			kubeClient, err := kubernetes.NewForConfig(restConf)
			if err != nil {
				t.Fatal("failed to create Kubernetes client:", err)
			}

			// Check if etcd is isolated from k8s cluster
			checkIsolationETCD(t, kubeClient)

			return ctx
		})

	testenv.Test(t, f.Feature())
}
