package scs_k8s_tests

import (
	"os"
	"testing"
)

func Test_scs_0200_smoke(t *testing.T) {
	// This test ensures that no DevelopmentMode was set
	// when using this test-suite productively
	developmentMode := os.Getenv(DevelopmentModeKey)
	if developmentMode != "" {
		t.Errorf("developmentMode is set to = %v; want None", developmentMode)
	}
}
