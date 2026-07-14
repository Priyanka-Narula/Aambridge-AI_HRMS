from app.core.security import ROLE_OWNER, ROLE_RECRUITER, normalize_role


def test_owner_and_recruiter_roles_normalized() -> None:
    assert normalize_role("owner") == ROLE_OWNER
    assert normalize_role("recruiter") == ROLE_RECRUITER
    assert normalize_role("admin") == ROLE_OWNER
