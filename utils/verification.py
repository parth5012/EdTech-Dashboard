import requests
# """Fetch specific badge details"""
url = "https://api.credly.com/v1/badges/bc86b51a-6aff-4815-a864-2d40b63d3966"
# try:
#     response = requests.get(url)
#     response.raise_for_status()
#     print( response.json())
# except requests.exceptions.RequestException as e:
#     print({"error": str(e)})

def verify_public_badge(badge_url: str) -> bool:
    response = requests.get(badge_url)
    if response.status_code == 200 :
        return True, "Badge found and valid."
    else:
        return False, "Badge not found or inaccessible."

# public_url = "https://www.credly.com/badges/steKMkTDSVOoZ1RMhSIZwQ/public_url"
# valid, msg = verify_public_badge(public_url)
# print(msg)



def verify_unstop_certificate(cert_url:str) -> bool:
    try:
        response = requests.get(cert_url)
        if response.status_code == 200:
            return True, "Certificate is valid and active on Unstop."
        else:
            return False, "Certificate not found or invalid."
    except Exception as e:
        return False, f"Error occurred: {str(e)}"

# Example (replace with actual certificate URL from Unstop)
# certificate_url = "https://unstop.com/certificate-preview/4bb55d71-7dfc-4463-bec8-6dd7d8ef07e7"
# valid, message = verify_unstop_certificate(certificate_url)
# print(message)

def verify_certifier_certificate(cert_url: str)-> bool:
    try:
        response = requests.get(cert_url)
        if response.status_code == 200:
            return True, "Certificate is valid and verified."
        else:
            return False, "Certificate not found or invalid."
    except Exception as e:
        return False, f"Verification failed: {str(e)}"

# Sample certificate URL (replace with real one in production)
# sample_cert_url = "https://certifier.io/verify/8c2e8bcd-113e-41f5-9676-fe2acdc88714"
# valid, message = verify_certifier_certificate(sample_cert_url)
# print(message)

