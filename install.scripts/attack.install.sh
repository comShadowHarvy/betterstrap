#!/bin/bash

# Enhanced Ultimate Pentest Installer
# This script categorizes and installs penetration testing tools with an interactive menu

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to display a loading bar with percentage
loading_bar() {
    local current=$1
    local total=$2
    local percent=$((100 * current / total))
    local bar_length=40
    local filled_length=$((bar_length * current / total))
    local empty_length=$((bar_length - filled_length))

    printf -v bar "%0.s█" $(seq 1 $filled_length)
    printf -v space "%0.s░" $(seq 1 $empty_length)

    echo -ne "${BLUE}Progress: [${GREEN}${bar}${RED}${space}${BLUE}] ${YELLOW}${percent}%%${NC}\r"
}

# Function to check if a package is installed
is_package_installed() {
    pacman -Qs "$1" > /dev/null 2>&1
}

# Function to display the header
display_header() {
    clear
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo -e "${BOLD}${CYAN}            Ultimate Pentest Installer               ${NC}"
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo
}

# Function to display a description
display_description() {
    local title=$1
    local description=$2
    local advantages=$3
    local disadvantages=$4

    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo -e "${BOLD}${CYAN}   $title${NC}"
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo
    echo -e "${BOLD}Description:${NC}"
    echo -e "$description"
    echo
    echo -e "${BOLD}${GREEN}Advantages:${NC}"
    echo -e "$advantages"
    echo
    echo -e "${BOLD}${RED}Disadvantages:${NC}"
    echo -e "$disadvantages"
    echo
    echo -e "${BLUE}--------------------------------------------------${NC}"
    echo
}

# Function to install AUR helper if needed
ensure_aur_helper() {
    if command -v yay > /dev/null 2>&1; then
        return 0
    elif command -v paru > /dev/null 2>&1; then
        AUR_HELPER="paru"
        return 0
    else
        echo -e "${YELLOW}No AUR helper found. Installing yay...${NC}"
        
        # Check if git is installed
        if ! command -v git > /dev/null 2>&1; then
            echo -e "${YELLOW}Installing git...${NC}"
            sudo pacman -S --noconfirm git || {
                echo -e "${RED}Failed to install git. Exiting.${NC}"
                exit 1
            }
        fi
        
        # Create temp directory and install yay
        local temp_dir=$(mktemp -d)
        cd "$temp_dir" || exit 1
        git clone https://aur.archlinux.org/yay.git || {
            echo -e "${RED}Failed to clone yay repository. Exiting.${NC}"
            exit 1
        }
        cd yay || exit 1
        makepkg -si --noconfirm || {
            echo -e "${RED}Failed to build yay. Exiting.${NC}"
            exit 1
        }
        cd "$OLDPWD" || exit 1
        rm -rf "$temp_dir"
        
        echo -e "${GREEN}yay installed successfully.${NC}"
        AUR_HELPER="yay"
        return 0
    fi
}

# Function to install a tool
install_tool() {
    local name=$1
    local description=$2
    local advantages=$3
    local disadvantages=$4
    
    display_description "Installing $name" "$description" "$advantages" "$disadvantages"
    
    if is_package_installed "$name"; then
        echo -e "${GREEN}$name is already installed. Skipping installation.${NC}"
        sleep 1
        return 0
    else
        echo -e "${YELLOW}Installing $name...${NC}"
        if $AUR_HELPER -S --noconfirm "$name"; then
            echo -e "${GREEN}$name installed successfully.${NC}"
            sleep 1
            return 0
        else
            echo -e "${RED}Error installing $name. Skipping to the next tool.${NC}"
            sleep 2
            return 1
        fi
    fi
}

# Tool definitions by category
declare -A tool_categories

# Network Scanning & Enumeration
tool_categories["network"]=(
    "nmap:Network discovery and security auditing:- Comprehensive network scanning capabilities.\n- Extensive scripting engine for custom scans and vulnerability detection.:- Can be complex for beginners.\n- May produce false positives."
    "masscan:Fast TCP port scanner:- Extremely fast port scanning.:- Limited to port scanning only."
    "massdns:High-performance DNS resolver:- Fast DNS resolution for large wordlists.:- Requires DNS knowledge."
    "dnsvalidator:DNS validation tool:- Validates DNS configurations.:- Requires knowledge of DNS."
    "interlace:Parallel command execution tool:- Speeds up command execution for large lists.:- Requires understanding of parallel execution."
    "cloud_enum:Cloud asset enumeration tool:- Enumerates cloud assets for potential security issues.:- Limited to cloud-specific scenarios."
    "nmap-parse-output:Tool for parsing nmap XML output:- Simplifies nmap output parsing.:- Limited to nmap scans."
)

