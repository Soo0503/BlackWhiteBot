import requests


API_URL = "https://lounge.mkcentral.com/api/player"


def get_lounge_name(player_id):
    """
    MKCentral Lounge APIからLounge Nameを取得する
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64)"
        )
    }

    params = {
        "id": player_id,
        "season": 16
    }

    try:
        response = requests.get(
            API_URL,
            headers=headers,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        lounge_name = data.get("name")

        if not lounge_name:
            return None

        return lounge_name

    except Exception as e:
        print(
            f"[Lounge API ERROR] "
            f"Player ID {player_id}: {e}"
        )
        return None