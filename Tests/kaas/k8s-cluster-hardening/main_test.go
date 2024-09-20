package scs_k8s_tests

import (
	"context"
	"fmt"
	"os"
	"testing"

	plugin_helper "github.com/vmware-tanzu/sonobuoy-plugins/plugin-helper"
	v1 "k8s.io/api/core/v1"
	"sigs.k8s.io/e2e-framework/pkg/env"
	"sigs.k8s.io/e2e-framework/pkg/envconf"
)


const (
	ProgressReporterCtxKey = "SONOBUOY_PROGRESS_REPORTER"
	NamespacePrefixKey = "NS_PREFIX"
)

var testenv env.Environment

func TestMain(m *testing.M) {
	// Assume we are running in the cluster as a Sonobuoy plugin.
	testenv = env.NewInClusterConfig()

	// Specifying a run ID so that multiple runs wouldn't collide. Allow a prefix to be set via env var
	// so that a plugin configuration (yaml file) can easily set that without code changes.
	nsPrefix := os.Getenv(NamespacePrefixKey)
	runID := envconf.RandomName(nsPrefix, 4)

	// Create updateReporter; will also place into context during Setup for use in features.
	updateReporter := plugin_helper.NewProgressReporter(0)

	testenv.Setup(func(ctx context.Context, config *envconf.Config) (context.Context, error) {
		// Try and create the client; doing it before all the tests allows the tests to assume
		// it can be created without error and they can just use config.Client().
		_,err:=config.NewClient()
		return context.WithValue(ctx,ProgressReporterCtxKey,updateReporter) ,err
	})

	testenv.BeforeEachTest(func(ctx context.Context, cfg *envconf.Config, t *testing.T) (context.Context, error) {
	fmt.Println("BeforeEachTest")
		updateReporter.StartTest(t.Name())
		return createNSForTest(ctx, cfg, t, runID)
	})

	testenv.AfterEachTest(func(ctx context.Context, cfg *envconf.Config, t *testing.T) (context.Context, error) {
	fmt.Println("AfterEachTest")
		updateReporter.StopTest(t.Name(),t.Failed(),t.Skipped(),nil)
		return deleteNSForTest(ctx, cfg, t, runID)
	})

	/*
	testenv.BeforeEachFeature(func(ctx context.Context, config *envconf.Config, info features.Feature) (context.Context, error) {
		// Note that you can also add logic here for before a feature is tested. There may be
		// more than one feature in a test.
		fmt.Println("BeforeEachFeature")
		return ctx, nil
	})

	testenv.AfterEachFeature(func(ctx context.Context, config *envconf.Config, info features.Feature) (context.Context, error) {
		// Note that you can also add logic here for after a feature is tested. There may be
		// more than one feature in a test.
		fmt.Println("AfterEachFeature")
		return ctx, nil
	})
	*/

	testenv.Finish(
		// Teardown func: delete kind cluster
		func(ctx context.Context, cfg *envconf.Config) (context.Context, error) {
			fmt.Println("Finished go test suite")
			//~ if err := ???; err != nil{
				//~ return ctx, err
			//~ }
			return ctx, nil
		},
	)

	os.Exit(testenv.Run(m))
}

// CreateNSForTest creates a random namespace with the runID as a prefix. It is stored in the context
// so that the deleteNSForTest routine can look it up and delete it.
func createNSForTest(ctx context.Context, cfg *envconf.Config, t *testing.T, runID string) (context.Context, error) {
	ns := envconf.RandomName(runID, 10)
	ctx = context.WithValue(ctx, nsKey(t), ns)

	t.Logf("Creating namespace %v for test %v", ns, t.Name())
	nsObj := v1.Namespace{}
	nsObj.Name = ns
	return ctx, cfg.Client().Resources().Create(ctx, &nsObj)
}

// DeleteNSForTest looks up the namespace corresponding to the given test and deletes it.
func deleteNSForTest(ctx context.Context, cfg *envconf.Config, t *testing.T, runID string) (context.Context, error) {
	ns := fmt.Sprint(ctx.Value(nsKey(t)))
	t.Logf("Deleting namespace %v for test %v", ns, t.Name())

	nsObj := v1.Namespace{}
	nsObj.Name = ns
	return ctx, cfg.Client().Resources().Delete(ctx, &nsObj)
}

func nsKey(t *testing.T) string {
	return "NS-for-%v" + t.Name()
}
