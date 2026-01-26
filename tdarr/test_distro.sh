#!/bin/bash

# Create a modified version of setup-tdarr.sh:
# 1. Use variable for os-release
sed 's|/etc/os-release|"$TEST_OS_RELEASE"|g' /home/mw/git/betterstrap/tdarr/setup-tdarr.sh > /tmp/setup-tdarr-test.sh

# 2. Disable main execution
sed -i 's/^main "$@"/# main "$@"/g' /tmp/setup-tdarr-test.sh

# 3. Change log file path to tmp
sed -i 's|readonly LOG_FILE=.*|readonly LOG_FILE="/tmp/setup-tdarr-test.log"|g' /tmp/setup-tdarr-test.sh

# Mock functions to avoid side effects
# We need to define them AFTER sourcing if we want to override, but readonly vars need to be changed in source.
# The log function is defined in the script, so if we want to override it, we must do it AFTER sourcing.
# But since we fixed LOG_FILE, the original log function should work.

clean_up() {
    rm -f /tmp/os-release-mock /tmp/setup-tdarr-test.sh /tmp/setup-tdarr-test.log
}
trap clean_up EXIT

run_test() {
    local test_id="$1"
    local expected_distro="arch"
    local expected_pkg="pacman"
    
    echo "Testing ID=$test_id..."
    
    # Create mock os-release
    echo "ID=$test_id" > /tmp/os-release-mock
    export TEST_OS_RELEASE="/tmp/os-release-mock"
    
    # Run detection
    (
        source /tmp/setup-tdarr-test.sh
        
        # Override error handler to not exit the subshell immediately on simple failures if we want to handle them
        # But for this test, we expect success.
        
        detect_distribution
        
        if [ "$DISTRO" == "$expected_distro" ] && [ "$PKG_MANAGER" == "$expected_pkg" ]; then
            echo "PASS: $test_id detected as $DISTRO with $PKG_MANAGER"
            exit 0
        else
            echo "FAIL: $test_id detected as $DISTRO with $PKG_MANAGER (Expected $expected_distro)"
            exit 1
        fi
    )
    
    if [ $? -ne 0 ]; then
        echo "Test failed for $test_id"
        exit 1
    fi
}

run_test "cachyos"
run_test "endeavouros"
run_test "garuda"
run_test "arch"

echo "All tests passed!"
