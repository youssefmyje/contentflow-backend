import secrets


oauth_states: set[str] = set()


def create_oauth_state() -> str:
    state = secrets.token_urlsafe(32)
    oauth_states.add(state)
    return state


def consume_oauth_state(state: str) -> bool:
    if state not in oauth_states:
        return False

    oauth_states.remove(state)
    return True