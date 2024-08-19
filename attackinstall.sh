#!/bin/bash

# Function to display a loading bar with percentage
loading_bar() {
    local current=$1
    local total=$2
    local percent=$(( 100 * current / total ))
    local bar_length=20
    local filled_length=$(( bar_length * current / total ))
    local empty_length=$(( bar_length - filled_length ))

    printf -v bar "%0.s#" $(seq 1 $filled_length)
    printf -v space "%0.s " $(seq 1 $empty_length)

    echo -ne "Progress: [${bar}${space}] (${percent}%%)\r"
}

# Function to check if a package is installed
is_package_installed() {
    pacman -Qs $1 > /dev/null
}

# Function to display the header
display_header() {
    clear
    echo "============================="
    echo "   Ultimate Pentest Installer"
    echo "============================="
    echo
}

# Function to display a description
display_description() {
    local title=$1
    local description=$2
    local advantages=$3
    local disadvantages=$4

    tput cup 4 0
    echo "============================="
    echo "   $title"
    echo "============================="
    echo
    echo "Description:"
    echo "$description"
    echo
    echo "Advantages:"
    echo -e "$advantages"
    echo
    echo "Disadvantages:"
    echo -e "$disadvantages"
    echo
    echo "----------------------------------"
    echo
}

total_steps=61  # Updated total number of steps
current_step=0

display_header