# Vulnerability Scanning
tool_categories["vuln_scan"]=(
    "nessus:Comprehensive vulnerability scanner:- Wide range of vulnerability checks.\n- Regular updates.:- Requires a subscription for advanced features."
    "openvas:Open-source vulnerability scanner:- Free and open-source.\n- Regularly updated vulnerability database.:- Can be resource-intensive."
    "nikto:Web server scanner:- Effective web server scanning.:- May produce false positives."
    "testssl:SSL/TLS scanner:- Comprehensive SSL/TLS analysis.:- Requires manual interpretation of results."
    "Nuclei templates:Vulnerability scanning templates for Nuclei:- Provides templates for Nuclei scans.:- Limited to the templates available."
    "wafw00f:Web application firewall detection tool:- Detects WAFs in web applications.:- Limited to known WAF signatures."
)

# Exploitation
tool_categories["exploit"]=(
    "metasploit:Exploit development and vulnerability research:- Extensive database of exploits.\n- Powerful automation capabilities.:- Can be complex for beginners."
    "beef:Browser-based exploitation:- Specialized in browser exploitation.:- Limited to browser-based attacks."
    "commix:Automated command injection and exploitation tool:- Automated command injection testing.:- Can be complex for beginners."
    "set:Framework for social engineering attacks:- Powerful social engineering tools.:- Requires knowledge of social engineering."
    "smuggler:Tool for HTTP request smuggling:- Effective for finding HTTP smuggling vulnerabilities.:- Requires knowledge of HTTP smuggling."
    "regulator:Tool for identifying and exploiting HTTP parameter pollution:- Detects and exploits parameter pollution.:- Limited to HTTP requests."
    "nomore403:Tool for bypassing 403 forbidden responses:- Attempts to bypass 403 restrictions.:- May not work on all sites."
    "spoofy:Spoofing tool:- Effective for various spoofing tasks.:- Requires knowledge of spoofing techniques."
)

# Web Application Testing
tool_categories["web"]=(
    "burpsuite:Web vulnerability scanner and testing platform:- Comprehensive web application testing.:- Requires a subscription for advanced features."
    "owasp-zap:Integrated web application security testing tool:- Free and open-source.\n- Wide range of testing tools.:- Can be slower than commercial tools."
    "fiddler:Web debugging proxy:- Effective for web debugging and traffic capture.:- Requires manual setup for HTTPS."
    "mitmproxy:Interactive man-in-the-middle proxy for HTTP and HTTPS:- Powerful and versatile proxy capabilities.:- Requires command-line knowledge."
    "sqlmap:Automatic SQL injection and database takeover tool:- Automated SQL injection testing.:- Can be complex for beginners."
    "ghauri:Advanced SQL injection tool:- Effective for finding and exploiting SQL injection.:- Requires SQL knowledge."
    "Corsy:CORS misconfiguration scanner:- Identifies misconfigurations in CORS.:- May produce false positives."
    "CMSeeK:CMS detection and exploitation suite:- Detects various CMS platforms and vulnerabilities.:- Limited by the CMS platforms supported."
    "swaggerspy:Swagger API enumeration tool:- Enumerates endpoints in Swagger APIs.:- Limited to Swagger API endpoints."
    "ffufPostprocessing:Post-processing for ffuf results:- Simplifies analysis of ffuf output.:- Limited to ffuf scans."
)

# Wireless Testing
tool_categories["wireless"]=(
    "aircrack-ng:Suite of tools for auditing wireless networks:- Comprehensive suite for wireless network security.:- Requires compatible hardware."
    "kismet:Wireless network detector and sniffer:- Effective for detecting and sniffing wireless networks.:- May require additional configuration."
)

