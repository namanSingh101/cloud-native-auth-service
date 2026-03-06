from fastapi import Request

def get_ip_address(request:Request) -> str:

    if request.client:
        return request.client.host
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return "unknown"