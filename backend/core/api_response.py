def success(data=None):
    return {
        "success": True,
        "data": data,
    }


def error(code, message):
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