# Password & Credential Testing
tool_categories["password"]=(
    "john:Password cracker:- Powerful and versatile password cracking capabilities.:- Can be resource-intensive."
    "hashcat:Advanced password recovery tool:- High performance with support for various algorithms.:- Requires a compatible GPU for best performance."
    "hydra:Network login cracker:- Fast and effective login cracking.:- Requires manual configuration."
    "pydictor:Python-based password generator and dictionary tool:- Customizable password generation.:- Requires Python knowledge."
    "LeakSearch:Tool for searching leaked credentials:- Automates the search for leaked credentials.:- Requires access to leaked databases."
)

# Forensics & Analysis
tool_categories["forensics"]=(
    "autopsy:Digital forensics platform:- Comprehensive digital forensics tools.:- Requires knowledge of digital forensics."
    "volatility:Advanced memory forensics framework:- Powerful memory analysis capabilities.:- Requires knowledge of memory forensics."
    "wireshark:Network protocol analyzer:- Comprehensive network analysis.:- Can be complex for beginners."
    "gitleaks:Tool for finding secrets in git repositories:- Detects secrets in git repositories.:- Limited to git repositories."
    "trufflehog:Tool for finding secrets in git history:- Effective for finding sensitive data in git history.:- Requires access to git history."
)

# Mobile & IoT
tool_categories["mobile"]=(
    "mobsf:Automated security analysis framework for mobile applications:- Comprehensive mobile app security analysis.:- Requires mobile app knowledge."
    "firmware-analysis-toolkit:Toolkit for analyzing and emulating firmware:- Effective firmware analysis tools.:- Requires knowledge of firmware analysis."
)

# Container & Cloud Security
tool_categories["container"]=(
    "aquasec:Container security platform:- Effective container security tools.:- Requires knowledge of container security."
    "kube-bench:Kubernetes security benchmark:- Automated Kubernetes security checks.:- Requires Kubernetes knowledge."
    "misconfig-mapper:Tool for mapping misconfigurations:- Identifies misconfigurations in systems.:- Requires manual analysis."
)

# OSINT & Reconnaissance
tool_categories["osint"]=(
    "dorks_hunter:Search engine dorking tool:- Automates the process of finding vulnerable sites via search engines.:- Limited to the dorks available."
    "fav-up:Tool for exploiting favicon.ico:- Useful for identifying web technologies via favicon.ico.:- Limited by the database of favicons."
    "waymore:Automated wayback machine URL extraction:- Extracts URLs from wayback machine.:- Limited to archived content."
    "emailfinder:Tool for finding email addresses:- Extracts emails from various sources.:- Limited to the sources provided."
    "xnLinkFinder:Tool for finding links in JavaScript files:- Automates link extraction from JS files.:- May produce false positives."
    "getjswords:Tool for extracting JavaScript words:- Useful for finding hidden JavaScript functions.:- Limited to words in JS files."
    "JSA:JavaScript analysis tool:- Analyzes JavaScript files for security issues.:- Requires manual analysis."
    "urless:URL extraction tool:- Extracts URLs from various sources.:- Limited to the sources provided."
)

# Wordlists & Resources
tool_categories["wordlists"]=(
    "OneListForAll:One list for all wordlists:- Consolidated wordlists for various purposes.:- May require filtering for specific use cases."
    "lfi_wordlist:Wordlist for Local File Inclusion attacks:- Specialized wordlist for LFI attacks.:- Limited to LFI-specific scenarios."
    "ssti_wordlist:Wordlist for Server-Side Template Injection:- Specialized wordlist for SSTI attacks.:- Limited to SSTI-specific scenarios."
    "subs_wordlist:Wordlist for subdomain enumeration:- Effective for finding subdomains.:- May require filtering for specific domains."
    "subs_wordlist_big:Larger wordlist for subdomain enumeration:- Comprehensive subdomain enumeration.:- Increased scan time."
    "resolvers:List of DNS resolvers:- Useful for DNS resolution tasks.:- May include untrusted resolvers."
    "resolvers_trusted:List of trusted DNS resolvers:- Trusted DNS resolution.:- Limited number of resolvers."
    "Fuzzing templates:Fuzzing templates for various tools:- Consolidated fuzzing templates.:- Requires filtering for specific use cases."
    "ripgen:Tool for generating wordlists based on target information:- Custom wordlist generation.:- Requires target-specific information."
)

