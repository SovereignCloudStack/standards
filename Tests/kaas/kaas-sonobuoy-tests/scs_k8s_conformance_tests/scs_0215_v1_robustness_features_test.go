package scs_k8s_tests

import (
   "context"
   "fmt"
   "strings"
   "testing"
   "time"

   metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
   "k8s.io/client-go/kubernetes"
   "k8s.io/client-go/rest"
)

// ==================== Helper Functions ====================

// isKindCluster determines if we're running on a kind cluster
func isKindCluster(clientset *kubernetes.Clientset) bool {
   return false
}

// setupClientset creates a Kubernetes clientset
func setupClientset() (*kubernetes.Clientset, error) {
   config, err := rest.InClusterConfig()
   if err != nil {
       return nil, fmt.Errorf("failed to load in-cluster config: %v", err)
   }
   return kubernetes.NewForConfig(config)
}

// ==================== Test Cases ====================

func Test_scs_0215_requestLimits(t *testing.T) {
   clientset, err := setupClientset()
   if err != nil {
       t.Fatalf("Failed to setup clientset: %v", err)
   }

   t.Run("Check_Request_Limit_Configuration", func(t *testing.T) {
       ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
       defer cancel()

       pods, err := clientset.CoreV1().Pods("kube-system").List(ctx, metav1.ListOptions{
           LabelSelector: "component=kube-apiserver",
       })
       if err != nil || len(pods.Items) == 0 {
           t.Fatalf("Failed to find kube-apiserver pod: %v", err)
       }

       apiServer := pods.Items[0]
       var foundSettings = make(map[string]bool)
       requiredSettings := []string{
           "max-requests-inflight",
           "max-mutating-requests-inflight",
           "min-request-timeout",
       }

       for _, container := range apiServer.Spec.Containers {
           for _, arg := range container.Command {
               for _, setting := range requiredSettings {
                   if strings.Contains(arg, setting) {
                       foundSettings[setting] = true
                   }
               }
               if strings.Contains(arg, "enable-admission-plugins") && 
                  strings.Contains(arg, "EventRateLimit") {
                   foundSettings["EventRateLimit"] = true
               }
           }
       }

       for _, setting := range requiredSettings {
           if !foundSettings[setting] {
               t.Errorf("Required setting %s not found in API server configuration", setting)
           }
       }
       if !foundSettings["EventRateLimit"] {
           t.Error("EventRateLimit admission plugin not enabled")
       }
   })
}

func Test_scs_0215_minRequestTimeout(t *testing.T) {
    clientset, err := setupClientset()
    if err != nil {
        t.Fatalf("Failed to setup clientset: %v", err)
    }

    t.Run("Check_minRequestTimeout_Configuration", func(t *testing.T) {
        pods, err := clientset.CoreV1().Pods("kube-system").List(context.Background(), metav1.ListOptions{
            LabelSelector: "component=kube-apiserver",
        })
        if err != nil || len(pods.Items) == 0 {
            t.Fatalf("Failed to find kube-apiserver pod: %v", err)
        }

        found := false
        for _, container := range pods.Items[0].Spec.Containers {
            for _, arg := range container.Command {
                if strings.Contains(arg, "--min-request-timeout=") {
                    found = true
                    break
                }
            }
        }

        if !found {
            t.Error("min-request-timeout not configured for API server")
        }
    })
}

func Test_scs_0215_eventRateLimit(t *testing.T) {
   clientset, err := setupClientset()
   if err != nil {
       t.Fatalf("Failed to setup clientset: %v", err)
   }

   if isKindCluster(clientset) {
       t.Skip("Running on kind cluster - skipping EventRateLimit test")
   }

   t.Run("Check_EventRateLimit_Configuration", func(t *testing.T) {
       configLocations := []struct {
           name      string
           namespace string
           key       string
       }{
           {"admission-configuration", "kube-system", "eventratelimit.yaml"},
           {"kube-apiserver", "kube-system", "config.yaml"},
       }

       for _, loc := range configLocations {
           config, err := clientset.CoreV1().ConfigMaps(loc.namespace).Get(context.Background(), loc.name, metav1.GetOptions{})
           if err == nil {
               if data, ok := config.Data[loc.key]; ok {
                   if strings.Contains(data, "eventratelimit.admission.k8s.io") {
                       t.Logf("Found EventRateLimit configuration in %s/%s", loc.namespace, loc.name)
                       return
                   }
               }
           }
       }

       configMaps, _ := clientset.CoreV1().ConfigMaps("kube-system").List(context.Background(), metav1.ListOptions{})
       for _, cm := range configMaps.Items {
           if strings.Contains(cm.Name, "event-rate-limit") {
               t.Logf("Found standalone EventRateLimit configuration in ConfigMap: %s", cm.Name)
               return
           }
       }

       t.Error("No EventRateLimit configuration found in production cluster")
   })
}

