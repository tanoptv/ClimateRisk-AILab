from app_config import Settings
from db import database
from main import create_app
from tests.helpers import temp_db_path


def test_dashboard_home_and_test_subscription():
    db_path = temp_db_path()
    settings = Settings("", "", "", "", 8000, f"sqlite:///{db_path}", "dashboard")
    app = create_app(settings)
    client = app.test_client()

    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Climate Risk Dashboard" in response.data

    response = client.post(
        "/dashboard/users",
        data={"user_id": "dashboard-user", "provinces": "เชียงใหม่ กรุงเทพมหานคร"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert database.get_user_provinces("dashboard-user", db_path) == ["เชียงใหม่", "กรุงเทพมหานคร"]

