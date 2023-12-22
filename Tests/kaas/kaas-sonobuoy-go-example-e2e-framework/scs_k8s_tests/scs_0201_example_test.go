package scs_k8s_tests

import (
	"context"
	"testing"
	"time"
	"fmt" 
	plugin_helper "github.com/vmware-tanzu/sonobuoy-plugins/plugin-helper"
	corev1 "k8s.io/api/core/v1"
	"sigs.k8s.io/e2e-framework/pkg/envconf"
	"sigs.k8s.io/e2e-framework/pkg/features"
)


func Test_scs_0200_sonobuoy_pass(t *testing.T) {
  fmt.Println("Test a passing test")
  testvar := 5
  if testvar != 5 {

    t.Errorf("testvar = %d; want 5", testvar)

  }
}

func Test_scs_0200_sonobuoy_fail(t *testing.T) {
  fmt.Println("Test a failing test")
  testvar := 5
  if testvar != 3 {

    t.Errorf("testvar = %d; want 3", testvar)

  }
}


func scs_0200_sonobuoy_TestListPods(t *testing.T) {
	f := features.New("pod list").
    WithLabel("type", "pod-count").
		Assess("pods from kube-system", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			var pods corev1.PodList
			err := cfg.Client().Resources("kube-system").List(context.TODO(), &pods)
			if err != nil {
				t.Fatal(err)
			}
			t.Logf("found %d pods", len(pods.Items))
			if len(pods.Items) == 0 {
				t.Fatal("no pods in namespace kube-system")
			}
			return ctx
		})

	testenv.Test(t, f.Feature())
}

func scs_0200_sonobuoy_TestListPods_Long(t *testing.T) {
	f := features.New("pod list").
    WithLabel("type", "progress").
		Assess("pods from kube-system", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			var pods corev1.PodList
			err := cfg.Client().Resources("kube-system").List(context.TODO(), &pods)
			if err != nil {
				t.Fatal(err)
			}
			progressReporterVal := ctx.Value(ProgressReporterCtxKey)
			progressReporter:=progressReporterVal.(plugin_helper.ProgressReporter)
			for i:=0;i<5;i++{
				time.Sleep(5*time.Second)
				progressReporter.SendMessageAsync("Waiting for a long test...")
			}
			return ctx
		})

	testenv.Test(t, f.Feature())
}