func Test_scs_0215_apiPriorityAndFairness(t *testing.T) {
   clientset, err := setupClientset()
   if err != nil {
       t.Fatalf("Failed to setup clientset: %v", err)
   }

   if isKindCluster(clientset) {
       t.Skip("Running on kind cluster - skipping APF test")
   }

   t.Run("Check_APF_Configuration", func(t *testing.T) {
       pods, err := clientset.CoreV1().Pods("kube-system").List(context.Background(), metav1.ListOptions{
           LabelSelector: "component=kube-apiserver",
       })
       if err != nil || len(pods.Items) == 0 {
           t.Fatal("Failed to find kube-apiserver pod")
       }

       for _, container := range pods.Items[0].Spec.Containers {
           for _, arg := range container.Command {
               if strings.Contains(arg, "--enable-priority-and-fairness=true") {
                   t.Log("APF enabled via Command Line Flags")
                   return
               }
           }
       }

       t.Error("API Priority and Fairness not enabled")
   })
}

func Test_scs_0215_rateLimitValues(t *testing.T) {
   clientset, err := setupClientset()
   if err != nil {
       t.Fatalf("Failed to setup clientset: %v", err)
   }

   if isKindCluster(clientset) {
       t.Skip("Running on kind cluster - skipping rate limit values test")
   }

   t.Run("Check_Rate_Limit_Values", func(t *testing.T) {
       expectedValues := map[string]string{
           "qps":   "5000",
           "burst": "20000",
       }

       configMaps, _ := clientset.CoreV1().ConfigMaps("kube-system").List(context.Background(), metav1.ListOptions{})
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
                   return
               }
           }
       }

       t.Error("Recommended rate limit values (qps: 5000, burst: 20000) not found")
   })
}

func Test_scs_0215_etcdCompaction(t *testing.T) {
   clientset, err := setupClientset()
   if err != nil {
       t.Fatalf("Failed to setup clientset: %v", err)
   }

   if isKindCluster(clientset) {
       t.Skip("Running on kind cluster - skipping etcd compaction test")
   }

   t.Run("Check_Etcd_Compaction_Settings", func(t *testing.T) {
       pods, err := clientset.CoreV1().Pods("kube-system").List(context.Background(), metav1.ListOptions{
           LabelSelector: "component=etcd",
       })
       if err != nil || len(pods.Items) == 0 {
           t.Skip("No etcd pods found")
           return
       }

       requiredSettings := map[string]string{
           "auto-compaction-mode":      "periodic",
           "auto-compaction-retention": "8h",
       }

       for _, pod := range pods.Items {
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
                   t.Log("Found correct etcd compaction settings")
                   return
               }
           }
       }

       t.Error("Required etcd compaction settings not found")
   })
}

func Test_scs_0215_etcdBackup(t *testing.T) {
   clientset, err := setupClientset()
   if err != nil {
       t.Fatalf("Failed to setup clientset: %v", err)
   }

   if isKindCluster(clientset) {
       t.Skip("Running on kind cluster - skipping etcd backup test")
   }

   t.Run("Check_Etcd_Backup_Configuration", func(t *testing.T) {
       cronJobs, err := clientset.BatchV1().CronJobs("").List(context.Background(), metav1.ListOptions{})
       if err == nil {
           for _, job := range cronJobs.Items {
               if strings.Contains(strings.ToLower(job.Name), "etcd") &&
                  strings.Contains(strings.ToLower(job.Name), "backup") {
                   t.Log("Found etcd backup solution: CronJob")
                   return
               }
           }
       }
       t.Error("No etcd backup solution found")
   })
}

func Test_scs_0215_certificateRotation(t *testing.T) {
   clientset, err := setupClientset()
   if err != nil {
       t.Skip("Failed to setup clientset")
   }

   t.Run("Check_Certificate_Controller", func(t *testing.T) {
       _, err := clientset.AppsV1().Deployments("cert-manager").Get(context.Background(), "cert-manager", metav1.GetOptions{})
       if err != nil {
           t.Error("cert-manager not found - certificate controller required")
       } else {
           t.Log("Found active certificate controller: cert-manager")
       }
   })
}