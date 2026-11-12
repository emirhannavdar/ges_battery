from pydantic import BaseModel


class EpiasTGTToken(BaseModel):
    username: str = ""
    password: str = ""



def get_tgt_headers():
    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"
    }

def get_tgt_body(username: str, password: str):
    return {
        "username": username,
        "password": password
    }

def get_epias_headers(token: str):
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "TGT": token
    }

def get_ptf_body(startDate: str, endDate: str):
    return {
        "startDate": startDate,
        "endDate": endDate
    }

def get_kptf_body(startDate: str):
    return {
        "startDate": startDate
    }
