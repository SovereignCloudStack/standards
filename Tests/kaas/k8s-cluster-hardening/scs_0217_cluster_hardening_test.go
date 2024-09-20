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
	kubeletReadOnlyPort   = "10255"
	connectionTimeout     = 5 * time.Second
	sonobuoyResultsDir    = "/tmp/sonobuoy/results"
)

type KubeletConfig struct {
	KubeletConfig struct {
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

// Test_scs_0217_sonobuoy_Kubelet_ReadOnly_Port_Disabled checks
// if the Kubelet's read-only port (10255) is disabled on all nodes.
// If the port is open, it will log a warning.
func Test_scs_0217_sonobuoy_Kubelet_ReadOnly_Port_Disabled(t *testing.T) {
	f := features.New("kubelet security").Assess(
		"Kubelet read-only port (10255) should be disabled",
		func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			// Get the list of nodes in the cluster
			nodes := &corev1.NodeList{}
			err := cfg.Client().Resources().List(context.TODO(), nodes)
			if err != nil {
				t.Fatal("failed to list nodes:", err)
			}

			// Loop over each node and check if the read-only port is open
			for _, node := range nodes.Items {
				nodeIP := node.Status.Addresses[0].Address
				isPortOpen := checkPortOpen(nodeIP, kubeletReadOnlyPort, connectionTimeout)
				if isPortOpen {
					t.Logf("⚠️ WARNING: kubelet read-only port 10255 is open on node %s", nodeIP)
				} else {
					t.Logf("✅ kubelet read-only port 10255 is correctly disabled on node %s", nodeIP)
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

			err := cfg.Client().Resources().List(context.TODO(), nodes, resources.WithLabelSelector(labelSelector))
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
			// Get the list of endpoints in the cluster
			endpoints := &corev1.EndpointsList{}
			err := cfg.Client().Resources().List(context.TODO(), endpoints)
			if err != nil {
				t.Fatal("failed to list endpoints:", err)
			}

			// Iterate over the endpoints and check if they're secured via HTTPS
			for _, ep := range endpoints.Items {
				for _, subset := range ep.Subsets {
					for _, addr := range subset.Addresses {
						// Check each endpoint address for HTTPS security
						nodeIP := addr.IP
						for _, port := range subset.Ports {
							portName := port.Name
							portNum := port.Port

							// Check if the endpoint is secured via HTTPS
							if isPortSecuredWithHTTPS(nodeIP, portNum, connectionTimeout) {
								t.Logf("✅ Endpoint %s:%d (%s) is secured via HTTPS", nodeIP, portNum, portName)
							} else {
								t.Errorf("❌ ERROR: Endpoint %s:%d (%s) is not secured via HTTPS", nodeIP, portNum, portName)
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

			nodeList, err := kubeClient.CoreV1().Nodes().List(context.TODO(), v1.ListOptions{})
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

			// Check anonymous authentication from configz files
			for _, nodeName := range nodeNames {
				configzPath := path.Join(sonobuoyResultsDir, nodeName, "configz.json")
				kubeletConfig, err := readKubeletConfigFromFile(configzPath)
				if err != nil {
					t.Errorf("Failed to read Kubelet config from file %s: %v", configzPath, err)
					continue
				}

				// Check if anonymous authentication is enabled
				if kubeletConfig.KubeletConfig.Authentication.Anonymous.Enabled {
					t.Errorf("❌ ERROR: Kubelet anonymous authentication is enabled at %s", nodeName)
				} else {
					t.Logf("✅ Kubelet anonymous authentication is correctly disabled at %s", nodeName)
				}
			}

			return ctx
		})

	testenv.Test(t, f.Feature())
}

// Test_Kubelet_Webhook_Authorization_Enabled checks
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

			nodeList, err := kubeClient.CoreV1().Nodes().List(context.TODO(), v1.ListOptions{})
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

			// Check authorization mode from `configz` files
			for _, nodeName := range nodeNames {
				configzPath := path.Join(sonobuoyResultsDir, nodeName, "configz.json")
				kubeletConfig, err := readKubeletConfigFromFile(configzPath)
				if err != nil {
					t.Errorf("Failed to read Kubelet config from file %s: %v", configzPath, err)
					continue
				}

				// Check if the authorization mode is Webhook
				if kubeletConfig.KubeletConfig.Authorization.Mode != "Webhook" {
					t.Errorf("❌ ERROR: Kubelet authorization mode is not webhook, got %s", kubeletConfig.KubeletConfig.Authorization.Mode)
				} else {
					t.Logf("✅ Kubelet authorization mode is correctly set to Webhook")
				}
			}

			return ctx
		})

	testenv.Test(t, f.Feature())
}

// Test_NodeRestriction_Admission_Controller_Enabled checks if the NodeRestriction admission controller is enabled.
func Test_NodeRestriction_Admission_Controller_Enabled_in_KubeAPIServer(t *testing.T) {
	f := features.New("kube-apiserver admission plugins").Assess(
		"Check if NodeRestriction admission plugin is enabled in kube-apiserver pods",
		func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			// Create an in-cluster Kubernetes client configuration
			restConf, err := rest.InClusterConfig()
			if err != nil {
				t.Fatal("failed to create rest config:", err)
			}

			// Create a Kubernetes clientset
			kubeClient, err := kubernetes.NewForConfig(restConf)
			if err != nil {
				t.Fatal("failed to create Kubernetes client:", err)
			}

			// List all pods in the kube-system namespace with label "component=kube-apiserver"
			podList, err := kubeClient.CoreV1().Pods("kube-system").List(context.TODO(), v1.ListOptions{
				LabelSelector: "component=kube-apiserver",
			})
			if err != nil {
				t.Fatal("failed to list kube-apiserver pods:", err)
			}

			// Check each kube-apiserver pod
			for _, pod := range podList.Items {
				// Check each container in the pod
				for _, container := range pod.Spec.Containers {
					flagFound := false
					for _, cmd := range container.Command {
						if strings.Contains(cmd, "--enable-admission-plugins=NodeRestriction") {
							t.Logf("✅ NodeRestriction admission plugin is enabled in container: %s of pod: %s", container.Name, pod.Name)
							flagFound = true
							break
						}
					}

					if !flagFound {
						t.Errorf("❌ ERROR: NodeRestriction admission plugin is not enabled in container: %s of pod: %s", container.Name, pod.Name)
					}
				}
			}

			return ctx
		})

	testenv.Test(t, f.Feature())
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
		t.Errorf("❌ ERROR: port %s on node %s should not be accessible, but it is open", port, ip)
	} else if !isOpen && shouldBeAccessible {
		t.Errorf("❌ ERROR: port %s on node %s should be accessible, but it is not", port, ip)
	} else if isOpen && shouldBeAccessible {
		t.Logf("✅ port %s on node %s is accessible as expected", port, ip)
	} else {
		t.Logf("✅ port %s on node %s is correctly restricted", port, ip)
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

// waitForDirectory waits for a directory to become available at a specified path.
func waitForDirectory(path string, timeout time.Duration) error {
	start := time.Now()
	for time.Since(start) < timeout {
		if info, err := os.Stat(path); err == nil && info.IsDir() {
			return nil
		}
		time.Sleep(5 * time.Second)
	}
	return fmt.Errorf("directory %s not found after %v", path, timeout)
}

// isConfigzFile checks if a file is a configz.json file.
func isConfigzFile(fileName string) bool {
	return fileName != "" && (fileName[0:8] == "configz-")
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
