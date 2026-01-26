#!/bin/bash

# Create a modified version of setup-tdarr.sh that uses a variable for os-release
# AND disables the main execution at the end
sed 's|/etc/os-release|"$TEST_OS_RELEASE"|g' /home/mw/git/betterstrap/tdarr/setup-tdarr.sh > /tmp/setup-tdarr-test.sh

# Comment out the main execution line
sed -i 's/^main "$@"/# main "$@"/g' /tmp/setup-tdarr-test.sh

# Mock functions to avoid side effects
log() { echo "LOG: $*"; }
print_section() { echo "SECTION: $*"; }
command_exists() { return 1; } # Fail extra checks
error_handler() { echo "Error at $1"; }

# Source the modified script functions (we only need detect_distribution)
clean_up() {
    rm -f /tmp/os-release-mock /tmp/setup-tdarr-test.sh
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