# Miscellaneous
tool_categories["misc"]=(
    "porch-pirate:Tool for automating package capture:- Automates the process of capturing packages.:- Limited to scenarios where packages are captured."
)

# Function to display category menu
display_category_menu() {
    display_header
    echo -e "${BOLD}${CYAN}Tool Categories:${NC}"
    echo
    
    local i=1
    for category in "${!tool_categories[@]}"; do
        local count=${#tool_categories[$category][@]}
        local desc=""
        
        case $category in
            network) desc="Network Scanning & Enumeration Tools" ;;
            vuln_scan) desc="Vulnerability Scanning Tools" ;;
            exploit) desc="Exploitation Frameworks & Tools" ;;
            web) desc="Web Application Testing Tools" ;;
            wireless) desc="Wireless Testing Tools" ;;
            password) desc="Password & Credential Testing Tools" ;;
            forensics) desc="Forensics & Analysis Tools" ;;
            mobile) desc="Mobile & IoT Security Tools" ;;
            container) desc="Container & Cloud Security Tools" ;;
            osint) desc="OSINT & Reconnaissance Tools" ;;
            wordlists) desc="Wordlists & Resources" ;;
            misc) desc="Miscellaneous Tools" ;;
        esac
        
        echo -e "${MAGENTA}$i)${NC} ${BOLD}$desc${NC} (${YELLOW}$count tools${NC})"
        categories_array[$i]=$category
        ((i++))
    done
    
    echo -e "${MAGENTA}a)${NC} ${BOLD}Install all tools${NC}"
    echo -e "${MAGENTA}q)${NC} ${BOLD}Quit${NC}"
    echo
}

# Function to install tools from a specific category
install_category() {
    local category=$1
    local tools=("${tool_categories[$category][@]}")
    local total_steps=${#tools[@]}
    local current_step=0
    
    display_header
    echo -e "${BOLD}${CYAN}Installing ${category} tools...${NC}"
    echo
    
    for tool in "${tools[@]}"; do
        IFS=':' read -r name description advantages disadvantages <<< "$tool"
        
        clear
        install_tool "$name" "$description" "$advantages" "$disadvantages"
        
        loading_bar $((++current_step)) $total_steps
    done
    
    echo -e "\n${GREEN}All tools in ${category} category installed.${NC}"
    sleep 2
}

# Function to install all tools
install_all_tools() {
    local all_tools=()
    
    # Combine all categories
    for category in "${!tool_categories[@]}"; do
        all_tools+=("${tool_categories[$category][@]}")
    done
    
    local total_steps=${#all_tools[@]}
    local current_step=0
    
    display_header
    echo -e "${BOLD}${CYAN}Installing all tools...${NC}"
    echo
    
    for tool in "${all_tools[@]}"; do
        IFS=':' read -r name description advantages disadvantages <<< "$tool"
        
        clear
        install_tool "$name" "$description" "$advantages" "$disadvantages"
        
        loading_bar $((++current_step)) $total_steps
    done
    
    echo -e "\n${GREEN}All tools installed.${NC}"
    sleep 2
}

# Main function
main() {
    # Check if running as root
    if [ "$(id -u)" -eq 0 ]; then
        echo -e "${RED}Error: This script should not be run as root.${NC}"
        exit 1
    fi
    
    # Initialize variables
    declare -A categories_array
    AUR_HELPER="yay"
    
    # Ensure an AUR helper is installed
    ensure_aur_helper
    
    # Main loop
    while true; do
        display_category_menu
        echo -n -e "${CYAN}Select a category to install (or 'q' to quit): ${NC}"
        read -r choice
        
        case $choice in
            [0-9]*)
                if [ -n "${categories_array[$choice]}" ]; then
                    install_category "${categories_array[$choice]}"
                else
                    echo -e "${RED}Invalid choice. Please try again.${NC}"
                    sleep 1
                fi
                ;;
            "a"|"A")
                install_all_tools
                ;;
            "q"|"Q")
                echo -e "${GREEN}Exiting. Thank you for using the Ultimate Pentest Installer!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice. Please try again.${NC}"
                sleep 1
                ;;
        esac
    done
}

# Run the main function
main