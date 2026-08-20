import httpx

from app.core.config import Settings
from app.services.citizen_data.base import CitizenDataProvider, DerivedCitizenAttributes


class DigiLockerProvider(CitizenDataProvider):
    """Implements DigiLocker's documented OAuth2 authorization-code flow
    (https://apisetu.gov.in / DigiLocker Partner API: /public/oauth2/1/authorize,
    /public/oauth2/1/token). Only constructed when DIGILOCKER_ENABLED=true
    and client credentials are configured — disabled by default per the
    master spec. Not live-verified in this sandbox (no test DigiLocker
    client credentials or network access to api.digitallocker.gov.in are
    available here); the flow is implemented against the real documented
    endpoints, never invented."""

    def __init__(self, settings: Settings):
        if not settings.DIGILOCKER_ENABLED:
            raise RuntimeError("DigiLocker integration is disabled (DIGILOCKER_ENABLED=false)")
        if not settings.DIGILOCKER_CLIENT_ID or not settings.DIGILOCKER_REDIRECT_URI:
            raise RuntimeError("DIGILOCKER_CLIENT_ID and DIGILOCKER_REDIRECT_URI must be configured")
        self._settings = settings

    async def get_authorization_url(self, state: str) -> str:
        s = self._settings
        return (
            f"{s.DIGILOCKER_BASE_URL}/public/oauth2/1/authorize"
            f"?response_type=code&client_id={s.DIGILOCKER_CLIENT_ID}"
            f"&redirect_uri={s.DIGILOCKER_REDIRECT_URI}&state={state}"
        )

    async def exchange_code_for_profile(self, code: str) -> DerivedCitizenAttributes:
        s = self._settings
        async with httpx.AsyncClient(timeout=s.LLM_REQUEST_TIMEOUT_SECONDS) as client:
            token_resp = await client.post(
                f"{s.DIGILOCKER_BASE_URL}/public/oauth2/1/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": s.DIGILOCKER_CLIENT_ID,
                    "client_secret": s.DIGILOCKER_CLIENT_SECRET,
                    "redirect_uri": s.DIGILOCKER_REDIRECT_URI,
                },
            )
            token_resp.raise_for_status()
            access_token = token_resp.json()["access_token"]

            profile_resp = await client.get(
                f"{s.DIGILOCKER_BASE_URL}/public/oauth2/1/user",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_resp.raise_for_status()
            raw = profile_resp.json()

        # Only derived, non-identity attributes are retained — never the
        # raw DigiLocker identity payload (Aadhaar, DOB document, etc.).
        return DerivedCitizenAttributes(
            age_range=_bucket_age(raw.get("dob")),
            state=raw.get("state"),
            extra={},
        )


def _bucket_age(dob: str | None) -> str | None:
    if not dob:
        return None
    from datetime import date

    try:
        year = int(dob.split("-")[0])
    except (ValueError, IndexError):
        return None
    age = date.today().year - year
    if age < 18:
        return "under_18"
    if age < 40:
        return "18_39"
    if age < 60:
        return "40_59"
    return "60_plus"