# List of tools to install
tools=(
    "nmap:Network discovery and security auditing:- Comprehensive network scanning capabilities.\n- Extensive scripting engine for custom scans and vulnerability detection.:- Can be complex for beginners.\n- May produce false positives."
    "masscan:Fast TCP port scanner:- Extremely fast port scanning.:- Limited to port scanning only."
    "nessus:Comprehensive vulnerability scanner:- Wide range of vulnerability checks.\n- Regular updates.:- Requires a subscription for advanced features."
    "openvas:Open-source vulnerability scanner:- Free and open-source.\n- Regularly updated vulnerability database.:- Can be resource-intensive."
    "metasploit:Exploit development and vulnerability research:- Extensive database of exploits.\n- Powerful automation capabilities.:- Can be complex for beginners."
    "beef:Browser-based exploitation:- Specialized in browser exploitation.:- Limited to browser-based attacks."
    "aircrack-ng:Suite of tools for auditing wireless networks:- Comprehensive suite for wireless network security.:- Requires compatible hardware."
    "kismet:Wireless network detector and sniffer:- Effective for detecting and sniffing wireless networks.:- May require additional configuration."
    "john:Password cracker:- Powerful and versatile password cracking capabilities.:- Can be resource-intensive."
    "hashcat:Advanced password recovery tool:- High performance with support for various algorithms.:- Requires a compatible GPU for best performance."
    "burpsuite:Web vulnerability scanner and testing platform:- Comprehensive web application testing.:- Requires a subscription for advanced features."
    "owasp-zap:Integrated web application security testing tool:- Free and open-source.\n- Wide range of testing tools.:- Can be slower than commercial tools."
    "fiddler:Web debugging proxy:- Effective for web debugging and traffic capture.:- Requires manual setup for HTTPS."
    "mitmproxy:Interactive man-in-the-middle proxy for HTTP and HTTPS:- Powerful and versatile proxy capabilities.:- Requires command-line knowledge."
    "autopsy:Digital forensics platform:- Comprehensive digital forensics tools.:- Requires knowledge of digital forensics."
    "volatility:Advanced memory forensics framework:- Powerful memory analysis capabilities.:- Requires knowledge of memory forensics."
    "sqlmap:Automatic SQL injection and database takeover tool:- Automated SQL injection testing.:- Can be complex for beginners."
    "nikto:Web server scanner:- Effective web server scanning.:- May produce false positives."
    "hydra:Network login cracker:- Fast and effective login cracking.:- Requires manual configuration."
    "wireshark:Network protocol analyzer:- Comprehensive network analysis.:- Can be complex for beginners."
    "aquasec:Container security platform:- Effective container security tools.:- Requires knowledge of container security."
    "kube-bench:Kubernetes security benchmark:- Automated Kubernetes security checks.:- Requires Kubernetes knowledge."
    "set:Framework for social engineering attacks:- Powerful social engineering tools.:- Requires knowledge of social engineering."
    "mobsf:Automated security analysis framework for mobile applications:- Comprehensive mobile app security analysis.:- Requires mobile app knowledge."
    "firmware-analysis-toolkit:Toolkit for analyzing and emulating firmware:- Effective firmware analysis tools.:- Requires knowledge of firmware analysis."
    "dorks_hunter:Search engine dorking tool:- Automates the process of finding vulnerable sites via search engines.:- Limited to the dorks available."
    "fav-up:Tool for exploiting favicon.ico:- Useful for identifying web technologies via favicon.ico.:- Limited by the database of favicons."
    "Corsy:CORS misconfiguration scanner:- Identifies misconfigurations in CORS.:- May produce false positives."
    "testssl:SSL/TLS scanner:- Comprehensive SSL/TLS analysis.:- Requires manual interpretation of results."
    "CMSeeK:CMS detection and exploitation suite:- Detects various CMS platforms and vulnerabilities.:- Limited by the CMS platforms supported."
    "OneListForAll:One list for all wordlists:- Consolidated wordlists for various purposes.:- May require filtering for specific use cases."
    "lfi_wordlist:Wordlist for Local File Inclusion attacks:- Specialized wordlist for LFI attacks.:- Limited to LFI-specific scenarios."
    "ssti_wordlist:Wordlist for Server-Side Template Injection:- Specialized wordlist for SSTI attacks.:- Limited to SSTI-specific scenarios."
    "subs_wordlist:Wordlist for subdomain enumeration:- Effective for finding subdomains.:- May require filtering for specific domains."
    "subs_wordlist_big:Larger wordlist for subdomain enumeration:- Comprehensive subdomain enumeration.:- Increased scan time."
    "resolvers:List of DNS resolvers:- Useful for DNS resolution tasks.:- May include untrusted resolvers."
    "resolvers_trusted:List of trusted DNS resolvers:- Trusted DNS resolution.:- Limited number of resolvers."
    "xnLinkFinder:Tool for finding links in JavaScript files:- Automates link extraction from JS files.:- May produce false positives."
    "waymore:Automated wayback machine URL extraction:- Extracts URLs from wayback machine.:- Limited to archived content."
    "commix:Automated command injection and exploitation tool:- Automated command injection testing.:- Can be complex for beginners."
    "getjswords:Tool for extracting JavaScript words:- Useful for finding hidden JavaScript functions.:- Limited to words in JS files."
    "JSA:JavaScript analysis tool:- Analyzes JavaScript files for security issues.:- Requires manual analysis."
    "cloud_enum:Cloud asset enumeration tool:- Enumerates cloud assets for potential security issues.:- Limited to cloud-specific scenarios."
    "nmap-parse-output:Tool for parsing nmap XML output:- Simplifies nmap output parsing.:- Limited to nmap scans."
    "pydictor:Python-based password generator and dictionary tool:- Customizable password generation.:- Requires Python knowledge."
    "urless:URL extraction tool:- Extracts URLs from various sources.:- Limited to the sources provided."
    "smuggler:Tool for HTTP request smuggling:- Effective for finding HTTP smuggling vulnerabilities.:- Requires knowledge of HTTP smuggling."
    "regulator:Tool for identifying and exploiting HTTP parameter pollution:- Detects and exploits parameter pollution.:- Limited to HTTP requests."
    "nomore403:Tool for bypassing 403 forbidden responses:- Attempts to bypass 403 restrictions.:- May not work on all sites."
    "ffufPostprocessing:Post-processing for ffuf results:- Simplifies analysis of ffuf output.:- Limited to ffuf scans."
    "misconfig-mapper:Tool for mapping misconfigurations:- Identifies misconfigurations in systems.:- Requires manual analysis."
    "spoofy:Spoofing tool:- Effective for various spoofing tasks.:- Requires knowledge of spoofing techniques."
    "swaggerspy:Swagger API enumeration tool:- Enumerates endpoints in Swagger APIs.:- Limited to Swagger API endpoints."
    "LeakSearch:Tool for searching leaked credentials:- Automates the search for leaked credentials.:- Requires access to leaked databases."
    "wafw00f:Web application firewall detection tool:- Detects WAFs in web applications.:- Limited to known WAF signatures."
    "dnsvalidator:DNS validation tool:- Validates DNS configurations.:- Requires knowledge of DNS."
    "Nuclei templates:Vulnerability scanning templates for Nuclei:- Provides templates for Nuclei scans.:- Limited to the templates available."
    "Fuzzing templates:Fuzzing templates for various tools:- Consolidated fuzzing templates.:- Requires filtering for specific use cases."
    "Massdns:High-performance DNS resolver:- Fast DNS resolution for large wordlists.:- Requires DNS knowledge."
    "interlace:Parallel command execution tool:- Speeds up command execution for large lists.:- Requires understanding of parallel execution."
    "emailfinder:Tool for finding email addresses:- Extracts emails from various sources.:- Limited to the sources provided."
    "ripgen:Tool for generating wordlists based on target information:- Custom wordlist generation.:- Requires target-specific information."
    "ghauri:Advanced SQL injection tool:- Effective for finding and exploiting SQL injection.:- Requires SQL knowledge."
    "gitleaks:Tool for finding secrets in git repositories:- Detects secrets in git repositories.:- Limited to git repositories."
    "trufflehog:Tool for finding secrets in git history:- Effective for finding sensitive data in git history.:- Requires access to git history."
    "porch-pirate:Tool for automating package capture:- Automates the process of capturing packages.:- Limited to scenarios where packages are captured."
)

# Function to install a tool
install_tool() {
    local tool=$1
    local name=$(echo $tool | cut -d: -f1)
    local description=$(echo $tool | cut -d: -f2)
    local advantages=$(echo $tool | cut -d: -f3)
    local disadvantages=$(echo $tool | cut -d: -f4)

    clear
    display_description "Installing $name" "$description" "$advantages" "$disadvantages"
    sleep 7
    if is_package_installed "$name"; then
        echo "$name is already installed."
    else
        yay -S --noconfirm $name
        echo -ne "\n$name installed.\n"
    fi
    loading_bar $((++current_step)) $total_steps
}

# Install each tool
for tool in "${tools[@]}"; do
    install_tool "$tool"
done

loading_bar $total_steps $total_steps
echo -ne '\nAll tools installed.\n'
