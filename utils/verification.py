import requests


def verify_public_badge(badge_url: str) -> bool:
    try:
        response = requests.get(badge_url, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Badge verification error: {e}")
        return False

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

